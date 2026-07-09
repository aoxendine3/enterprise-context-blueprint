import sqlite3
import os
import time

# Strict Path Compliance: All paths must point to the Desktop Xoras_Project
DB_PATH = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Omni_Dojo_Sandbox/Error_Catalyst/global_catalyst.db"
)
ARCHIVE_DIR = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Omni_Dojo_Sandbox/Wisdom_Archives/"
)


def compile_manual(record):
    err_id, timestamp, exc_type, err_msg, stack, status, heal_action = record

    filename = f"Wisdom_Record_{err_id}_{exc_type}.md"
    filepath = os.path.join(ARCHIVE_DIR, filename)

    content = f"""# Dojo Wisdom Record: {err_id}

**Timestamp:** {timestamp}
**Fault Type:** `{exc_type}`

## The Fracture
The system encountered a structural fault:
`{err_msg}`

### Trace
```python
{stack}
```

## The Healing (Resolution)
The Omni-Nexus resolved this fault via the following systemic action:
> {heal_action}

---
*Generated autonomously by the Xoras System Archivist for global AI integration.*
"""
    # Ensure archive dir exists
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"[XORAS ARCHIVIST] Compiled Training Manual: {filename}")


def run_archivist():
    if not os.path.exists(DB_PATH):
        print("[XORAS ARCHIVIST] Global DB not found. Waiting...")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure table exists just in case
    cursor.execute('''CREATE TABLE IF NOT EXISTS error_logs
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       exception_type TEXT,
                       error_message TEXT,
                       stack_trace TEXT,
                       status TEXT DEFAULT 'OPEN',
                       healing_action TEXT)''')

    # Find all healed but unarchived records
    cursor.execute("SELECT * FROM error_logs WHERE status='HEALED'")
    records = cursor.fetchall()

    for rec in records:
        compile_manual(rec)
        # Mark as archived
        cursor.execute("UPDATE error_logs SET status='ARCHIVED' WHERE id=?", (rec[0],))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Xoras System Archivist Daemon started. Scanning for HEALED resolutions...")
    while True:
        try:
            run_archivist()
        except Exception as e:
            print(f"Archivist encountered error: {e}")
        time.sleep(5)
