from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services.message import get_session_history
from app.services.extraction import extract_lead_data_from_reply

router = APIRouter(prefix="/reply", tags=["Reply"])

@router.get("/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Returns the complete ordered message history for a given session."""
    history = await get_session_history(db, session_id)
    
    clean_history = []
    for turn in history:
        if turn["role"] == "assistant":
            _, cleaned = extract_lead_data_from_reply(turn["content"])
            clean_history.append({"role": turn["role"], "content": cleaned})
        else:
            clean_history.append(turn)
            
    return {"session_id": session_id, "messages": clean_history}
