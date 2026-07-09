import asyncio
import websockets
import json
import time
import os
import struct
import subprocess
import signal
import sys
from multiprocessing import shared_memory

# OrderBookTick struct size = 192 bytes
# Struct format: 16s (char[16]) + 8d (bid_prices, bid_vols) + 8d (ask_prices, ask_vols) + Q (uint64_t) + 40x (padding)
# Layout: 16s d d d d d d d d d d d d d d d d Q 40x
TICK_FORMAT = "16s dddddddd dddddddd Q B 39x"
TICK_SIZE = 192

# MarketDecision struct size = 64 bytes
# Struct format: 16s (char[16]) + d (price) + d (vol) + Q (timestamp) + B (action) + B (conf) + 22x (padding)
DECISION_FORMAT = "16s d d Q B B 22x"
DECISION_SIZE = 64

# RingBuffer Header Offset = 128 bytes (two 64-byte aligned atomic size_t)
# ApexMemoryBlock Layout:
# input_ring: 128b header + (192b * 1024) data = 128 + 196608 = 196736 bytes
# output_ring: 128b header + (64b * 1024) data = 128 + 65536 = 65664 bytes
# Total memory size = 196736 + 65664 = 262400 bytes

INPUT_CAPACITY = 1024
OUTPUT_CAPACITY = 1024
SHM_NAME = "/xoras_apex_shm"


class ApexBridge:
    def __init__(self):
        self.shm = None
        self.hft_process = None

        # Start C++ Engine
        self.start_cpp_engine()

        # Connect to SHM
        print("[BRIDGE] Waiting for C++ engine to map memory...")
        time.sleep(1.0)  # Wait for C++ to create the mmap

        # In Python, shm names don't take the leading slash in the shared_memory module
        try:
            from multiprocessing import resource_tracker
            self.shm = shared_memory.SharedMemory(name=SHM_NAME.lstrip('/'))
            try:
                resource_tracker.unregister(self.shm._name, "shared_memory")
            except Exception:
                pass
            print(f"[BRIDGE] Successfully mapped to {SHM_NAME}")
        except FileNotFoundError:
            print(f"[BRIDGE] FATAL: SHM {SHM_NAME} not found. Did C++ engine start?")
            sys.exit(1)

        # Offsets
        self.input_base = 0
        self.input_header = self.input_base
        self.input_data = self.input_base + 128

        self.output_base = 196736
        self.output_header = self.output_base
        self.output_data = self.output_base + 128

        # Perform baseline training
        self.train_engine_baseline()

    def train_engine_baseline(self):
        print("[BRIDGE] Seeding C++ HDC Engine with baseline training samples...")
        # Baseline BUY pattern (high bid prices, low ask vols)
        bids_buy = [[10000.1, 1.0], [9999.1, 2.0], [9998.1, 3.0], [9997.1, 4.0]]
        asks_buy = [[10002.1, 1.0], [10003.1, 2.0], [10004.1, 3.0], [10005.1, 4.0]]
        self.push_tick("BTCUSDT", bids_buy, asks_buy, learn_flag=1)

        # Baseline SELL pattern (low bid prices, high ask vols)
        bids_sell = [[89000.3, 1.0], [88999.3, 2.0], [88998.3, 3.0], [88997.3, 4.0]]
        asks_sell = [[89002.3, 1.0], [89003.3, 2.0], [89004.3, 3.0], [89005.3, 4.0]]
        self.push_tick("BTCUSDT", bids_sell, asks_sell, learn_flag=2)
        print("[BRIDGE] HDC Engine trained successfully.")

    def start_cpp_engine(self):
        print("[BRIDGE] Compiling Apex C++ Engine...")
        compile_cmd = "clang++ -std=c++17 -O3 -pthread xoras_apex_engine.cpp -o xoras_apex_engine"
        subprocess.run(compile_cmd, shell=True,
                       cwd=os.path.dirname(os.path.abspath(__file__)))

        print("[BRIDGE] Booting Apex C++ Engine...")
        engine_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "xoras_apex_engine")
        self.hft_process = subprocess.Popen([engine_path])

    def push_tick(self, symbol, bids, asks, learn_flag=0):
        # Read input head and tail
        head = struct.unpack_from("Q", self.shm.buf, self.input_header)[0]
        tail = struct.unpack_from("Q", self.shm.buf, self.input_header + 64)[0]

        next_head = (head + 1) & (INPUT_CAPACITY - 1)
        if next_head == tail:
            return False  # Buffer full

        # Pack the data
        sym_bytes = symbol.encode('utf-8')[:15]
        timestamp = time.time_ns()

        offset = self.input_data + (head * TICK_SIZE)
        struct.pack_into(TICK_FORMAT, self.shm.buf, offset,
                         sym_bytes,
                         bids[0][0], bids[1][0], bids[2][0], bids[3][0],  # Bid Prices
                         bids[0][1], bids[1][1], bids[2][1], bids[3][1],  # Bid Vols
                         asks[0][0], asks[1][0], asks[2][0], asks[3][0],  # Ask Prices
                         asks[0][1], asks[1][1], asks[2][1], asks[3][1],  # Ask Vols
                         timestamp,
                         learn_flag)

        # Update head
        struct.pack_into("Q", self.shm.buf, self.input_header, next_head)
        return True

    def pop_decision(self):
        head = struct.unpack_from("Q", self.shm.buf, self.output_header)[0]
        tail = struct.unpack_from("Q", self.shm.buf, self.output_header + 64)[0]

        if tail == head:
            return None  # Buffer empty

        offset = self.output_data + (tail * DECISION_SIZE)
        data = struct.unpack_from(DECISION_FORMAT, self.shm.buf, offset)

        sym_raw, price, vol, ts, action, conf = data
        symbol = sym_raw.decode('utf-8').rstrip('\x00')

        # Update tail
        next_tail = (tail + 1) & (OUTPUT_CAPACITY - 1)
        struct.pack_into("Q", self.shm.buf, self.output_header + 64, next_tail)

        return {
            "symbol": symbol,
            "price": price,
            "volume": vol,
            "timestamp": ts,
            "action": action,
            "confidence": conf
        }

    async def run_simulation(self):
        print("[BRIDGE] Simulating High-Frequency Websocket Stream...")

        bids = [[10000.0, 1.0], [9999.0, 2.0], [9998.0, 3.0], [9997.0, 4.0]]
        asks = [[10001.0, 1.0], [10002.0, 2.0], [10003.0, 3.0], [10004.0, 4.0]]

        total_signals = 100000
        start_t = time.time()

        for i in range(total_signals):
            bids[0][0] += 0.1
            self.push_tick("BTCUSDT", bids, asks)

            dec = self.pop_decision()
            if dec and dec['action'] != 0:
                action_str = "BUY" if dec['action'] == 1 else "SELL"
                if i % 10000 == 0:
                    print(
                        f"[BRIDGE] Dec: {action_str} {dec['symbol']} @ {dec['price']} | Conf: {dec['confidence']}%")

            await asyncio.sleep(0.00001)

        end_t = time.time()
        print(
            f"[BRIDGE] Processed {total_signals} simulated ticks via SHM in {end_t - start_t:.3f} seconds.")

    async def run_live_websocket(self):
        url = "wss://stream.binance.us:9443/ws/btcusdt@depth5"
        print(f"[BRIDGE] Connecting to live Binance WebSocket: {url}...")
        try:
            async with websockets.connect(url) as websocket:
                print("[BRIDGE] Connected. Streaming live order book ticks...")
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    # Parse bids and asks
                    bids = [[float(b[0]), float(b[1])] for b in data['bids']]
                    asks = [[float(a[0]), float(a[1])] for a in data['asks']]
                    
                    # Ensure we have at least 4 levels
                    while len(bids) < 4:
                        bids.append([0.0, 0.0])
                    while len(asks) < 4:
                        asks.append([0.0, 0.0])
                        
                    # Push to C++ engine
                    self.push_tick("BTCUSDT", bids[:4], asks[:4])
                    
                    # Pop decision
                    dec = self.pop_decision()
                    if dec and dec['action'] != 0:
                        action_str = "BUY" if dec['action'] == 1 else "SELL"
                        latency_us = (time.time_ns() - dec['timestamp']) / 1000.0
                        print(f"[TRADE SIGNAL] {action_str} {dec['symbol']} @ {dec['price']} | Confidence: {dec['confidence']}% | Latency: {latency_us:.2f} us")
        except Exception as e:
            print(f"[BRIDGE] WebSocket error: {e}")

    def cleanup(self):
        if self.hft_process:
            print("[BRIDGE] Terminating C++ Engine...")
            self.hft_process.terminate()
            self.hft_process.wait()
        if self.shm:
            self.shm.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run with live Binance WebSocket stream")
    args = parser.parse_args()

    bridge = ApexBridge()
    try:
        if args.live:
            await bridge.run_live_websocket()
        else:
            await bridge.run_simulation()
    except KeyboardInterrupt:
        print("\n[BRIDGE] Interrupted by user.")
    finally:
        bridge.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
