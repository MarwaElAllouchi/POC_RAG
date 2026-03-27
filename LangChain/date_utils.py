
import dateparser
from dateparser.search import search_dates

def get_target_dates(query, ref_date_str):
    

    settings = {
        'PREFER_DATES_FROM': 'future',
        'DATE_ORDER': 'DMY',
        'RELATIVE_BASE': ref_date_str
    }

    # 1️⃣ Cherche une date explicite dans la phrase (25-02-2026, demain, lundi, etc.)
    results = search_dates(query, languages=['fr'], settings=settings)

    if results:
        date_obj = results[0][1]
        return date_obj.strftime("%Y-%m-%d")

    # 2️⃣ Sinon tentative avec parse simple (fallback)
    parsed = dateparser.parse(query, languages=['fr'], settings=settings)
    if parsed:
        return parsed.strftime("%Y-%m-%d")

    return None
def detect_intent(user_input: str) -> str:
    user_input = user_input.lower()
    salutations = ["bonjour", "salut", "coucou", "hey"]
    remerciements = ["merci", "thank you"]

    if any(word in user_input for word in salutations):
        return "salutation"
    if any(word in user_input for word in remerciements):
        return "remerciement"
    return "RAG"