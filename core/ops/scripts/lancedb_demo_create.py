#!/usr/bin/env python3
"""Create a demo table in the LanceDB vault.
This script is intended for quick verification that the vault is writable.
It creates a table named `demo_vectors` with a few sample rows.
"""
import os
import sys
import pandas as pd

# Ensure the environment variable is set (source zenith_env.sh first)
vault_dir = os.getenv("VAULT_DIR")
if not vault_dir:
    print("[ERROR] VAULT_DIR is not set. Source zenith_env.sh first.")
    sys.exit(1)

import lancedb

print(f"Connecting to vault: {vault_dir}")
db = lancedb.connect(vault_dir)

# Sample data
df = pd.DataFrame({
    "id": [1, 2, 3],
    "text": ["first", "second", "third"],
    "embedding": [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 1.0, 1.1, 1.2],
    ],
})

# Create or replace the table
table_name = "demo_vectors"
# Use deprecated but functional table_names() to get list
if table_name in db.table_names():
    print(f"Table '{table_name}' already exists – dropping for fresh start.")
    db.drop_table(table_name)

print(f"Creating table '{table_name}'...")
table = db.create_table(table_name, data=df)
print("Table created. Current tables:", db.list_tables())

