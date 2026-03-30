import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from cachetools import TTLCache

from app.schemas.message import WebhookPayload, WebhookResponse
from app.models.message import RoleEnum
from app.services.message import (
    add_message,
    generate_message_hash,
    get_message_by_hash,
    HISTORY_CACHE,
)
from app.services.chat import generate_chat_reply
from app.services.extraction import extract_lead_data_from_reply
from app.services.lead import upsert_lead
from app.core.db import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter()

idempotency_cache = TTLCache(maxsize=1000, ttl=60)


async def process_webhook_background(
    session_id: str,
    user_message: str,
    raw_reply: str,
    extracted_data: dict,
    msg_hash: str,
):
    """Background task to fully persist the state to DB without blocking the user response."""
    async with AsyncSessionLocal() as db:
        try:
            # Idempotency check
            existing_msg = await get_message_by_hash(db, session_id, msg_hash)
            if existing_msg:
                # Duplicate detected in background, skip writing
                return

            # persist the new user message
            await add_message(db, session_id, RoleEnum.user, user_message)

            # persist assistant reply
            await add_message(db, session_id, RoleEnum.assistant, raw_reply)

            # Upsert Lead if extracted
            if extracted_data:
                await upsert_lead(db, session_id, extracted_data)
        except Exception as e:
            logger.error(f"Error in background DB task for session {session_id}: {e}")


@router.post(
    "",
    response_model=WebhookResponse,
    summary="Send a chat message",
    description="""Send a message to the AI chatbot and get a response.""",
)
async def receive_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    # Notice we removed Depends(get_db) from the main injection!
    # This prevents FastAPI from acquiring a DB connection before the LLM runs.
    session_id = (
        payload.session_id if payload.session_id else f"session_{uuid.uuid4().hex[:12]}"
    )
    user_message = payload.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    msg_hash = generate_message_hash(session_id, user_message)
    if msg_hash in idempotency_cache:
        return idempotency_cache[msg_hash]

    # Quick history retrieval from memory cache only! No DB lookup on the critical path.
    # If cache miss (server restart), we start a fresh context array.
    history = list(HISTORY_CACHE.get(session_id, []))

    # Pre-append user message simulating the synchronous add_message
    history.append({"role": RoleEnum.user.value, "content": user_message})

    # Hit the LLM DIRECTLY! No DB wait whatsoever.
    try:
        raw_reply = await generate_chat_reply(history)
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}")
        raise HTTPException(status_code=503, detail="AI Service unavailable.")

    # Extract Data purely in python memory
    extracted_data, cleaned_reply = extract_lead_data_from_reply(raw_reply)

    # Offload ALL DB writes AND reads to the background
    background_tasks.add_task(
        process_webhook_background,
        session_id=session_id,
        user_message=user_message,
        raw_reply=raw_reply,
        extracted_data=extracted_data,
        msg_hash=msg_hash,
    )

    # Update the cache so the NEXT immediate question knows what was said
    if session_id not in HISTORY_CACHE:
        HISTORY_CACHE[session_id] = []

    if (
        len(HISTORY_CACHE[session_id]) == 0
        or HISTORY_CACHE[session_id][-1].get("role") != "user"
    ):
        HISTORY_CACHE[session_id].append({"role": "user", "content": user_message})
    HISTORY_CACHE[session_id].append({"role": "assistant", "content": raw_reply})

    response = WebhookResponse(
        session_id=session_id,
        reply=cleaned_reply,
        lead_extracted=bool(extracted_data),
        lead_priority="pending" if extracted_data else None,
    )

    idempotency_cache[msg_hash] = response
    return response
