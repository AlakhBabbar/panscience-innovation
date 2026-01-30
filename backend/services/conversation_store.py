from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _conversations(db: AsyncIOMotorDatabase):
    return db["conversations"]


def _messages(db: AsyncIOMotorDatabase):
    return db["messages"]


def _oid(value: str) -> ObjectId:
    return ObjectId(value)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # Fast lookup by user
    await _conversations(db).create_index([("user_id", 1), ("updated_at", -1)])
    await _messages(db).create_index([("conversation_id", 1), ("created_at", 1)])


async def create_conversation(db: AsyncIOMotorDatabase, *, user_id: str, title: str) -> dict[str, Any]:
    now = _now()
    doc = {
        "user_id": user_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
    }
    res = await _conversations(db).insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


async def list_conversations(db: AsyncIOMotorDatabase, *, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    cursor = _conversations(db).find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_conversation(db: AsyncIOMotorDatabase, *, user_id: str, conversation_id: str) -> Optional[dict[str, Any]]:
    try:
        oid = _oid(conversation_id)
    except Exception:
        return None
    return await _conversations(db).find_one({"_id": oid, "user_id": user_id})


async def delete_conversation(db: AsyncIOMotorDatabase, *, user_id: str, conversation_id: str) -> bool:
    try:
        oid = _oid(conversation_id)
    except Exception:
        return False

    await _messages(db).delete_many({"conversation_id": oid, "user_id": user_id})
    res = await _conversations(db).delete_one({"_id": oid, "user_id": user_id})
    return res.deleted_count == 1


async def append_message(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    conversation_id: str,
    sender: str,
    text: str,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    now = _now()

    oid = _oid(conversation_id)
    msg = {
        "user_id": user_id,
        "conversation_id": oid,
        "sender": sender,
        "text": text,
        "attachments": attachments or [],
        "created_at": now,
    }
    res = await _messages(db).insert_one(msg)
    msg["_id"] = res.inserted_id

    await _conversations(db).update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": {"updated_at": now}},
    )

    return msg


async def update_conversation_title(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    conversation_id: str,
    title: str,
) -> bool:
    try:
        oid = _oid(conversation_id)
    except Exception:
        return False

    res = await _conversations(db).update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": {"title": title}},
    )
    return res.matched_count == 1


async def update_conversation_title_if_placeholder(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    conversation_id: str,
    title: str,
    placeholders: list[str] | None = None,
) -> bool:
    placeholders = placeholders or ["New Chat", "Chat", "Conversation"]
    try:
        oid = _oid(conversation_id)
    except Exception:
        return False

    res = await _conversations(db).update_one(
        {"_id": oid, "user_id": user_id, "title": {"$in": placeholders}},
        {"$set": {"title": title}},
    )
    return res.modified_count == 1


async def list_messages(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    conversation_id: str,
    limit: int = 200,
) -> list[dict[str, Any]]:
    try:
        oid = _oid(conversation_id)
    except Exception:
        return []

    cursor = (
        _messages(db)
        .find({"conversation_id": oid, "user_id": user_id})
        .sort("created_at", 1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
