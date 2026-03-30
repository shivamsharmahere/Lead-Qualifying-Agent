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
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if email_match:
        extracted["email"] = email_match.group(0)

    # Simple regex for finding Indian Lakh/Crore budgets
    budget_match = re.search(
        r"(?:rs\.?|inr|budget)?\s*(\d+(?:\.\d+)?)\s*(lakhs?|l|cr|crores?)",
        text,
        re.IGNORECASE,
    )
    if budget_match:
        val = float(budget_match.group(1))
        unit = budget_match.group(2).lower()
        if "l" in unit:
            extracted["budget"] = val * 100_000
        elif "c" in unit:
            extracted["budget"] = val * 10_000_000

    # Simple regex for timeline
    timeline_match = re.search(r"(\d+)\s*(months?|weeks?|years?)", text, re.IGNORECASE)
    if timeline_match:
        val = int(timeline_match.group(1))
        unit = timeline_match.group(2).lower()
        if "week" in unit:
            extracted["timeline_months"] = max(1, val // 4)
        elif "year" in unit:
            extracted["timeline_months"] = val * 12
        else:
            extracted["timeline_months"] = val

    return extracted


def clean_reply_text(text: str) -> str:
    """Clean up any extra formatting from the reply text."""
    # Remove trailing \n> or > characters
    text = re.sub(r"\n+>", "\n", text)
    text = re.sub(r"\n+$", "", text)
    text = re.sub(r">+$", "", text)

    # Remove any remaining LEAD_DATA artifacts that might have been missed
    text = re.sub(r"<!--\s*LEAD_DATA:.*?-->", "", text, flags=re.DOTALL)

    # Clean up multiple newlines to single newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def extract_lead_data_from_reply(reply: str) -> Tuple[Dict[str, Any], str]:
    """
    Parses the hidden JSON block from the LLM's reply.
    Returns a tuple: (Extracted Dictionary, Cleaned Reply string to show user)
    """
    cleaned_reply = reply
    extracted_data = {}

    # Find <!-- LEAD_DATA: ... --> block with proper nested JSON handling
    start_marker = "<!-- LEAD_DATA:"
    end_marker = "-->"

    start_idx = reply.find(start_marker)
    if start_idx != -1:
        # Find the opening brace after LEAD_DATA:
        json_start = reply.find("{", start_idx)
        if json_start != -1:
            # Count braces to find matching closing brace
            brace_count = 0
            json_end = json_start
            for i in range(json_start, len(reply)):
                if reply[i] == "{":
                    brace_count += 1
                elif reply[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if brace_count == 0:
                json_str = reply[json_start:json_end]
                full_block = reply[start_idx : json_end + len(end_marker)]
                try:
                    extracted_data = json.loads(json_str)
                    cleaned_reply = reply.replace(full_block, "").strip()
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode LEAD_DATA JSON: {e}")
                    extracted_data = parse_regex_fallback(reply)
    else:
        # Fallback if AI forgot to add the block
        extracted_data = parse_regex_fallback(reply)

    # Clean up the reply text
    cleaned_reply = clean_reply_text(cleaned_reply)

    return extracted_data, cleaned_reply
