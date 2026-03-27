from datetime import datetime
from LangChain.date_utils import get_target_dates, detect_intent

REF_DATE = datetime(2026, 2, 24)

def test_detect_intent_salutation():
    assert detect_intent("bonjour") == "salutation"
    assert detect_intent("salut") == "salutation"

def test_detect_intent_remerciement():
    assert detect_intent("merci beaucoup") == "remerciement"

def test_detect_intent_rag():
    assert detect_intent("événements à paris") == "RAG"

def test_get_target_dates_explicit():
    result = get_target_dates("événement le 25-02-2026", REF_DATE)
    assert result == "2026-02-25"

def test_get_target_dates_relative():
    result = get_target_dates("demain", REF_DATE)
    assert result == "2026-02-25"

def test_get_target_dates_none():
    result = get_target_dates("événements à paris", REF_DATE)
    assert result is None