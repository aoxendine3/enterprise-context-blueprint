"""Import a customer CSV/Excel file into the live MongoDB customers collection.

Usage:
    python import_customers.py sample_data/customer_churn_sample.csv
"""
import sys
import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from database import get_db
from ml_service import validate_columns

load_dotenv()


def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return value


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample_data/customer_churn_sample.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    df = pd.read_csv(csv_path) if csv_path.suffix.lower() == ".csv" else pd.read_excel(csv_path)
    missing = validate_columns(df)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    db = get_db()
    count = 0
    now = datetime.datetime.utcnow()
    for _, row in df.iterrows():
        customer_id = str(row["Customer ID"]).strip()
        record = {str(col): clean_value(row[col]) for col in df.columns}
        record.update({
            "customer_id": customer_id,
            "updated_at": now,
            "import_source": str(csv_path),
        })
        db.customers.update_one({"customer_id": customer_id}, {"$set": record, "$setOnInsert": {"created_at": now}}, upsert=True)
        count += 1

    print(f"✅ Imported/updated {count} customers into MongoDB database '{db.name}', collection 'customers'.")


if __name__ == "__main__":
    main()
