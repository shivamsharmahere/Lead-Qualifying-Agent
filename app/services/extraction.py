import re
import re
import json
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def parse_regex_fallback(text: str) -> Dict[str, Any]:
    """Fallback parser if JSON extraction fails or is missing."""
    extracted = {}
    
    # Email extraction
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    if email_match:
        extracted['email'] = email_match.group(0)

    # Simple regex for finding Indian Lakh/Crore budgets
    budget_match = re.search(r'(?:rs\.?|inr|budget)?\s*(\d+(?:\.\d+)?)\s*(lakhs?|l|cr|crores?)', text, re.IGNORECASE)
    if budget_match:
        val = float(budget_match.group(1))
        unit = budget_match.group(2).lower()
        if 'l' in unit:
            extracted['budget'] = val * 100_000
        elif 'c' in unit:
            extracted['budget'] = val * 10_000_000

    # Simple regex for timeline
    timeline_match = re.search(r'(\d+)\s*(months?|weeks?|years?)', text, re.IGNORECASE)
    if timeline_match:
        val = int(timeline_match.group(1))
        unit = timeline_match.group(2).lower()
        if 'week' in unit:
            extracted['timeline_months'] = max(1, val // 4)
        elif 'year' in unit:
            extracted['timeline_months'] = val * 12
        else:
            extracted['timeline_months'] = val
            
    return extracted

def extract_lead_data_from_reply(reply: str) -> Tuple[Dict[str, Any], str]:
    """
    Parses the hidden JSON block from the LLM's reply.
    Returns a tuple: (Extracted Dictionary, Cleaned Reply string to show user)
    """
    cleaned_reply = reply
    extracted_data = {}
    
    # Regex to find <!-- LEAD_DATA: {...} -->
    pattern = r'<!--\s*LEAD_DATA:\s*(\{.*?\})\s*-->'
    match = re.search(pattern, reply, re.DOTALL)
    
    if match:
        try:
            json_str = match.group(1)
            extracted_data = json.loads(json_str)
            # Remove the hidden block from the reply text so the end user doesn't see it
            cleaned_reply = re.sub(pattern, '', reply).strip()
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode LEAD_DATA JSON: {e}")
            extracted_data = parse_regex_fallback(reply) # Fallback
    else:
        # Fallback if AI forgot to add the block
        extracted_data = parse_regex_fallback(reply)
            
    return extracted_data, cleaned_reply

