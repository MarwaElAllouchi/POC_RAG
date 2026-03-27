import os
import faiss
import numpy as np
from typing import List, Dict
from mistralai import Mistral
from dotenv import load_dotenv
import time
import logging

from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()

# ----------------------------- 
# Logger UTF-8
# -----------------------------
logger = logging.getLogger("vectorize_events")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# -----------------------------
# Configuration
# -----------------------------
FAISS_INDEX_FILE = "LangChain/BD/events_index.faiss"
VECTORS_FILE = "LangChain/BD/events_vectors_chunks.npz"
EMBEDDING_MODEL = "mistral-embed"

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

# -----------------------------
# Chunking sémantique
# -----------------------------
def semantic_chunk_text(text: str, max_chunk_size: int = 500) -> List[str]:
    """Découpe le texte en respectant la ponctuation."""
    if not text:
        return []

    sentences = text.split(". ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def build_event_chunks(event: Dict, max_chunk_size: int = 500) -> List[str]:
    """Construit un texte riche avant de le découper en max 2 chunks."""
    title = event.get("title", "")
    description = event.get("description", "")
    keywords = ", ".join(event.get("keywords", [])) if isinstance(event.get("keywords"), list) else ""
    city = event.get("city", "")
    location = event.get("location", "")
    address = event.get("address", "")
    start = event.get("start", "")
    end = event.get("end", "")

    # 🔹 Texte riche pour l'embedding (Titre + Lieu + Description)
    full_text = f"Titre: {title}. Lieu: {city} ({location}, {address}). Dates: du {start} au {end}. Mots-clés: {keywords}. Description: {description}."

    chunks = semantic_chunk_text(full_text.strip(), max_chunk_size=max_chunk_size)

    # 🔹 max 2 chunks par événement 
    return chunks[:2]


# -----------------------------
# Embeddings avec Retry Logic
# -----------------------------
def get_mistral_embeddings(chunks: List[str], batch_size: int = 16, max_retries: int = 3) -> np.ndarray:
    all_embeddings = []
    logger.info(f"🚀 Génération des embeddings pour {len(chunks)} chunks...")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]

        for attempt in range(max_retries):
            try:
                resp = client.embeddings.create(model=EMBEDDING_MODEL, inputs=batch)
                all_embeddings.extend([item.embedding for item in resp.data])
                break
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    wait_time = 15 * (attempt + 1)
                    logger.warning(f"⏳ Rate limit (429). Pause {wait_time}s avant essai {attempt+1}...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Erreur critique embeddings : {e}")
                    raise e

        time.sleep(0.5) # Petite pause entre les batches

    return np.array(all_embeddings, dtype="float32")


# -----------------------------
# Création et Sauvegarde FAISS
# -----------------------------
def create_faiss_index(events: List[Dict], max_chunk_size: int = 500):
    texts = []
    chunked_metadata = []

    for e in events:
        chunks = build_event_chunks(e, max_chunk_size)

        for chunk in chunks:
            texts.append(chunk)
            # 🔹 ON SAUVEGARDE LE TEXTE COMPLET DU CHUNK DANS LES METADATA
            meta = {
                "full_chunk_text": chunk, 
                "uid": e.get("uid"),
                "title": e.get("title"),
                "start": e.get("start"),
                "end": e.get("end"),
                "city": e.get("city"),
                "location": e.get("location"),
                "address": e.get("address"),
                "description": e.get("description")
            }
            chunked_metadata.append(meta)

    embeddings = get_mistral_embeddings(texts)

    # Création de l'index FAISS
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    if not os.path.exists("LangChain/BD"):
        os.makedirs("LangChain/BD")

    # Sauvegarde de l'index et des vecteurs/métadonnées
    faiss.write_index(index, FAISS_INDEX_FILE)
    np.savez(VECTORS_FILE, embeddings=embeddings, metadata=np.array(chunked_metadata, dtype=object))

    logger.info(f"💾 Index et Vecteurs sauvegardés ({len(texts)} chunks)")
    return index, chunked_metadata


# -----------------------------
# Chargement Vectorstore LangChain
# -----------------------------
def get_vectorstore():
    """Charge le vectorstore en synchronisant le texte avec les embeddings."""
    if not os.path.exists(VECTORS_FILE):
        logger.error("❌ Fichier de vecteurs introuvable.")
        return None

    data = np.load(VECTORS_FILE, allow_pickle=True)
    embeddings_array = data["embeddings"].astype("float32")
    metadata_list = data["metadata"].tolist()

    # 🔹 SYNCHRONISATION : On utilise le texte riche (full_chunk_text)
    documents = [
        Document(
            page_content=m.get("full_chunk_text", m.get("description", "")), 
            metadata=m
        ) for m in metadata_list
    ]

    embeddings_model = MistralAIEmbeddings(api_key=os.getenv("MISTRAL_API_KEY"))

    # Reconstruction du vectorstore LangChain
    vectorstore = FAISS.from_embeddings(
        text_embeddings=zip([d.page_content for d in documents], embeddings_array),
        embedding=embeddings_model,
        metadatas=metadata_list
    )

    #logger.info(f"✅ Vectorstore prêt et synchronisé ({len(documents)} documents)")
    return vectorstore