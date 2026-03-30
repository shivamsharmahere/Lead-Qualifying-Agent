import asyncio
import logging
from typing import List
from langchain_groq import ChatGroq
from app.core.config import get_settings

settings = get_settings()
from app.agents.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Initialize LangChain Groq client
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.3,
    max_tokens=500
)


async def generate_chat_reply(messages: List[dict], retries: int = 3) -> str:
    """
    Calls the Groq LLM via LangChain with the structured conversation history.
    Includes an exponential backoff retry mechanism.

    messages format: [{"role": "user"/"assistant", "content": "..."}]
    """

    # Convert to LangChain message format
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in messages[-settings.MAX_CONTEXT_MESSAGES :]:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    for attempt in range(retries):
        try:
            response = await llm.ainvoke(langchain_messages)
            content = response.content
            return content

        except Exception as e:
            logger.warning(
                f"Groq API call failed (attempt {attempt + 1}/{retries}): {str(e)}"
            )
            if attempt == retries - 1:
                logger.error("All Groq API retries exhausted.")
                raise e
            await asyncio.sleep(2**attempt)

    raise RuntimeError("Failed to generate chat reply")
