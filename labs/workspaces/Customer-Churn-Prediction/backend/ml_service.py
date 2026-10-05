from pathlib import Path
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).parent / "models" / "xgboost_churn_model.joblib"
_MODEL_CACHE = None
_MODEL_CACHE_LOADED = False

FEATURES = [
    "age",
    "total_orders",
    "days_since_last_purchase",
    "avg_order_value",
    "cart_abandonment_rate",
    "website_visits",
    "customer_rating",
    "return_count",
    "support_tickets",
]

REQUIRED_COLUMNS = [
    "Customer ID",
    "Age",
    "Gender",
    "Location",
    "Total Orders",
    "Last Purchase Date",
    "Average Order Value",
    "Cart Abandonment Rate (%)",
    "Website Visits",
    "Customer Rating",
    "Payment Method",
    "Return Count",
    "Support Tickets",
    "Churn Status",
]


def _load_model():
    global _MODEL_CACHE, _MODEL_CACHE_LOADED
    if _MODEL_CACHE_LOADED:
        return _MODEL_CACHE
    _MODEL_CACHE_LOADED = True
    if MODEL_PATH.exists():
        try:
            _MODEL_CACHE = joblib.load(MODEL_PATH)
        except Exception:
            _MODEL_CACHE = None
    return _MODEL_CACHE


def predict_churn(payload: dict) -> dict:
    """Return churn probability and risk label for a customer payload."""
    values = {k: _safe_float(payload.get(k, 0)) for k in FEATURES}
    model = _load_model()

    if model:
        X = pd.DataFrame([values])
        prob = float(model.predict_proba(X)[0][1]) * 100
    else:
        prob = _rule_based_score(values)

    prob = round(max(1.0, min(99.0, prob)), 1)
    risk = _risk_label(prob)
    action = _recommended_action(prob)

    return {
        "probability": prob,
        "risk": risk,
        "action": action,
        "features_used": values,
        "model_used": "XGBoost" if model else "Rule-Based (train model to enable XGBoost)",
    }


def _rule_based_score(v: dict) -> float:
    """Heuristic churn score when no trained model is available."""
    prob = 20.0
    prob += min(v["days_since_last_purchase"] / 1.8, 38.0)
    prob += min(v["cart_abandonment_rate"] / 2.8, 26.0)
    prob += min(v["support_tickets"] * 6.0, 18.0)
    prob += min(v["return_count"] * 3.0, 12.0)
    prob -= min(v["customer_rating"] * 5.0, 22.0)
    prob -= min(v["total_orders"] / 4.0, 14.0)
    prob += max(0, (3 - v["website_visits"] / 5.0) * 3.0)
    return prob


def _risk_label(prob: float) -> str:
    if prob < 35:
        return "Low Churn Risk"
    if prob < 70:
        return "Medium Churn Risk"
    return "High Churn Risk"


def _recommended_action(prob: float) -> str:
    if prob >= 70:
        return "Immediate intervention required. Send personalized discount (20%), assign account manager, and initiate win-back campaign."
    if prob >= 35:
        return "Schedule re-engagement email with product recommendations and offer loyalty reward points."
    return "Continue regular engagement. Include in standard newsletter and loyalty programme."


def validate_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def get_feature_importance() -> list[dict]:
    """Return feature importance list (from model if available, else defaults)."""
    model = _load_model()
    if model and hasattr(model, "feature_importances_"):
        scores = model.feature_importances_
        pairs = sorted(zip(FEATURES, scores), key=lambda x: x[1], reverse=True)
        return [{"feature": f.replace("_", " ").title(), "score": round(float(s) * 100, 1)} for f, s in pairs]

    # Default importance scores
    defaults = [
        ("Days Since Last Purchase", 22.4),
        ("Cart Abandonment Rate", 19.8),
        ("Support Tickets", 15.2),
        ("Return Count", 12.6),
        ("Customer Rating", 11.3),
        ("Website Visits", 8.9),
        ("Average Order Value", 5.4),
        ("Total Orders", 3.2),
        ("Age", 1.2),
    ]
    return [{"feature": f, "score": s} for f, s in defaults]


def _safe_float(val) -> float:
    import math
    try:
        if val is None or str(val).strip().lower() in ("", "n/a", "nan", "null", "none", "inf", "-inf"):
            return 0.0
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        return 0.0
