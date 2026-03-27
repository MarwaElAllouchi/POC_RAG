# fetch_events.py
import requests
import json
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)


def fetch_openagenda_events(
    agenda_uid: str,
    token: str,
    page_size: int ,
    output_file: str
) -> list:
    """
    Récupère tous les événements d'un agenda OpenAgenda et les sauvegarde en JSON.
    """

    # Plage de date : 1 an d'historique
    today = datetime.utcnow()
    one_year_ago = today - timedelta(days=365)
    timings_gte = one_year_ago.isoformat() + "Z"

    url = f"https://api.openagenda.com/v2/agendas/{agenda_uid}/events"

    # ----------------------------
    # PARAMÈTRES DE BASE
    # ----------------------------
    params = {
        "relative[]": ["passed", "current", "upcoming"],  # Passé, en cours, futur
        "size": page_size,                                      # max par appel
        "monolingual": "fr",                              # texte en français
        "timings[gte]": timings_gte                       # 1 an d'historique
    }

    headers = {"Authorization": f"Bearer {token}"}

    all_events = []
    after = None

    # ----------------------------
    # FILTRER LES CATÉGORIES CULTURELLES
    # ----------------------------
    culture_keywords = [
        "musique",
        "exposition",
        "théâtre",
        "danse",
        "cinéma",
        "visite",
        "atelier",
        "performance",
        "festival",
        "spectacle"
    ]

    # Pour tester, on peut d'abord récupérer tous les événements sans keyword
    # puis filtrer ensuite en Python pour être sûr
    apply_filter_in_python = True

    while True:
        if after:
            params["after[]"] = after

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        events = data.get("events", [])

        # ----------------------------
        # FILTRAGE CULTUREL EN PYTHON
        # ----------------------------
        if apply_filter_in_python:
            filtered = []
            for event in events:
                title = event.get("title", "").lower()
                long_desc = event.get("longDescription", "").lower() if event.get("longDescription") else ""
                # Si l'un des mots-clés culturels apparaît dans le titre ou description
                if any(keyword in title or keyword in long_desc for keyword in culture_keywords):
                    filtered.append(event)
            events = filtered

        all_events.extend(events)

      
        logger.info(f"Page récupérée : {len(events)} événements (Total cumulé : {len(all_events)})")

        after = data.get("after")
        if after is None:
            break

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ Export terminé : {output_file} ({len(all_events)} événements)")

    return all_events
