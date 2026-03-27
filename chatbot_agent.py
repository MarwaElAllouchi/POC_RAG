import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from LangChain.mistral_tool import generate_mistral_response
from LangChain.vectorize_events import get_vectorstore
from LangChain.date_utils import get_target_dates, detect_intent

load_dotenv()

VECTORS_FILE = "LangChain/BD/events_vectors_chunks.npz"
DATE_REF = datetime.now()

# -----------------------------
# Logger sécurisé UTF-8
# -----------------------------
logger = logging.getLogger("chatbot_agent")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Fichier log UTF-8 complet
    fh = logging.FileHandler("chatbot.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(fh)

    # Console safe ASCII (supprime caractères non compatibles)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    class ConsoleFilter(logging.Filter):
        def filter(self, record):
            if isinstance(record.msg, str):
                record.msg = record.msg.encode("ascii", errors="ignore").decode()
            return True
    ch.addFilter(ConsoleFilter())
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(ch)

def get_chatbot_response(user_input,vectorstore):
    """
    Recherche dans le vectorstore, construit le contexte, et génère la réponse via Mistral.
    Retourne: response_text, predicted_uids
    """
   

    raw_docs = vectorstore.similarity_search(user_input, k=10)
    target_date = get_target_dates(user_input, DATE_REF)

    # Filtrage par date
    valid_docs = []
    for d in raw_docs:
        start_val = d.metadata.get("start", "")
        event_date = str(start_val)[:10]

        if target_date:
            if event_date == target_date:
                valid_docs.append(d)
        else:
            if event_date >= DATE_REF.strftime("%Y-%m-%d"):
                valid_docs.append(d)

    valid_docs.sort(key=lambda x: str(x.metadata.get("start", "")))

    # 🔹 EXTRACTION DES UID
    predicted_uids = []
    for d in valid_docs[:5]:
        uid = d.metadata.get("uid")
        if uid is not None:
            predicted_uids.append(uid)

    # Construction du contexte pour Mistral
    if not valid_docs:
        context_str = f"Aucun événement trouvé après le {DATE_REF.strftime('%Y-%m-%d')}."
    else:
        context_str = ""
        for i, d in enumerate(valid_docs[:3]):
            m = d.metadata
            context_str += (
                f"Event {i+1}: {m.get('title')} à {m.get('city')} "
                f"le {m.get('start')} au lieu {m.get('location')}. "
                f"Description: {m.get('description')}\n\n"
            )

    #logger.info(f"📊 Documents valides pour cette requête : {len(valid_docs)}")

    response_text = generate_mistral_response(context_str, user_input)

    # 🔹 retourner texte + uids
    return response_text, predicted_uids

# -----------------------------
# Main chatbot
# -----------------------------
def run_chatbot():
    logger.info("🚀 Démarrage du chatbot...")
    start_init = time.time()

    vectorstore = get_vectorstore()
    if not vectorstore:
        logger.error("❌ Vectorstore non chargé. Arrêt du programme.")
        return

    #logger.info(f"⏱️ Temps de chargement vectorstore : {time.time() - start_init:.2f}s")
    print("💬 Bonjour ! Je suis ton assistant culturel pour les événements en Île-de-France.")
    print("💬 Dis-moi ce que tu cherches? 😊")
    print("💬 Tape 'exit' pour quitter.\n")

    while True:
        try:
            user_input = input("\nVous : ")
            if user_input.lower() in ["exit", "quit"]:
                logger.info("👋 Arrêt du chatbot.")
                print("Assistant : Au revoir 👋")
                break

            start_query = time.time()
            intent = detect_intent(user_input)

            # -----------------------------
            # Gestion des intentions simples (salutation, remerciement)
            # -----------------------------
            if intent == "salutation":
                print("Assistant : Bonjour ! Comment puis-je vous aider ?")
                logger.info(f"Intent salutation détectée : {user_input}")
                continue
            elif intent == "remerciement":
                print("Assistant : Avec plaisir !")
                logger.info(f"Intent remerciement détectée : {user_input}")
                continue

            # -----------------------------
            # Intent RAG
            # -----------------------------
            # RAG via la fonction centralisée
     
            response, predicted_uids = get_chatbot_response(user_input,vectorstore)
     
            print(f"\nAssistant : {response}")

            # Logging des stats par requête
            #logger.info(f"⏱️ Temps requête total : {time.time() - start_query:.2f}s")
           
            #logger.info(f"🔹 Intent détecté : {intent}")

        except Exception as e:
            logger.error(f"🔥 Erreur pendant l'exécution : {str(e)}")
            print("⚠️ Une erreur est survenue. Veuillez reformuler votre question.")

if __name__ == "__main__":
    run_chatbot()