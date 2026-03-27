# mistral_tool.py

from mistralai import Mistral
import os
from dotenv import load_dotenv

load_dotenv()

# 🔹 Créer le client une seule fois au lieu de le recréer à chaque appel
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)
MODEL_NAME = "mistral-large-latest"

def generate_mistral_response(context_str, question, max_tokens=600, temperature=0.3):
    """
    Génère une réponse basée sur le contexte fourni déjà sous forme de texte.
    
    context_str : str -> Texte complet du contexte (déjà fusionné)
    question : str -> Question de l'utilisateur
    """

    # 🔹 Si le contexte est vide
    if not context_str:
        context_str = "Aucun événement trouvé."

    # 🔹 Prompt unique
    prompt = f"""
    Tu es un assistant culturel expert de la région Île-de-France.
    Ta mission est d'aider l'utilisateur à trouver des sorties en utilisant UNIQUEMENT les données fournies.

    CONTEXTE (Événements filtrés pour la requête) :
    {context_str}

    QUESTION DE L'UTILISATEUR : 
    {question}

    RÈGLES CRITIQUES :
    1. Si le contexte contient "Aucun événement trouvé" ou est vide, réponds exactement : "Désolé, je n'ai trouvé aucun événement correspondant à votre recherche dans ma base de données."
    2. Si des événements sont présents, présente-les TOUS sans exception, par ordre chronologique.
    3. Ne mentionne jamais d'événements qui ne sont pas dans la liste ci-dessus.
    4. Pour chaque événement, respecte ce format :
    - **[Nom de l'événement]**
    - 📍 Ville : [Ville]
    - 📅 Date : [Date formatée proprement]
    - 🏛️ Lieu : [Lieu]
    - 📝 Description : [Description courte]

    5. Ton ton doit être chaleureux et professionnel.
    6. Termine TOUJOURS en proposant à l'utilisateur d'affiner sa recherche par thème (ex: musique, famille, danse), par ville ou par type de tarif (gratuit/payant).
    """

    # 🔹 Appel à l'API Mistral
    response = client.chat.complete(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content