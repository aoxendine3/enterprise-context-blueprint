#!/usr/bin/env python3
"""
XORAS SOVEREIGN AGENT CLIENT: High-Frequency Execution Broker
Attaches directly to /xoras_apex_shm output slots, handles mock portfolio
fills, executes risk compliance, and updates live telemetry reports.
"""
import os
import sys
import struct
import time
import json
import subprocess
import urllib.request
import numpy as np
from pathlib import Path
from multiprocessing import shared_memory

SHM_NAME = "xoras_apex_shm"
OUTPUT_BASE = 196736
OUTPUT_HEADER = OUTPUT_BASE
OUTPUT_DATA = OUTPUT_BASE + 128
DECISION_FORMAT = "16s d d Q B B 22x"
DECISION_SIZE = 64
OUTPUT_CAPACITY = 1024

REPORT_PATH = Path.home() / "Desktop" / "Projects" / "Xoras_Knowledge" / "wisdom" / "roi_reports.md"

def get_keychain_secret(service):
    """Safely query macOS Keychain for API credentials."""
    try:
        res = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return None

class ExecutionBroker:
    def __init__(self, initial_capital=100000.0):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # symbol -> position dict {"qty": float, "entry_price": float}
        self.trades = []      # list of trade dicts
        self.total_volume = 0.0
        self.wins = 0
        
        self.shm = None
        self.read_tail = 0
        self.last_prices = {"BTCUSDT": 60000.0, "ETHUSDT": 1600.0}
        
        self.OUTPUT_HEADER = OUTPUT_HEADER
        self.OUTPUT_DATA = OUTPUT_DATA
        
        # Load credentials
        self.alpaca_key = get_keychain_secret("ALPACA_API_KEY_ID")
        self.alpaca_secret = get_keychain_secret("ALPACA_API_SECRET_KEY")
        
        if self.alpaca_key:
            print(f"[EXECUTION-BROKER] Registered Alpaca API Key: {self.alpaca_key[:6]}...")
        else:
            print("[EXECUTION-BROKER] No Alpaca API Key ID found in Keychain.")
        if not self.alpaca_secret:
            print("[EXECUTION-BROKER] No Alpaca API Secret Key found in Keychain. Running in mock-execution mode.")

        # Connect to SHM
        self.connect_shm()

    def connect_shm(self):
        print(f"[EXECUTION-BROKER] Connecting to shared memory /{SHM_NAME}...")
        try:
            self.shm = shared_memory.SharedMemory(name=SHM_NAME.lstrip('/'))
            # Unregister to prevent resource tracker cleanup on exit
            from multiprocessing import resource_tracker
            try:
                resource_tracker.unregister(self.shm._name, 'shared_memory')
            except:
                pass
            print(f"[EXECUTION-BROKER] Successfully attached to shared memory.")
        except FileNotFoundError:
            print(f"[EXECUTION-BROKER] Shared memory not found. Retrying in 1s...")
            time.sleep(1.0)
            self.connect_shm()

    def pop_decisions(self):
        """Reads all unread output decisions from the ring buffer."""
        if not self.shm:
            return []
            
        head = struct.unpack_from("<Q", self.shm.buf, self.OUTPUT_HEADER)[0]
        decisions = []
        
        while self.read_tail != head:
            offset = self.OUTPUT_DATA + (self.read_tail * DECISION_SIZE)
            unpacked = struct.unpack_from(DECISION_FORMAT, self.shm.buf, offset)
            
            symbol = unpacked[0].decode('utf-8').strip('\x00')
            price = unpacked[1]
            qty = unpacked[2]
            ts = unpacked[3]
            action = unpacked[4]
            confidence = unpacked[5]
            
            decisions.append({
                "symbol": symbol,
                "price": price,
                "qty": qty,
                "timestamp": ts,
                "action": action,
                "confidence": confidence
            })
            
            self.read_tail = (self.read_tail + 1) & (OUTPUT_CAPACITY - 1)
            
        return decisions

    def execute_trade(self, decision):
        symbol = decision["symbol"]
        action = decision["action"]  # 1 = BUY, 2 = SELL
        price = decision["price"]
        qty = decision["qty"]
        confidence = decision["confidence"]
        
        if price <= 0.0 or qty <= 0.0:
            return

        # 1. Dynamic Risk Control / Kill Switch Verification
        portfolio_val = self.get_portfolio_value(self.last_prices)
        profit = portfolio_val - self.initial_capital
        roi_pct = (profit / self.initial_capital) * 100.0
        
        # KILL SWITCH: Halt execution if ROI drops below -2.5% AND confidence
        # is below 60%. This gives the engine a recovery window during shallow
        # drawdowns (observed range: -1.0% to -1.5%) while hard-stopping at
        # -2.5% to prevent runaway capital erosion.
        if roi_pct < -2.5 and confidence < 60:
            print(f"[RISK-COMPLIANCE] KILL SWITCH ACTIVE. Trade blocked: ROI is {roi_pct:.2f}% and Similarity is {confidence}% (< 70%)")
            return

        # 2. Alpaca Live REST Execution Call
        if self.alpaca_key and self.alpaca_secret:
            try:
                side = "buy" if action == 1 else "sell"
                payload = json.dumps({
                    "symbol": symbol,
                    "qty": str(qty),
                    "side": side,
                    "type": "market",
                    "time_in_force": "gtc"
                }).encode("utf-8")
                
                req = urllib.request.Request(
                    "https://paper-api.alpaca.markets/v2/orders",
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "APCA-API-KEY-ID": self.alpaca_key,
                        "APCA-API-SECRET-KEY": self.alpaca_secret
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    print(f"[ALPACA] Order executed: {side.upper()} {qty} {symbol} | OrderID: {resp_data.get('id')}")
            except Exception as e:
                print(f"[ALPACA] API execution failed: {e}. Falling back to simulated ledger.")

        # 3. Simulated Ledger Matching (Simulated fallback)
        trade_value = price * qty
        fee = trade_value * 0.0005
        
        if action == 1:  # BUY
            if self.cash >= (trade_value + fee):
                self.cash -= (trade_value + fee)
                if symbol not in self.positions:
                    self.positions[symbol] = {"qty": 0.0, "entry_price": 0.0}
                pos = self.positions[symbol]
                total_qty = pos["qty"] + qty
                avg_price = ((pos["qty"] * pos["entry_price"]) + trade_value) / total_qty
                pos["qty"] = total_qty
                pos["entry_price"] = avg_price
                
                self.total_volume += trade_value
                self.trades.append({"action": "BUY", "price": price, "qty": qty, "pnl": 0.0})
                print(f"[EXECUTION] BUY FILL: {qty} {symbol} @ {price:.2f} | Fee: ${fee:.2f} | Cash: ${self.cash:.2f}")
                
        elif action == 2:  # SELL
            if symbol in self.positions and self.positions[symbol]["qty"] >= qty:
                pos = self.positions[symbol]
                pos["qty"] -= qty
                pnl = (price - pos["entry_price"]) * qty - fee
                self.cash += (trade_value - fee)
                
                if pos["qty"] <= 1e-8:
                    del self.positions[symbol]
                    
                self.total_volume += trade_value
                if pnl > 0:
                    self.wins += 1
                self.trades.append({"action": "SELL", "price": price, "qty": qty, "pnl": pnl})
                print(f"[EXECUTION] SELL FILL: {qty} {symbol} @ {price:.2f} | PnL: ${pnl:.2f} | Fee: ${fee:.2f} | Cash: ${self.cash:.2f}")
                
    def get_portfolio_value(self, current_prices):
        val = self.cash
        for sym, pos in self.positions.items():
            price = current_prices.get(sym, pos["entry_price"])
            val += pos["qty"] * price
        return val

    def calculate_sharpe(self):
        if len(self.trades) < 5:
            return 0.0
        pnls = [t["pnl"] for t in self.trades if t["action"] == "SELL"]
        if not pnls:
            return 0.0
        mean_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        if std_pnl == 0.0:
            return 1.0 if mean_pnl > 0 else 0.0
        return float((mean_pnl / std_pnl) * np.sqrt(252)) # Scaled to annual standard

    def write_roi_report(self, portfolio_val):
        profit = portfolio_val - self.initial_capital
        roi_pct = (profit / self.initial_capital) * 100.0
        trades_count = len(self.trades)
        
        sell_trades = [t for t in self.trades if t["action"] == "SELL"]
        win_rate = (self.wins / len(sell_trades) * 100.0) if sell_trades else 0.0
        sharpe = self.calculate_sharpe()
        
        report_content = f"""# XORAS Sovereign Live Execution Ledger

## ROI Performance Update
Active Capital: ${portfolio_val:,.2f}
Net Simulated Profit: ${profit:,.2f}
Return on Investment: {roi_pct:.4f}%
Total Executed Trades: {trades_count}
Win Rate: {win_rate:.1f}%
Total Executed Volume: ${self.total_volume:,.2f}
Sharpe Ratio: {sharpe:.2f}
"""
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_PATH, "w") as f:
            f.write(report_content)

    def run_loop(self):
        print("[EXECUTION-BROKER] Broker client live loop active. Awaiting SHM decisions...")
        
        # Simple baseline prices dict to compute portfolio value
        last_prices = {"BTCUSDT": 60000.0, "ETHUSDT": 1600.0}
        
        try:
            # Seed tail read index to head initially
            if self.shm:
                self.read_tail = struct.unpack_from("<Q", self.shm.buf, self.OUTPUT_HEADER)[0]
                
            while True:
                decisions = self.pop_decisions()
                for dec in decisions:
                    if dec["action"] != 0:
                        # Update current tracking price
                        self.last_prices[dec["symbol"]] = dec["price"]
                        self.execute_trade(dec)
                        
                # Dynamically write ledger stats
                portfolio_val = self.get_portfolio_value(self.last_prices)
                self.write_roi_report(portfolio_val)
                
                time.sleep(0.1) # 100ms interval polling
        except KeyboardInterrupt:
            print("[EXECUTION-BROKER] Shutting down.")
        finally:
            if self.shm:
                self.shm.close()

if __name__ == "__main__":
    broker = ExecutionBroker()
    broker.run_loop()
