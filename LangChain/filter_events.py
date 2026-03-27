from datetime import datetime, timezone, timedelta
import json
import re
import logging

# 🔹 Logger configuré pour UTF-8
logger = logging.getLogger("filter_events")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def filter_cultural_events(events: list, city: str = None, min_description_len: int = 20) -> list:
    """
    Filtre les événements pour préparation à un pipeline RAG.
    Ajoute : statistiques et logging sécurisé.
    """

    filtered_events = []
    seen_uids = set()
    today = datetime.now(timezone.utc)
    one_year_ago = today - timedelta(days=365)

    # Stats pour contrôle 
    stats = {
        "total": len(events),
        "no_uid": 0,
        "duplicates": 0,
        "trop_ancien":0,
        "short_description": 0,
        "bad_chars": 0,
        "no_city": 0,
        "wrong_city": 0,
        "invalid_dates": 0,
        "start_after_end": 0,
        "no_location": 0,
        "kept": 0
    }

    allowed_pattern = re.compile(r'^[\w\s\'\-À-ÖØ-öø-ÿ\.\,\!\?\(\)\:\;\/\"\@\d]+$')

    for event in events:
        uid = event.get("uid")
        title = event.get("title", "Sans titre")

        if not uid:
            stats["no_uid"] += 1
            logger.info(f"🔹 Ignoré (pas d'uid) : {title}")
            continue
        if uid in seen_uids:
            stats["duplicates"] += 1
            logger.info(f"🔹 Ignoré (doublon) : {title}")
            continue
        seen_uids.add(uid)

        description = event.get("description", "")
        if not description or len(description) < min_description_len:
            stats["short_description"] += 1
            logger.info(f"🔹 Ignoré (description trop courte) : {title}")
            continue

        if not allowed_pattern.match(title) or not allowed_pattern.match(description):
            stats["bad_chars"] += 1
            logger.info(f"🔹 Ignoré (caractères spéciaux) : {title}")
            continue

        event_city = event.get("location", {}).get("city", "")
        if not event_city:
            stats["no_city"] += 1
            logger.info(f"🔹 Ignoré (pas de ville) : {title}")
            continue
        if city and city.lower() not in event_city.lower():
            stats["wrong_city"] += 1
            logger.info(f"🔹 Ignoré (ville non correspondante) : {title} - {event_city}")
            continue

        start_str = None
        end_str = None
 
        try:
            # 🔹 1. Priorité : nextTiming (événements futurs ou récurrents)
            next_timing = event.get("nextTiming")
            if next_timing and isinstance(next_timing, dict):
                start_str = next_timing.get("begin")
                end_str = next_timing.get("end")

            # 🔹 2. Sinon : lastTiming (dernière occurrence pour filtrage historique)
            if not start_str:
                last_timing = event.get("lastTiming")
                if last_timing and isinstance(last_timing, dict):
                    start_str = last_timing.get("begin")
                    end_str = last_timing.get("end")

            # 🔹 3. Sinon : firstTiming (événement unique ou premier timing connu)
            if not start_str:
                first_timing = event.get("firstTiming")
                if first_timing and isinstance(first_timing, dict):
                    start_str = first_timing.get("begin")
                    end_str = first_timing.get("end")

            # 🔹 Conversion en datetime
            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else None
            end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None

            # 🔹 FILTRE 1 AN D'HISTORIQUE
            if end_time and end_time < one_year_ago:
                stats["trop_ancien"] += 1
                logger.info(f"🔹 Ignoré ( > 1 an historique) : {title}")
                continue

            # 🔹 Vérification start <= end
            if start_time and end_time and start_time > end_time:
                stats["start_after_end"] += 1
                logger.info(f"🔹 Ignoré (start > end) : {title}")
                continue

        except Exception as e:
            stats["invalid_dates"] += 1
            logger.info(f"🔹 Ignoré (erreur date) : {title} - {e}")
            continue

        if not start_time or not end_time:
            stats["invalid_dates"] += 1
            logger.info(f"🔹 Ignoré (dates manquantes) : {title}")
            continue

        location_name = event.get("location", {}).get("name", "")
        if not location_name:
            stats["no_location"] += 1
            logger.info(f"🔹 Ignoré (pas de lieu) : {title}")
            continue

        keywords = event.get("keywords") or []

        filtered_events.append({
            "uid": uid,
            "title": title,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "description": description,
            "city": event_city,
            "location": location_name,
            "address": event.get("location", {}).get("address", ""),
            "keywords": keywords
        })
        stats["kept"] += 1



    # 🔹 Logs statistiques finales
    logger.info(f"✅ Filtrage terminé : {stats['kept']} événements conservés sur {stats['total']}")
    logger.info(f"📊 Détails des filtrages : {stats}")

    return filtered_events