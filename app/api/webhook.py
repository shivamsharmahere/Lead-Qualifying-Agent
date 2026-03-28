import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.message import WebhookPayload, WebhookResponse
from app.models.message import RoleEnum
from app.services.message import add_message, get_session_history, generate_message_hash, get_message_by_hash
from app.services.chat import generate_chat_reply
from app.services.extraction import extract_lead_data_from_reply
from app.services.lead import upsert_lead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook"])

@router.post("", response_model=WebhookResponse)
async def receive_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    # Auto-generate session_id if none is provided via the payload
    session_id = payload.session_id if payload.session_id else f"session_{uuid.uuid4().hex[:12]}"
    user_message = payload.message.strip()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    # Idempotency check before doing any LLM work
    msg_hash = generate_message_hash(session_id, user_message)
    existing_msg = await get_message_by_hash(db, session_id, msg_hash)
    
    if existing_msg:
        logger.info(f"Duplicate webhook received for session {session_id}")
        history = await get_session_history(db, session_id)
        last_reply = history[-1]['content'] if history and history[-1]['role'] == 'assistant' else ""
        extracted_data, cleaned_reply = extract_lead_data_from_reply(last_reply)
        return WebhookResponse(
            session_id=session_id,
            reply=cleaned_reply,
            lead_extracted=bool(extracted_data),
            lead_priority=None,  
            tokens_used=0,
            cached=True
        )

    # 1. Persist the new user message
    await add_message(db, session_id, RoleEnum.user, user_message)
    
    # 2. Get full session history
    history = await get_session_history(db, session_id)
    
    # 3. Call LLM
    try:
        raw_reply, tokens_used = await generate_chat_reply(history)
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}")
        raise HTTPException(status_code=503, detail="AI Service unavailable. Please try again later.")
        
    # 4. Extract data and clean reply
    extracted_data, cleaned_reply = extract_lead_data_from_reply(raw_reply)
    
    # 5. Persist assistant reply 
    await add_message(db, session_id, RoleEnum.assistant, raw_reply, tokens_used)
    
    # 6. Upsert Lead directly into the database (Day 3 feature)
    lead_priority = None
    if extracted_data:
        lead = await upsert_lead(db, session_id, extracted_data)
        lead_priority = lead.priority.value
    
    # 7. Response
    return WebhookResponse(
        session_id=session_id,
        reply=cleaned_reply,
        lead_extracted=bool(extracted_data),
        lead_priority=lead_priority,
        tokens_used=tokens_used,
        cached=False
    )


