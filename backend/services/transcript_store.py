from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _transcripts(db: AsyncIOMotorDatabase):
    return db["media_transcripts"]


def _oid(value: str) -> ObjectId:
    return ObjectId(value)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await _transcripts(db).create_index([("user_id", 1), ("created_at", -1)])


async def create_transcript(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    filename: str | None,
    mimetype: str | None,
    duration: float | None,
    segments: list[dict[str, Any]],
) -> dict[str, Any]:
    doc = {
        "user_id": user_id,
        "filename": filename,
        "mimetype": mimetype,
        "duration": duration,
        "segments": segments,
        "created_at": _now(),
    }
    res = await _transcripts(db).insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


async def get_transcript(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    transcript_id: str,
) -> Optional[dict[str, Any]]:
    try:
        oid = _oid(transcript_id)
    except Exception:
        return None
    return await _transcripts(db).find_one({"_id": oid, "user_id": user_id})


async def list_transcripts(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    cursor = _transcripts(db).find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
