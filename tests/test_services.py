import pytest
from app.services.scoring import score_lead
from app.models.lead import PriorityEnum
from app.services.extraction import parse_regex_fallback, extract_lead_data_from_reply

def test_score_lead():
    # HIGH tests
    assert score_lead(8000000, 2) == PriorityEnum.high
    assert score_lead(10000000, 12) == PriorityEnum.high
    
    # MEDIUM tests
    assert score_lead(3500000, 5) == PriorityEnum.medium
    assert score_lead(8000000, 6) == PriorityEnum.medium
    
    # LOW tests
    assert score_lead(2000000, 2) == PriorityEnum.low
    assert score_lead(4000000, 8) == PriorityEnum.low
    
    # PENDING tests
    assert score_lead(None, None) == PriorityEnum.pending

def test_regex_fallback():
    extracted = parse_regex_fallback("I want a house for 85 lakhs and want to move in 2 months.")
    assert extracted.get("budget") == 8500000.0
    assert extracted.get("timeline_months") == 2
    
def test_json_extraction():
    text = 'Here are options.\n<!-- LEAD_DATA: {"name": "Priya", "budget": 8000000} -->'
    data, clean = extract_lead_data_from_reply(text)
    assert data["name"] == "Priya"
    assert "<!--" not in clean
