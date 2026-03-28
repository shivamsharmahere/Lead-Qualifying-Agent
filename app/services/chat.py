import asyncio
import logging
from typing import List, Tuple
from groq import AsyncGroq
from app.config import settings
from app.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def generate_chat_reply(messages: List[dict], retries: int = 3) -> Tuple[str, int]:
    """
    Calls the Groq LLM with the structured conversation history.
    Includes an exponential backoff retry mechanism.
    
    messages format: [{"role": "user"/"assistant", "content": "..."}]
    """
    
    # Prepend the system prompt
    formatted_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    formatted_messages.extend(messages[-settings.MAX_CONTEXT_MESSAGES:])
    
    for attempt in range(retries):
        try:
            response = await groq_client.chat.completions.create(
                messages=formatted_messages,
                model=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return content, tokens_used
            
        except Exception as e:
            logger.warning(f"Groq API call failed (attempt {attempt + 1}/{retries}): {str(e)}")
            if attempt == retries - 1:
                logger.error("All Groq API retries exhausted.")
                raise e
            await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s...
    
    raise RuntimeError("Failed to generate chat reply")
