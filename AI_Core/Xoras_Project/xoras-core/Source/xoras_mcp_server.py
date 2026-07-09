import os
import sqlite3
import json
from mcp.server.fastmcp import FastMCP

app = FastMCP("xoras-core")


@app.tool()
async def get_dojo_errors() -> str:
    """Fetch the latest errors from the Xoras Omni-Dojo SQLite ledger."""
    db_path = os.path.expanduser(
        "~/Desktop/Xoras_Project/xoras-core/Source/xoras_memory.db")
    if not os.path.exists(db_path):
        return json.dumps({"error": "DB not found"})
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, text, timestamp, domain "
            "FROM memory_vectors ORDER BY id DESC LIMIT 50"
        )
        rows = cursor.fetchall()

        errors = []
        for r in rows:
            errors.append({"id": r[0], "text": r[1], "timestamp": r[2], "domain": r[3]})
        return json.dumps(errors)
    except Exception as e:
        return json.dumps({"error": str(e)})


@app.tool()
async def execute_trade(symbol: str, side: str, quantity: float, price: float) -> str:
    """Execute a high-frequency trade via the Xoras Arbitrage Engine."""
    # In a real setup, this would push a struct into the POSIX SHM ring buffer
    # Here we mock the MCP command boundary
    return json.dumps({
        "status": "MOCK_SUCCESS",
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price
    })

if __name__ == "__main__":
    app.run()
