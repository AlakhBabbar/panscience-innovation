import os
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv

# Keep env loading local to the service so main.py stays clean.
# Resolve the dotenv path relative to the backend folder so it works
# regardless of the current working directory.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH)

_llm: Optional["ChatGoogleGenerativeAI"] = None


def _get_llm():
    """Create (and cache) a Gemini chat model.

    This service is intentionally stateless (no memory/history) to keep
    dependencies minimal and make local testing easy.
    """
    global _llm
    if _llm is not None:
        return _llm

    api_key = (os.getenv("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY in environment (.env)")

    # Import lazily so the backend can still start and show a clear error
    # if dependencies are missing.
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Default to a non-advanced, cost-effective Gemini 1.5 model.
    # You can override with GEMINI_MODEL in .env.
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    _llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
        convert_system_message_to_human=True,
    )
    return _llm


def generate_chat_response(message: str, conversation_id) -> str:
    """Generate a single-turn reply.

    `conversation_id` is accepted for API compatibility but ignored.
    """
    return generate_chat_response_with_history(
        history=(),
        user_message=message,
        conversation_id=conversation_id,
    )


def generate_chat_response_with_history(
    *,
    history: Sequence[dict] | Sequence[tuple[str, str]],
    user_message: str,
    conversation_id,
    system_prompt: str | None = None,
    max_history_messages: int = 40,
) -> str:
    """Generate a reply using recent conversation history.

    History items can be either:
    - dicts with keys: {"sender": "user"|"assistant", "text": "..."}
    - tuples: (sender, text)

    `conversation_id` is accepted for API compatibility but ignored.
    """
    if not user_message or not str(user_message).strip():
        return ""

    llm = _get_llm()
    system_prompt = system_prompt or (
        "You are PanScience, a helpful conversational AI assistant. "
        "Be concise, accurate, and friendly."
    )

    # Prefer langchain-core message objects when available.
    try:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        msgs: list = [SystemMessage(content=system_prompt)]

        trimmed_history = list(history)[-max_history_messages:] if history else []
        for item in trimmed_history:
            if isinstance(item, dict):
                sender = str(item.get("sender") or "").strip().lower()
                text = str(item.get("text") or "")
            else:
                sender = str(item[0] or "").strip().lower()  # type: ignore[index]
                text = str(item[1] or "")  # type: ignore[index]

            if not text.strip():
                continue
            if sender == "assistant":
                msgs.append(AIMessage(content=text))
            else:
                # Default to user when unknown.
                msgs.append(HumanMessage(content=text))

        msgs.append(HumanMessage(content=str(user_message)))

        result = llm.invoke(msgs)
        content = getattr(result, "content", None)
        return (content if isinstance(content, str) else str(result)).strip()
    except Exception:
        # Backwards compatibility across langchain versions.
        # Fallback: inline a simple transcript of recent turns.
        lines: list[str] = [system_prompt, ""]
        trimmed_history = list(history)[-max_history_messages:] if history else []
        for item in trimmed_history:
            if isinstance(item, dict):
                sender = str(item.get("sender") or "user").strip().lower()
                text = str(item.get("text") or "")
            else:
                sender = str(item[0] or "user").strip().lower()  # type: ignore[index]
                text = str(item[1] or "")  # type: ignore[index]
            if not text.strip():
                continue
            role = "Assistant" if sender == "assistant" else "User"
            lines.append(f"{role}: {text}")

        lines.append(f"User: {str(user_message).strip()}")
        prompt = "\n".join(lines).strip()

        if hasattr(llm, "predict"):
            return str(llm.predict(prompt)).strip()
        return str(llm.invoke(prompt)).strip()


def generate_chat_title(first_user_message: str, first_assistant_message: str) -> str:
    """Generate a short conversation title from the first Q/A pair."""
    llm = _get_llm()

    user_text = (first_user_message or "").strip()
    assistant_text = (first_assistant_message or "").strip()
    if not user_text and not assistant_text:
        return "New Chat"

    prompt = (
        "Write a short, helpful chat title based on the user's first message and the assistant's first reply. "
        "Rules: 3-8 words, Title Case, no quotes, no emojis, no trailing punctuation. "
        "Return ONLY the title text.\n\n"
        f"User: {user_text}\n"
        f"Assistant: {assistant_text}\n"
        "Title:"
    )

    try:
        from langchain_core.messages import HumanMessage

        result = llm.invoke([HumanMessage(content=prompt)])
        title = getattr(result, "content", None)
        title_text = title if isinstance(title, str) else str(result)
    except Exception:
        if hasattr(llm, "predict"):
            title_text = str(llm.predict(prompt))
        else:
            title_text = str(llm.invoke(prompt))

    cleaned = title_text.strip().strip('"').strip("'")
    cleaned = cleaned.replace("\r", " ").replace("\n", " ").strip()

    if not cleaned:
        return "New Chat"
    # Clamp title length for UI.
    return cleaned[:80]


def reset_conversation(conversation_id) -> None:
    """No-op: history is not persisted."""
    return None
