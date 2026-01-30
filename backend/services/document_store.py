"""
MongoDB store for parsed documents.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _documents(db: AsyncIOMotorDatabase):
    return db["parsed_documents"]


def _oid(value: str) -> ObjectId:
    return ObjectId(value)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes for fast document lookup."""
    await _documents(db).create_index([("user_id", 1), ("created_at", -1)])


async def create_document(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    filename: str,
    mimetype: str,
    content: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Store a parsed document."""
    now = _now()
    doc = {
        "user_id": user_id,
        "filename": filename,
        "mimetype": mimetype,
        "content": content,
        "metadata": metadata,
        "created_at": now,
    }
    res = await _documents(db).insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


async def get_document(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    document_id: str,
) -> Optional[dict[str, Any]]:
    """Retrieve a parsed document by ID (with ownership check)."""
    try:
        oid = _oid(document_id)
    except Exception:
        return None
    return await _documents(db).find_one({"_id": oid, "user_id": user_id})


async def list_documents(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """List recent parsed documents for a user."""
    cursor = (
        _documents(db)
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
