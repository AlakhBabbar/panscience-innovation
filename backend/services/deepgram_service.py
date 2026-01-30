from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

# Load env from backend/.env regardless of cwd
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH)


def _seconds_to_hms(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _extract_segments_from_deepgram(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract a flat list of timestamped segments.

    Prefers Deepgram 'utterances' when available; otherwise falls back to paragraphs or words.
    Returned items: {start: float, end: float, text: str}
    """
    results = payload.get("results") or {}

    utterances = results.get("utterances")
    if isinstance(utterances, list) and utterances:
        segs: list[dict[str, Any]] = []
        for u in utterances:
            text = str(u.get("transcript") or "").strip()
            if not text:
                continue
            segs.append(
                {
                    "start": float(u.get("start") or 0.0),
                    "end": float(u.get("end") or 0.0),
                    "text": text,
                }
            )
        if segs:
            return segs

    # Paragraphs fallback
    channels = results.get("channels")
    if isinstance(channels, list) and channels:
        alts = (channels[0] or {}).get("alternatives")
        if isinstance(alts, list) and alts:
            alt0 = alts[0] or {}
            paragraphs = (alt0.get("paragraphs") or {}).get("paragraphs")
            if isinstance(paragraphs, list) and paragraphs:
                segs = []
                for p in paragraphs:
                    sentences = p.get("sentences")
                    if isinstance(sentences, list) and sentences:
                        text = " ".join([str(s.get("text") or "").strip() for s in sentences]).strip()
                    else:
                        text = str(p.get("text") or "").strip()
                    if not text:
                        continue
                    segs.append(
                        {
                            "start": float(p.get("start") or 0.0),
                            "end": float(p.get("end") or 0.0),
                            "text": text,
                        }
                    )
                if segs:
                    return segs

            # Words fallback (grouped)
            words = alt0.get("words")
            if isinstance(words, list) and words:
                segs = []
                bucket: list[str] = []
                bucket_start: Optional[float] = None
                bucket_end: Optional[float] = None
                max_bucket_seconds = 8.0

                for w in words:
                    word = str(w.get("word") or "").strip()
                    if not word:
                        continue
                    w_start = float(w.get("start") or 0.0)
                    w_end = float(w.get("end") or w_start)

                    if bucket_start is None:
                        bucket_start = w_start
                        bucket_end = w_end
                        bucket = [word]
                        continue

                    # start new bucket if too large
                    if (w_end - bucket_start) > max_bucket_seconds:
                        segs.append(
                            {
                                "start": float(bucket_start),
                                "end": float(bucket_end or bucket_start),
                                "text": " ".join(bucket).strip(),
                            }
                        )
                        bucket_start = w_start
                        bucket_end = w_end
                        bucket = [word]
                    else:
                        bucket.append(word)
                        bucket_end = w_end

                if bucket and bucket_start is not None:
                    segs.append(
                        {
                            "start": float(bucket_start),
                            "end": float(bucket_end or bucket_start),
                            "text": " ".join(bucket).strip(),
                        }
                    )
                return segs

    return []


async def transcribe_media_bytes(
    *,
    data: bytes,
    mimetype: str,
    filename: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    api_key = (os.getenv("DEEPGRAM_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Missing DEEPGRAM_API_KEY in environment (.env)")

    # Deepgram prerecorded transcription endpoint
    # Docs: https://developers.deepgram.com
    params: dict[str, str] = {
        "model": os.getenv("DEEPGRAM_MODEL", "nova-2"),
        "smart_format": "true",
        "punctuate": "true",
        "utterances": "true",
        "paragraphs": "true",
    }
    if language:
        params["language"] = language

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": mimetype or "application/octet-stream",
    }

    url = "https://api.deepgram.com/v1/listen"

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        resp = await client.post(url, params=params, headers=headers, content=data)

    if resp.status_code >= 400:
        detail = resp.text
        raise RuntimeError(f"Deepgram transcription failed ({resp.status_code}): {detail}")

    payload = resp.json()
    segments = _extract_segments_from_deepgram(payload)

    # Best-effort metadata
    duration = None
    try:
        duration = float((payload.get("metadata") or {}).get("duration") or 0.0)
    except Exception:
        duration = None

    transcript = "\n".join(
        [f"[{_seconds_to_hms(s['start'])} - {_seconds_to_hms(s['end'])}] {s['text']}" for s in segments]
    ).strip()

    return {
        "filename": filename,
        "mimetype": mimetype,
        "duration": duration,
        "segments": segments,
        "transcript": transcript,
        "raw": payload,  # helpful for debugging; you can remove later if you want
    }
