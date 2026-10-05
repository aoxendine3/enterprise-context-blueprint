#!/usr/bin/env python3
"""
Embedding Generation Script
==========================
Creates text embeddings using the Gemini Embedding API and stores them in the
LanceDB vector table ``demo_vectors``.

Prerequisites
-------------
* ``google-generativeai`` must be installed (already available in the environment).
* Set the Gemini API key in the environment: ``export GEMINI_API_KEY=your_key``.
* ``VAULT_DIR`` must be defined – it is exported by ``zenith_env.sh``.

Usage
-----
```bash
python3 ops/scripts/generate_embeddings.py data/sample_texts.csv
```
If the CSV path is omitted, ``data/sample_texts.csv`` is used by default.

The CSV must contain a column named ``text``. An ``id`` column is optional – if not
provided, sequential integers are assigned.
"""
import os
import sys
import csv
import json
from pathlib import Path
import pandas as pd

# Guard against missing API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.stderr.write("[Error] GEMINI_API_KEY environment variable is not set.\n")
    sys.exit(1)

# Initialise Gemini embedding client
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.embed_content

# Resolve vault directory
vault_dir = os.getenv("VAULT_DIR")
if not vault_dir:
    sys.stderr.write("[Error] VAULT_DIR not defined. Source zenith_env.sh first.\n")
    sys.exit(1)

# Import LanceDB – assumed already installed
import lancedb

def load_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.is_file():
        sys.stderr.write(f"[Error] CSV file not found: {csv_path}\n")
        sys.exit(1)
    df = pd.read_csv(csv_path)
    if "text" not in df.columns:
        sys.stderr.write("[Error] CSV must contain a 'text' column.\n")
        sys.exit(1)
    if "id" not in df.columns:
        df.insert(0, "id", range(1, len(df) + 1))
    return df

def embed_texts(texts: list[str]):
    embeddings = []
    for txt in texts:
        try:
            resp = model(
                model="text-embedding-004",
                content=txt,
                task_type="retrieval_document",
            )
            # The response contains "embedding" key with the vector
            embeddings.append(resp["embedding"])
        except Exception as e:
            sys.stderr.write(f"[Error] Embedding failed for text: {txt[:30]}… {e}\n")
            embeddings.append([])
    return embeddings

def main():
    # Determine CSV path
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = Path("data/sample_texts.csv")
    df = load_csv(csv_path)
    # Generate embeddings
    df["embedding"] = embed_texts(df["text"].tolist())
    # Connect to LanceDB
    db = lancedb.connect(vault_dir)
    table_name = "demo_vectors"
    # Create table if missing
    if table_name not in db.table_names():
        db.create_table(table_name, schema=df)
        print(f"Created table {table_name}.")
    table = db.open_table(table_name)
    # Upsert – LanceDB expects a DataFrame without the embedding column being a list of floats.
    # The simplest approach is to replace the existing rows by ID.
    table.add(df)
    print(f"Inserted {len(df)} records into {table_name}.")

if __name__ == "__main__":
    main()
