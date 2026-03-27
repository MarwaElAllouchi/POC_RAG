# tests/test_filter_events.py
import pytest
from LangChain.filter_events import filter_cultural_events
from datetime import datetime, timezone, timedelta

# 🔹 Exemple d'événements bien formés pour tests
EVENTS_FIXTURE = [
    {
        "uid": "1",
        "title": "Concert de Jazz",
        "description": "Super concert avec musique live incroyable pour tous les âges",
        "location": {
            "city": "Paris",
            "name": "Salle XYZ",
            "address": "1 rue de la Musique"
        },
        "nextTiming": {
            "begin": "2026-03-01T20:00:00Z",
            "end": "2026-03-01T22:00:00Z"
        },
        "keywords": ["musique", "concert"]
    },
    {
        "uid": "2",
        "title": "Exposition Moderne",
        "description": "Exposition immersive d'art contemporain gratuite",
        "location": {
            "city": "Paris",
            "name": "Galerie ABC",
            "address": "12 avenue des Arts"
        },
        "nextTiming": {
            "begin": "2026-03-05T10:00:00Z",
            "end": "2026-03-05T18:00:00Z"
        },
        "keywords": ["exposition", "art"]
    },
    {
        "uid": "3",
        "title": "Atelier Peinture",
        "description": "Atelier créatif pour enfants et adultes",
        "location": {
            "city": "Versailles",
            "name": "Maison de la Culture",
            "address": "5 rue des Peintres"
        },
        "nextTiming": {
            "begin": "2026-03-10T14:00:00Z",
            "end": "2026-03-10T17:00:00Z"
        },
        "keywords": ["atelier", "peinture"]
    },
]

# 🔹 Test filtrage par ville
def test_filter_by_city():
    filtered_paris = filter_cultural_events(EVENTS_FIXTURE, city="Paris")
    assert len(filtered_paris) == 2
    for e in filtered_paris:
        assert "Paris" in e["city"]

# 🔹 Test suppression des doublons
def test_remove_duplicates():
    duplicated_events = EVENTS_FIXTURE + [EVENTS_FIXTURE[0]]  # ajouter doublon
    filtered = filter_cultural_events(duplicated_events)
    uids = [e["uid"] for e in filtered]
    assert len(uids) == len(set(uids))  # pas de doublons

# 🔹 Test description minimale
def test_min_description_len():
    short_desc_event = {
        "uid": "4",
        "title": "Mini Concert",
        "description": "Trop court",
        "location": {
            "city": "Paris",
            "name": "Salle Petit"
        },
        "nextTiming": {
            "begin": "2026-03-15T18:00:00Z",
            "end": "2026-03-15T20:00:00Z"
        },
        "keywords": ["musique"]
    }
    events = EVENTS_FIXTURE + [short_desc_event]
    filtered = filter_cultural_events(events, min_description_len=20)
    # Le nouvel événement doit être exclu
    uids = [e["uid"] for e in filtered]
    assert "4" not in uids