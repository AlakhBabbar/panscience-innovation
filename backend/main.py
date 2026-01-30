from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import asyncio
import logging
import re
from pydantic import BaseModel
from pydantic import EmailStr
from typing import List, Optional
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from services.chat_service import (
    generate_chat_response,
    generate_chat_response_with_history,
    generate_chat_title,
    reset_conversation,
)
from services.deepgram_service import transcribe_media_bytes
from services.document_service import parse_document_bytes
from db.mongo import get_db
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    decode_access_token,
    get_user_by_id,
    ensure_indexes as ensure_auth_indexes,
)
from services.conversation_store import (
    append_message,
    create_conversation as create_conversation_doc,
    delete_conversation as delete_conversation_doc,
    ensure_indexes as ensure_conversation_indexes,
    get_conversation as get_conversation_doc,
    list_conversations as list_conversation_docs,
    list_messages,
    update_conversation_title_if_placeholder,
)
from services.transcript_store import (
    create_transcript,
    ensure_indexes as ensure_transcript_indexes,
    get_transcript,
    list_transcripts,
)
from services.document_store import (
    create_document,
    ensure_indexes as ensure_document_indexes,
    get_document,
    list_documents,
)

_log = logging.getLogger("panscience")


async def _generate_and_persist_title(
    *,
    db: AsyncIOMotorDatabase,
    user_id: str,
    conversation_id: str,
    first_user_message: str,
    first_assistant_message: str,
) -> None:
    try:
        title = await asyncio.to_thread(generate_chat_title, first_user_message, first_assistant_message)
        await update_conversation_title_if_placeholder(
            db,
            user_id=user_id,
            conversation_id=conversation_id,
            title=title,
        )
    except Exception as e:
        _log.warning("Failed to generate/persist conversation title: %s", e)


# Custom CORS middleware for Vercel
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "https://panscience-innovation-assessment-al.vercel.app",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                },
            )
        
        response = await call_next(request)
        
        # Add CORS headers to all responses
        origin = request.headers.get("origin", "")
        allowed_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://panscience-innovation-assessment-al.vercel.app",
        ]
        
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

app = FastAPI(title="PanScience Chat API", version="1.0.0")

# Add custom CORS middleware first
app.add_middleware(CORSHeaderMiddleware)

# CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://panscience-innovation-assessment-al.vercel.app",
    ],  # Vite, CRA, and deployed Vercel frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Pydantic models
class Attachment(BaseModel):
    name: str
    kind: str
    mimetype: Optional[str] = None


class Message(BaseModel):
    text: str
    sender: str
    timestamp: Optional[str] = None
    attachments: Optional[list[Attachment]] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    transcript_id: Optional[str] = None
    document_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attachments: Optional[list[Attachment]] = None

class ChatResponse(BaseModel):
    message: str
    timestamp: str
    conversation_id: str


class TranscribeResponse(BaseModel):
    transcript_id: str
    filename: Optional[str] = None
    mimetype: Optional[str] = None
    duration: Optional[float] = None
    segments: list[dict]


class MediaAnswerRequest(BaseModel):
    transcript_id: str
    question: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class MediaAnswerResponse(BaseModel):
    answer: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: Optional[str] = None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserResponse:
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Invalid token")
        user_id = str(subject)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse(id=str(user["_id"]), email=user["email"], username=user.get("username"))

class Conversation(BaseModel):
    id: str
    title: str
    date: str
    messages: List[Message] = []


def _to_message(doc: dict) -> Message:
    return Message(
        text=doc.get("text", ""),
        sender=doc.get("sender", ""),
        timestamp=(doc.get("created_at") or datetime.now(timezone.utc)).isoformat(),
        attachments=[Attachment(**a) for a in (doc.get("attachments") or []) if isinstance(a, dict)] or None,
    )


def _to_conversation(conv: dict, messages: list[dict]) -> Conversation:
    updated_at = conv.get("updated_at") or conv.get("created_at") or datetime.now(timezone.utc)
    return Conversation(
        id=str(conv.get("_id")),
        title=conv.get("title", "Conversation"),
        date=updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
        messages=[_to_message(m) for m in messages],
    )


_TS_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")


def _looks_transcript_related(message: str, *, start_time: Optional[float], end_time: Optional[float]) -> bool:
    """Heuristic: only use a transcript when the prompt clearly refers to it."""
    if start_time is not None or end_time is not None:
        return True

    text = (message or "").strip().lower()
    if not text:
        return False

    if _TS_RE.search(text):
        return True

    keywords = (
        "transcript",
        "recording",
        "audio",
        "video",
        "clip",
        "attached",
        "the file",
        "timestamp",
        "timecode",
        "minute",
        "minutes",
        "second",
        "seconds",
    )
    return any(k in text for k in keywords)


@app.on_event("startup")
async def _startup() -> None:
    db = get_db()
    await ensure_auth_indexes(db)
    await ensure_conversation_indexes(db)
    await ensure_transcript_indexes(db)
    await ensure_document_indexes(db)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PanScience Chat API",
        "status": "active",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/auth/register", response_model=UserResponse)
async def register(request: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Create a user account (signup)."""
    try:
        user = await create_user(db, request.email, request.username, request.password)
        return UserResponse(id=str(user["id"]), email=user["email"], username=user.get("username"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """OAuth2 password flow: returns a Bearer JWT access token.

    Note: OAuth2PasswordRequestForm uses fields `username` + `password`.
    We treat `username` as the user's email.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=str(user["id"]), email=user["email"])
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@app.get("/api/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get all conversations for the current user."""
    convs = await list_conversation_docs(db, user_id=current_user.id)
    out: list[Conversation] = []
    for c in convs:
        updated_at = c.get("updated_at") or c.get("created_at") or datetime.now(timezone.utc)
        out.append(
            Conversation(
                id=str(c.get("_id")),
                title=c.get("title", "Conversation"),
                date=updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
                messages=[],
            )
        )
    return out

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get a specific conversation by ID."""
    conv = await get_conversation_doc(db, user_id=current_user.id, conversation_id=conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = await list_messages(db, user_id=current_user.id, conversation_id=conversation_id, limit=200)
    return _to_conversation(conv, msgs)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Handle chat messages"""
    conversation_id = request.conversation_id
    created_new = False
    if conversation_id:
        existing = await get_conversation_doc(db, user_id=current_user.id, conversation_id=conversation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = await create_conversation_doc(
            db,
            user_id=current_user.id,
            title="New Chat",
        )
        conversation_id = str(convo["_id"])
        created_new = True

    # Pull history BEFORE inserting the new user message, so the LLM doesn't see
    # the prompt twice.
    recent = await list_messages(db, user_id=current_user.id, conversation_id=conversation_id, limit=200)
    history: list[dict] = [
        {"sender": m.get("sender"), "text": m.get("text")}
        for m in recent
        if isinstance(m, dict) and (m.get("text") or "").strip()
    ]

    await append_message(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        sender="user",
        text=request.message,
        attachments=[a.model_dump() for a in (request.attachments or [])],
    )

    try:
        use_transcript = bool(
            request.transcript_id
            and _looks_transcript_related(
                request.message,
                start_time=request.start_time,
                end_time=request.end_time,
            )
        )

        # Check if document is attached
        use_document = bool(request.document_id)

        if use_document:
            ddoc = await get_document(db, user_id=current_user.id, document_id=request.document_id)
            if not ddoc:
                raise HTTPException(status_code=404, detail="Document not found")

            doc_content = ddoc.get("content", "")
            doc_filename = ddoc.get("filename", "document")
            doc_metadata = ddoc.get("metadata", {})
            
            # Truncate if still too large for context
            if len(doc_content) > 50_000:
                doc_content = doc_content[:50_000] + "\n\n[Content truncated for context window...]"

            prompt = (
                f"You are given the contents of a document: {doc_filename}\n"
                f"Format: {doc_metadata.get('format', 'Unknown')}\n\n"
                "Answer the user's question using the document content below. "
                "Provide summaries, extract information, or answer questions based on the document. "
                "If the answer is not in the document, say so clearly.\n\n"
                f"Question: {request.message.strip()}\n\n"
                "Document Content:\n"
                f"{doc_content}\n\n"
                "Answer:"
            )

            response_text = generate_chat_response_with_history(
                history=history,
                user_message=prompt,
                conversation_id=conversation_id,
                system_prompt=(
                    "You are PanScience, a helpful conversational AI assistant. "
                    "When analyzing documents, provide clear summaries and accurate information. "
                    "Be concise, accurate, and friendly."
                ),
            )
        elif use_transcript:
            tdoc = await get_transcript(db, user_id=current_user.id, transcript_id=request.transcript_id)
            if not tdoc:
                raise HTTPException(status_code=404, detail="Transcript not found")

            context = _build_transcript_context(
                tdoc.get("segments") or [],
                start_time=request.start_time,
                end_time=request.end_time,
            )
            if not context:
                raise HTTPException(status_code=400, detail="No transcript content in the requested time range")

            st = request.start_time
            et = request.end_time
            window = ""
            if st is not None or et is not None:
                window = f" Time window: {st if st is not None else 0.0}s to {et if et is not None else 'end'}s."

            prompt = (
                "You are given a transcript from an audio/video recording with timestamps." + window + " "
                "Answer the user's question using ONLY the transcript content below. "
                "Do not mention any limitations about accessing media files; you already have the transcript. "
                "If the answer is not present in the transcript, say exactly: Not stated in the recording. "
                "When you make a factual claim, include at least one supporting timestamp range in brackets.\n\n"
                f"Question: {request.message.strip()}\n\n"
                "Transcript:\n"
                f"{context}\n\n"
                "Answer (with timestamps):"
            )

            response_text = generate_chat_response_with_history(
                history=history,
                user_message=prompt,
                conversation_id=conversation_id,
                system_prompt=(
                    "You are PanScience, a helpful conversational AI assistant. "
                    "If the user's message contains a Transcript section, you MUST use only that Transcript for facts "
                    "and ignore earlier conversation history for factual claims. "
                    "Be concise, accurate, and friendly."
                ),
            )
        else:
            response_text = generate_chat_response_with_history(
                history=history,
                user_message=request.message,
                conversation_id=conversation_id,
            )
    except RuntimeError as e:
        # Misconfiguration like missing GOOGLE_API_KEY
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Surface the error message to help local debugging (avoid hiding root cause).
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {e}")
    
    await append_message(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        sender="assistant",
        text=response_text,
    )

    # After the first AI response, make a second AI call to generate a proper title.
    # Do this in the background so /api/chat stays snappy.
    if created_new:
        asyncio.create_task(
            _generate_and_persist_title(
                db=db,
                user_id=current_user.id,
                conversation_id=conversation_id,
                first_user_message=request.message,
                first_assistant_message=response_text,
            )
        )

    return ChatResponse(
        message=response_text,
        timestamp=datetime.now(timezone.utc).isoformat(),
        conversation_id=conversation_id,
    )

@app.post("/api/conversations")
async def create_conversation(
    title: str = "New Conversation",
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Create a new conversation."""
    convo = await create_conversation_doc(db, user_id=current_user.id, title=title)
    return {"id": str(convo["_id"]), "title": convo["title"]}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Delete a conversation."""
    ok = await delete_conversation_doc(db, user_id=current_user.id, conversation_id=conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    reset_conversation(0)
    return {"message": "Conversation deleted successfully"}

@app.post("/api/upload")
async def upload_file(file: bytes):
    """Handle file uploads (documents, audio, video, etc.)"""
    # Placeholder for file upload logic
    return {
        "message": "File uploaded successfully",
        "filename": "uploaded_file",
        "size": len(file)
    }


def _seconds_to_hms(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _build_transcript_context(segments: list[dict], *, start_time: Optional[float], end_time: Optional[float]) -> str:
    st = float(start_time) if start_time is not None else 0.0
    et = float(end_time) if end_time is not None else float("inf")

    chosen: list[dict] = []
    for s in segments or []:
        try:
            a = float(s.get("start") or 0.0)
            b = float(s.get("end") or a)
            txt = str(s.get("text") or "").strip()
        except Exception:
            continue
        if not txt:
            continue
        if b >= st and a <= et:
            chosen.append({"start": a, "end": b, "text": txt})

    if not chosen:
        return ""

    lines = [f"[{_seconds_to_hms(s['start'])} - {_seconds_to_hms(s['end'])}] {s['text']}" for s in chosen]
    context = "\n".join(lines)
    # Keep prompts bounded.
    return context[:120_000]


@app.post("/api/media/transcribe", response_model=TranscribeResponse)
async def media_transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Transcribe an uploaded audio/video file with timestamps (Deepgram).

    Returns an id you can later use to ask timestamp-scoped questions.
    """
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    # Basic size guardrail (default 50MB). Adjust as needed.
    max_bytes = int((__import__("os").getenv("MAX_UPLOAD_BYTES") or "52428800").strip())
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (>{max_bytes} bytes)")

    try:
        dg = await transcribe_media_bytes(
            data=data,
            mimetype=file.content_type or "application/octet-stream",
            filename=file.filename,
            language=language,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to transcribe: {e}")

    doc = await create_transcript(
        db,
        user_id=current_user.id,
        filename=dg.get("filename"),
        mimetype=dg.get("mimetype"),
        duration=dg.get("duration"),
        segments=dg.get("segments") or [],
    )

    return TranscribeResponse(
        transcript_id=str(doc.get("_id")),
        filename=doc.get("filename"),
        mimetype=doc.get("mimetype"),
        duration=doc.get("duration"),
        segments=doc.get("segments") or [],
    )


@app.get("/api/media/transcripts")
async def media_list_transcripts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    docs = await list_transcripts(db, user_id=current_user.id, limit=25)
    return [
        {
            "id": str(d.get("_id")),
            "filename": d.get("filename"),
            "mimetype": d.get("mimetype"),
            "duration": d.get("duration"),
            "created_at": (d.get("created_at") or datetime.now(timezone.utc)).isoformat(),
        }
        for d in docs
    ]


@app.get("/api/media/transcripts/{transcript_id}")
async def media_get_transcript(
    transcript_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await get_transcript(db, user_id=current_user.id, transcript_id=transcript_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {
        "id": str(doc.get("_id")),
        "filename": doc.get("filename"),
        "mimetype": doc.get("mimetype"),
        "duration": doc.get("duration"),
        "segments": doc.get("segments") or [],
        "created_at": (doc.get("created_at") or datetime.now(timezone.utc)).isoformat(),
    }


class ParseDocumentResponse(BaseModel):
    document_id: str
    filename: Optional[str] = None
    mimetype: Optional[str] = None
    content_preview: str
    metadata: dict


@app.post("/api/documents/parse", response_model=ParseDocumentResponse)
async def parse_document(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Parse an uploaded document (PDF, Word, Excel, JSON, etc.)."""
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    # Size guardrail (default 50MB)
    max_bytes = int((__import__("os").getenv("MAX_UPLOAD_BYTES") or "52428800").strip())
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (>{max_bytes} bytes)")

    try:
        parsed = parse_document_bytes(
            data=data,
            mimetype=file.content_type or "application/octet-stream",
            filename=file.filename,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {e}")

    doc = await create_document(
        db,
        user_id=current_user.id,
        filename=parsed.get("filename"),
        mimetype=parsed.get("mimetype"),
        content=parsed.get("content"),
        metadata=parsed.get("metadata", {}),
    )

    # Return preview (first 500 chars)
    content = parsed.get("content", "")
    preview = content[:500] + ("..." if len(content) > 500 else "")

    return ParseDocumentResponse(
        document_id=str(doc.get("_id")),
        filename=doc.get("filename"),
        mimetype=doc.get("mimetype"),
        content_preview=preview,
        metadata=doc.get("metadata", {}),
    )


@app.get("/api/documents")
async def list_parsed_documents(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    docs = await list_documents(db, user_id=current_user.id, limit=25)
    return [
        {
            "id": str(d.get("_id")),
            "filename": d.get("filename"),
            "mimetype": d.get("mimetype"),
            "metadata": d.get("metadata", {}),
            "created_at": (d.get("created_at") or datetime.now(timezone.utc)).isoformat(),
        }
        for d in docs
    ]


@app.get("/api/documents/{document_id}")
async def get_parsed_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await get_document(db, user_id=current_user.id, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.get("_id")),
        "filename": doc.get("filename"),
        "mimetype": doc.get("mimetype"),
        "content": doc.get("content"),
        "metadata": doc.get("metadata", {}),
        "created_at": (doc.get("created_at") or datetime.now(timezone.utc)).isoformat(),
    }


@app.post("/api/media/answer", response_model=MediaAnswerResponse)
async def media_answer(
    request: MediaAnswerRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Answer a question strictly grounded in the transcript.

    Optional: provide start_time/end_time (seconds) to constrain what the model may use.
    """
    doc = await get_transcript(db, user_id=current_user.id, transcript_id=request.transcript_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Transcript not found")

    segments = doc.get("segments") or []
    start_t = request.start_time
    end_t = request.end_time
    if start_t is not None or end_t is not None:
        st = float(start_t or 0.0)
        et = float(end_t) if end_t is not None else float("inf")
        segments = [
            s
            for s in segments
            if float(s.get("end") or 0.0) >= st and float(s.get("start") or 0.0) <= et
        ]

    if not segments:
        raise HTTPException(status_code=400, detail="No transcript content in the requested time range")

    context_lines = []
    for s in segments:
        try:
            a = float(s.get("start") or 0.0)
            b = float(s.get("end") or a)
            txt = str(s.get("text") or "").strip()
        except Exception:
            continue
        if not txt:
            continue
        context_lines.append(f"[{_seconds_to_hms(a)} - {_seconds_to_hms(b)}] {txt}")

    context = "\n".join(context_lines)
    if len(context) > 120_000:
        # Keep prompts bounded; if you need more, we can chunk + retrieve.
        context = context[:120_000]

    prompt = (
        "You are given a transcript from an audio/video recording with timestamps. "
        "Answer the user's question using ONLY the transcript content below. "
        "If the answer is not present in the transcript, say: 'Not stated in the recording.' "
        "When you make a factual claim, include at least one supporting timestamp range in brackets.\n\n"
        f"Question: {request.question.strip()}\n\n"
        "Transcript:\n"
        f"{context}\n\n"
        "Answer (with timestamps):"
    )

    try:
        answer = generate_chat_response(prompt, conversation_id=0)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {e}")

    return MediaAnswerResponse(answer=answer)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
