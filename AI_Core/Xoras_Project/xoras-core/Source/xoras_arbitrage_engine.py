import asyncio
import aiohttp
import json
import time
import os
import struct
import subprocess
import sys
from multiprocessing import shared_memory

# Apex Architecture Memory Layout (Aligns with xoras_apex_shm.hpp)
# OrderBookTick size = 192 bytes: 16s dddddddd dddddddd Q B 39x
TICK_FORMAT = "16s dddddddd dddddddd Q B 39x"
TICK_SIZE = 192

# MarketDecision size = 64 bytes: 16s d d Q B B 22x
DECISION_FORMAT = "16s d d Q B B 22x"
DECISION_SIZE = 64

INPUT_CAPACITY = 1024
OUTPUT_CAPACITY = 1024
SHM_NAME = "xoras_apex_shm"  # no leading slash in python 3.14


class LiveExecutionModule:
    """Handles the actual live order firing to Binance API."""

    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY", "")
        self.base_url = "https://api.binance.us"

    async def execute_trade(self, symbol, side, price, quantity):
        if not self.api_key:
            return {"status": "SIMULATED", "action": side, "symbol": symbol, "price": price}

        print(f"[EXECUTION-CORE] FIRE {side} {symbol} @ {price} | VOL: {quantity}")
        return {"status": "MOCKED_EXECUTION_SUCCESS"}


class ArbitrageEngine:
    def __init__(self, brain):
        self.brain = brain
        self.executor = LiveExecutionModule()
        self.streams = [
            "wss://stream.binance.us:9443/ws/btcusdt@depth5",
            "wss://stream.binance.us:9443/ws/ethusdt@depth5"
        ]
        self.active_trades = 0
        self.total_volume = 0.0
        self.hft_process = None
        self.ticks_seen = 0

        # Shared Memory configuration
        self.shm = None
        self.input_base = 0
        self.input_header = self.input_base
        self.input_data = self.input_base + 128
        self.output_base = 196736
        self.output_header = self.output_base
        self.output_data = self.output_base + 128

    async def start_hft_engine(self):
        """Spawns the C++ Apex HDC engine."""
        print("[APEX-BRIDGE] Ensuring Apex HDC Binary is Compiled...")
        compile_cmd = "clang++ -std=c++17 -O3 -pthread cpp_core/xoras_apex_engine.cpp -o cpp_core/xoras_apex_engine"
        subprocess.run(compile_cmd, shell=True,
                       cwd=os.path.dirname(os.path.abspath(__file__)))

        print("[APEX-BRIDGE] Booting Apex Bare-Metal C++ Engine...")
        engine_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "cpp_core", "xoras_apex_engine")

        self.hft_process = await asyncio.create_subprocess_exec(
            engine_path,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Start a background task to constantly read C++ stdout to prevent pipe deadlocks
        asyncio.create_task(self._monitor_cpp_stdout())

        print("[APEX-BRIDGE] Waiting for C++ engine to map memory...")
        await asyncio.sleep(1.0)  # Wait for mmap to exist

        try:
            self.shm = shared_memory.SharedMemory(name=SHM_NAME)
            print(f"[APEX-BRIDGE] Successfully locked onto bare-metal memory block.")
        except FileNotFoundError:
            print(
                f"[APEX-BRIDGE] FATAL: SHM {SHM_NAME} not found. C++ Engine Boot Failure.")
            return

    async def _monitor_cpp_stdout(self):
        if not self.hft_process:
            return
        while True:
            line = await self.hft_process.stdout.readline()
            if not line:
                break
            print(f"[C++ ENGINE] {line.decode().strip()}")

    async def stop_hft_engine(self):
        """Terminates the Apex C++ engine."""
        if self.hft_process:
            print("[APEX-BRIDGE] Terminating Apex C++ Engine...")
            try:
                self.hft_process.terminate()
                await self.hft_process.wait()
            except Exception:
                pass
            self.hft_process = None

        if self.shm:
            try:
                self.shm.close()
            except Exception:
                pass
            self.shm = None

    def push_tick(self, symbol, bids, asks):
        if not self.shm:
            return False

        head = struct.unpack_from("Q", self.shm.buf, self.input_header)[0]
        tail = struct.unpack_from("Q", self.shm.buf, self.input_header + 64)[0]

        next_head = (head + 1) & (INPUT_CAPACITY - 1)
        if next_head == tail:
            return False  # Buffer full

        sym_bytes = symbol.encode('utf-8')[:15]
        timestamp = time.time_ns()
        offset = self.input_data + (head * TICK_SIZE)

        # Supervise C++ Holographic Learning
        self.ticks_seen += 1
        learn_flag = 0  # Infer by default

        # Teach it a basic paradigm for the first 50 ticks:
        # If the spread is extremely tight, call it a SELL prototype. If spread is loose, BUY prototype.
        # This is purely to seed the 10,000-bit vectors for the demonstration.
        if self.ticks_seen < 50:
            spread = asks[0][0] - bids[0][0]
            if spread < 0.5:
                learn_flag = 2  # Teach SELL
                print(f"[HDC-SUPERVISOR] Teaching C++ Engine SELL Prototype...")
            else:
                learn_flag = 1  # Teach BUY
                print(f"[HDC-SUPERVISOR] Teaching C++ Engine BUY Prototype...")

        struct.pack_into(TICK_FORMAT, self.shm.buf, offset,
                         sym_bytes,
                         bids[0][0], bids[1][0], bids[2][0], bids[3][0],  # Bid Prices
                         bids[0][1], bids[1][1], bids[2][1], bids[3][1],  # Bid Vols
                         asks[0][0], asks[1][0], asks[2][0], asks[3][0],  # Ask Prices
                         asks[0][1], asks[1][1], asks[2][1], asks[3][1],  # Ask Vols
                         timestamp, learn_flag)

        # Update input head
        struct.pack_into("Q", self.shm.buf, self.input_header, next_head)
        return True

    def pop_decision(self):
        if not self.shm:
            return None

        head = struct.unpack_from("Q", self.shm.buf, self.output_header)[0]
        tail = struct.unpack_from("Q", self.shm.buf, self.output_header + 64)[0]

        if tail == head:
            return None  # Buffer empty

        offset = self.output_data + (tail * DECISION_SIZE)
        data = struct.unpack_from(DECISION_FORMAT, self.shm.buf, offset)

        sym_raw, price, vol, ts, action, conf = data
        symbol = sym_raw.decode('utf-8').rstrip('\x00')

        # Advance output tail
        next_tail = (tail + 1) & (OUTPUT_CAPACITY - 1)
        struct.pack_into("Q", self.shm.buf, self.output_header + 64, next_tail)

        return {
            "symbol": symbol,
            "price": price,
            "volume": vol,
            "timestamp": ts,
            "action": action,  # 1=BUY, 2=SELL, 0=HOLD
            "confidence": conf
        }

    async def _listen_stream(self, url):
        """Listens to a public websocket for live market ticks."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    print(
                        f"[APEX-BRIDGE] Locked onto data stream: {url.split('/')[-1]}")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            symbol = url.split('/')[-1].split('@')[0].upper()

                            raw_bids = data.get('bids', [])
                            raw_asks = data.get('asks', [])

                            if len(raw_bids) >= 4 and len(raw_asks) >= 4:
                                try:
                                    # Convert to double floats for the binary structure
                                    bids = [[float(b[0]), float(b[1])]
                                            for b in raw_bids]
                                    asks = [[float(a[0]), float(a[1])]
                                            for a in raw_asks]

                                    # Inject raw binary
                                    pushed = self.push_tick(symbol, bids, asks)

                                    if pushed:
                                        # Poll for instant response
                                        dec = self.pop_decision()
                                        if dec and dec['action'] != 0:
                                            action_str = "BUY" if dec['action'] == 1 else "SELL"
                                            print(
                                                f"[APEX-EXECUTION] {action_str} {dec['symbol']} @ ${dec['price']} | Conf: {dec['confidence']}%")
                                            self.active_trades += 1
                                            self.total_volume += dec['price'] * \
                                                dec['volume']

                                            # Async AI Analysis + Execution
                                            asyncio.create_task(self.brain.analyze_arbitrage_opportunity(
                                                symbol, dec['price'], "Binance", "Kraken"))
                                            asyncio.create_task(self.executor.execute_trade(
                                                symbol, action_str, dec['price'], dec['volume']))

                                    # Write state for Kill Switch
                                    with open("xoras_state.json", "w") as f:
                                        json.dump(
                                            {"active_trades": self.active_trades, "timestamp": time.time()}, f)
                                except Exception as ex:
                                    print(f"[APEX-BRIDGE] Math execution fault: {ex}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
        except Exception as e:
            print(f"[APEX-BRIDGE] Stream error: {e}")

    async def ignite_streams(self):
        print("[APEX-BRIDGE] Igniting High-Frequency Websocket Engines...")
        await self.start_hft_engine()
        try:
            tasks = [self._listen_stream(url) for url in self.streams]
            await asyncio.gather(*tasks)
        finally:
            await self.stop_hft_engine()
