from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Load env from backend/.env regardless of cwd
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH)

_MONGODB_URI = (os.getenv("MONGODB_URI") or "").strip()
_MONGODB_DB = (os.getenv("MONGODB_DB") or "panscience").strip()

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return a cached Motor database instance."""
    global _client, _db

    if _db is not None:
        return _db

    if not _MONGODB_URI:
        raise RuntimeError("Missing MONGODB_URI in environment (.env)")

    _client = AsyncIOMotorClient(_MONGODB_URI)
    _db = _client[_MONGODB_DB]
    return _db
