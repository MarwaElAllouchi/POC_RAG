# tests/test_pipeline.py

import os
import pytest
import json
from LangChain.fetch_events import fetch_openagenda_events
from LangChain.filter_events import filter_cultural_events
from LangChain.vectorize_events import build_event_chunks, create_faiss_index, get_vectorstore
from LangChain.mistral_tool import generate_mistral_response
from chatbot_agent import get_chatbot_response

# 🔹 Variables globales pour tests
AGENDA_UID = "56500817"
TOKEN = os.getenv("OPENAGENDA_API_KEY")
OUTPUT_JSON = "tests/test_events.json"


@pytest.mark.order(1)
def test_fetch_events():
    """Test récupération des événements depuis OpenAgenda."""
    events = fetch_openagenda_events(
        agenda_uid=AGENDA_UID,
        token=TOKEN,
        page_size=50,   # petite taille pour test rapide
        output_file=OUTPUT_JSON
    )
    assert isinstance(events, list)
    assert len(events) > 0
    assert os.path.exists(OUTPUT_JSON)


@pytest.mark.order(2)
def test_filter_events():
    """Test filtrage des événements culturels."""
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        events = json.load(f)
    filtered = filter_cultural_events(events, city="Paris", min_description_len=20)
    assert isinstance(filtered, list)
    for e in filtered:
        assert "uid" in e
        assert "title" in e
        assert "description" in e
        assert "city" in e
    # Vérifier qu'au moins un événement Paris a été conservé
    assert any(e["city"].lower() == "paris" for e in filtered)


@pytest.mark.order(3)
def test_chunking():
    """Test découpage en chunks sémantiques."""
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        events = json.load(f)
    filtered = filter_cultural_events(events, city="Paris", min_description_len=20)
    for e in filtered[:3]:  # test sur 3 événements
        chunks = build_event_chunks(e, max_chunk_size=500)
        assert isinstance(chunks, list)
        assert all(isinstance(c, str) for c in chunks)
        assert len(chunks) <= 2  # comme défini dans build_event_chunks


@pytest.mark.order(4)
def test_embeddings_and_faiss():
    """Test création des embeddings et index FAISS."""
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        events = json.load(f)
    filtered = filter_cultural_events(events, city="Paris", min_description_len=20)
    index, metadata = create_faiss_index(filtered, max_chunk_size=500)
    assert index.ntotal > 0
    assert isinstance(metadata, list)
    assert len(metadata) == index.ntotal


@pytest.mark.order(5)
def test_vectorstore_and_chatbot():
    """Test vectorstore et réponse chatbot."""
    vectorstore = get_vectorstore()
    assert vectorstore is not None

    question = "Quels événements de musique à Paris cette semaine ?"
    response_text, predicted_uids = get_chatbot_response(question, vectorstore)
    assert isinstance(response_text, str)
    assert isinstance(predicted_uids, list)


@pytest.mark.order(6)
def test_end_to_end_pipeline():
    """Test pipeline complet sur un petit dataset."""
    events = fetch_openagenda_events(
        agenda_uid=AGENDA_UID,
        token=TOKEN,
        page_size=10,
        output_file="tests/test_events_small.json"
    )
    filtered = filter_cultural_events(events, city="Paris")
    index, metadata = create_faiss_index(filtered)
    vectorstore = get_vectorstore()
    response_text, predicted_uids = get_chatbot_response("Spectacle à Paris cette semaine ?", vectorstore)
    assert isinstance(response_text, str)
    assert isinstance(predicted_uids, list)