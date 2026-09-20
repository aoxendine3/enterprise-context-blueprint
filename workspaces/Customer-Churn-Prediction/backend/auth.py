import os
import datetime
import jwt
from werkzeug.security import check_password_hash, generate_password_hash

SECRET = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")

DEFAULT_USERS = [
    {
        "email": os.getenv("ADMIN_EMAIL", "admin@churnshield.ai").lower(),
        "password": os.getenv("ADMIN_PASSWORD", "Admin@123"),
        "role": "Admin",
        "name": "ChurnShield Admin",
    },
    {
        "email": os.getenv("ANALYST_EMAIL", "analyst@churnshield.ai").lower(),
        "password": os.getenv("ANALYST_PASSWORD", "Analyst@123"),
        "role": "Data Analyst",
        "name": "Data Analyst",
    },
]


def seed_default_users(db):
    """Create real MongoDB login users when they are missing."""
    now = datetime.datetime.utcnow()
    for user in DEFAULT_USERS:
        existing = db.users.find_one({"email": user["email"]})
        if not existing:
            db.users.insert_one({
                "email": user["email"],
                "password_hash": generate_password_hash(user["password"]),
                "role": user["role"],
                "name": user["name"],
                "created_at": now,
                "updated_at": now,
            })


def make_token(email: str, role: str) -> str:
    payload = {
        "email": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def verify_login(db, email: str, password: str, role: str) -> dict | None:
    seed_default_users(db)
    user = db.users.find_one({"email": email.lower()})
    if not user:
        return None
    if not check_password_hash(user.get("password_hash", ""), password):
        return None
    if role and user.get("role") != role:
        return None
    return {
        "email": user["email"],
        "role": user.get("role", role or "Admin"),
        "name": user.get("name", "ChurnShield User"),
    }
