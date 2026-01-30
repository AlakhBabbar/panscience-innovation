from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from bson import ObjectId
from dotenv import load_dotenv
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

# Load env from backend/.env regardless of cwd
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = (os.getenv("JWT_SECRET_KEY") or "").strip() or "dev-secret-change-me"
JWT_ALGORITHM = (os.getenv("JWT_ALGORITHM") or "HS256").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int((os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60").strip())


def _bcrypt_password_bytes(password: str) -> bytes:
    """Return a bcrypt-compatible password payload.

    bcrypt only uses the first 72 bytes of the password.
    """
    if password is None:
        return b""
    password_bytes = password.encode("utf-8")
    return password_bytes[:72] if len(password_bytes) > 72 else password_bytes


def _users(db: AsyncIOMotorDatabase):
    return db["users"]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await _users(db).create_index("email", unique=True)
    await _users(db).create_index("username", unique=True)


def hash_password(password: str) -> str:
    return pwd_context.hash(_bcrypt_password_bytes(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(_bcrypt_password_bytes(plain_password), password_hash)


async def create_user(db: AsyncIOMotorDatabase, email: str, username: str, password: str) -> dict[str, Any]:
    if not email or not email.strip():
        raise ValueError("Email is required")
    if not username or not username.strip():
        raise ValueError("Username is required")
    if not password:
        raise ValueError("Password is required")

    normalized_email = email.strip().lower()
    normalized_username = username.strip()

    existing_email = await _users(db).find_one({"email": normalized_email})
    if existing_email:
        raise ValueError("Email already registered")

    existing_username = await _users(db).find_one({"username": normalized_username})
    if existing_username:
        raise ValueError("Username already taken")

    doc = {
        "email": normalized_email,
        "username": normalized_username,
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc),
    }
    res = await _users(db).insert_one(doc)
    doc["_id"] = res.inserted_id
    return {"id": str(doc["_id"]), "email": doc["email"], "username": doc["username"]}


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict[str, Any]]:
    if not email:
        return None
    return await _users(db).find_one({"email": email.strip().lower()})


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict[str, Any]]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await _users(db).find_one({"_id": oid})


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[dict[str, Any]]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return {"id": str(user["_id"]), "email": user["email"], "username": user.get("username", "")}


def create_access_token(*, subject: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": subject,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e
