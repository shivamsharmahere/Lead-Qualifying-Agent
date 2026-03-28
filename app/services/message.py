import hashlib
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from app.models.message import Message, RoleEnum
import logging

logger = logging.getLogger(__name__)

def generate_message_hash(session_id: str, content: str) -> str:
    """Generate SHA-256 hash for message deduplication"""
    raw_str = f"{session_id}:{content}".encode('utf-8')
    return hashlib.sha256(raw_str).hexdigest()

async def get_message_by_hash(db: AsyncSession, session_id: str, message_hash: str) -> Optional[Message]:
    """Check if a message with this hash already exists for the session."""
    query = select(Message).where(
        Message.session_id == session_id,
        Message.message_hash == message_hash
    )
    result = await db.execute(query)
    return result.scalars().first()

async def add_message(db: AsyncSession, session_id: str, role: RoleEnum, content: str, tokens_used: int = None) -> Message:
    """Save a message to the DB if it doesn't already exist (idempotency check)"""
    msg_hash = generate_message_hash(session_id, content)
    
    # Check if duplicate
    existing_msg = await get_message_by_hash(db, session_id, msg_hash)
    if existing_msg:
        logger.info(f"Duplicate message suppressed for session {session_id}")
        return existing_msg
        
    db_message = Message(
        session_id=session_id,
        role=role,
        content=content,
        message_hash=msg_hash,
        tokens_used=tokens_used
    )
    
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_session_history(db: AsyncSession, session_id: str) -> List[dict]:
    """Retrieve full chronological conversation history for a session, formatted for the LLM"""
    query = select(Message).where(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc())
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    history = []
    for msg in messages:
        history.append({
            "role": msg.role.value,
            "content": msg.content
        })
    return history

