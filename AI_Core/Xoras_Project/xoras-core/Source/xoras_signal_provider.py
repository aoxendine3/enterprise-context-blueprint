import time
import datetime
import random
import sys

# Mocking MetaTrader5 import since the terminal is not yet installed on this Mac.
# In production, this will be: import MetaTrader5 as mt5


class MockMT5:
    @staticmethod
    def initialize():
        print("[MT5-BRIDGE] Initializing MetaTrader 5 connection...")
        return True

    @staticmethod
    def symbol_info_tick(symbol):
        # Mocking a tick response
        class Tick:
            ask = round(random.uniform(1.0500, 1.0600), 5)
            bid = ask - 0.0002
        return Tick()

    @staticmethod
    def order_send(request):
        # Mocking trade execution
        print(
            f"[MT5-BRIDGE] ---> ORDER SENT: {request['action']} {request['symbol']} @ {request['price']}")

        class Result:
            retcode = 10009  # mt5.TRADE_RETCODE_DONE
        return Result()


mt5 = MockMT5()


def run_signal_provider():
    print("[SIGNAL-PROVIDER] Starting Background Daemon...")

    if not mt5.initialize():
        print("[SIGNAL-PROVIDER] Failed to initialize MT5. Exiting.")
        sys.exit(1)

    symbol = "EURUSD"
    print(f"[SIGNAL-PROVIDER] Subscribed to {symbol}. Waiting for logic trigger...")

    while True:
        try:
            # Fetch market data
            tick = mt5.symbol_info_tick(symbol)

            # --- SIGNAL LOGIC (MOCK EMA CROSSOVER) ---
            # In a live environment, this evaluates 1-hour candles.
            # For demonstration, we trigger a random mock trade occasionally.
            if random.random() > 0.95:
                action = "BUY" if random.random() > 0.5 else "SELL"
                price = tick.ask if action == "BUY" else tick.bid

                request = {
                    "action": action,
                    "symbol": symbol,
                    "volume": 0.1,
                    "price": price,
                    "type": "ORDER_TYPE_BUY" if action == "BUY" else "ORDER_TYPE_SELL"
                }

                print(
                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SIGNAL-PROVIDER] Logic Triggered: {action} {symbol}!")
                result = mt5.order_send(request)

                if result.retcode == 10009:  # TRADE_RETCODE_DONE
                    print("[SIGNAL-PROVIDER] Trade executed successfully on MT5 Terminal.")
                    print("[SIGNAL-PROVIDER] Signal broadcast to followers.")

            time.sleep(5)  # Poll every 5 seconds for demonstration

        except KeyboardInterrupt:
            print("[SIGNAL-PROVIDER] Shutting down.")
            break


if __name__ == "__main__":
    run_signal_provider()
