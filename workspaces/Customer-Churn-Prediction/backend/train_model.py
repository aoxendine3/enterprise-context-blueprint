"""
train_model.py — Train the XGBoost churn prediction model.

Usage:
    python train_model.py                         # uses sample_data/
    python train_model.py path/to/your_data.csv  # uses your file
"""

import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  xgboost not installed. Run: pip install xgboost")

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

FEATURE_MAP = {
    "Age": "age",
    "Total Orders": "total_orders",
    "Last Purchase Date": "days_since_last_purchase",
    "Average Order Value": "avg_order_value",
    "Cart Abandonment Rate (%)": "cart_abandonment_rate",
    "Website Visits": "website_visits",
    "Customer Rating": "customer_rating",
    "Return Count": "return_count",
    "Support Tickets": "support_tickets",
}
TARGET = "Churn Status"


def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    print(f"📁 Loaded {len(df):,} rows from {csv_path.name}")
    return df


def preprocess(df: pd.DataFrame):
    df = df.copy()

    # Convert last purchase date to days since
    if "Last Purchase Date" in df.columns:
        df["Last Purchase Date"] = pd.to_datetime(df["Last Purchase Date"], errors="coerce")
        ref = df["Last Purchase Date"].max()
        df["Last Purchase Date"] = (ref - df["Last Purchase Date"]).dt.days.fillna(30)

    feature_cols = list(FEATURE_MAP.keys())
    present = [c for c in feature_cols if c in df.columns]
    X = df[present].rename(columns=FEATURE_MAP)
    y = df[TARGET].astype(int)

    for col in X.select_dtypes(include="object").columns:
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))

    X = X.fillna(X.median())
    return X, y


def train(X, y):
    if not XGBOOST_AVAILABLE:
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred) * 100, 2),
        "precision": round(precision_score(y_test, y_pred) * 100, 2),
        "recall": round(recall_score(y_test, y_pred) * 100, 2),
        "f1_score": round(f1_score(y_test, y_pred) * 100, 2),
        "roc_auc": round(roc_auc_score(y_test, y_prob) * 100, 2),
    }

    print("\n📊 Model Metrics:")
    for k, v in metrics.items():
        print(f"   {k:12s}: {v:.2f}%")

    return model, metrics


def save(model, metrics):
    model_path = MODEL_DIR / "xgboost_churn_model.joblib"
    metrics_path = MODEL_DIR / "metrics.json"
    joblib.dump(model, model_path)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n✅ Model saved to {model_path}")
    print(f"✅ Metrics saved to {metrics_path}")


if __name__ == "__main__":
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sample_data" / "customer_churn_sample.csv"
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        sys.exit(1)

    df = load_data(data_path)
    X, y = preprocess(df)
    print(f"🔢 Features: {list(X.columns)}")
    print(f"🎯 Class distribution: {y.value_counts().to_dict()}")

    model, metrics = train(X, y)
    save(model, metrics)
    print("\n🚀 Training complete! Restart the API to use the new model.")
