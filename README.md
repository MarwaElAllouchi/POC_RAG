Puls-Events – Assistant Culturel Île-de-France (POC-RAG)

📌 Présentation

Puls-Events est un assistant intelligent pour les événements culturels en Île-de-France.
Il combine les données OpenAgenda et un pipeline RAG (Retrieval-Augmented Generation) pour offrir des réponses précises et naturelles en langage humain.

Fonctionnalités clés :

Centralisation des événements de multiples sources

Filtrage, nettoyage et enrichissement sémantique

Découpage en chunks et vectorisation

Indexation avec FAISS

Recherche et génération de réponses via LangChain + LLM Mistral

🎯 Objectifs

Transformer des données brutes en réponses naturelles et fiables.

Garantir la précision des informations factuelles (dates, lieux, tarifs).

Évaluer la robustesse du pipeline grâce à des tests unitaires.

Démontrer une architecture modulaire prête pour la production.

🗂 Structure du projet
POC_RAG/
│
├─ LangChain/
│   ├─ __init__.py
│   ├─ fetch_events.py
│   ├─ filter_events.py
│   ├─ vectorize_events.py
│   ├─ chatbot_agent.py
│   └─ mistral_tool.py
│
├─ tests/
│   ├─ __init__.py
│   └─ test_pipeline.py
│
├─ run_pipeline.py
├─ evaluate_chatbot.py
├─ requirements.txt
└─ environment.yml

⚙️ Installation & Dépendances
1️⃣ Avec pip
python -m venv rag_env
source rag_env/Scripts/activate  # Windows: rag_env\Scripts\activate
pip install -r requirements.txt

🔑 Clés API

Créer un fichier .env à la racine :

OPENAGENDA_API_KEY=fe4161a724ed4ea58bc3fbce70b2bce3
MISTRAL_API_KEY=Fw181uDxeLQ63Xq6sAUUAtgGs1T3EZ60

🚀 Utilisation

Exécuter le pipeline pour implémenter notre base de données vectorielle

python run_pipeline.py

Tester le chatbot
python -m  chatbot_agent
![![]()](https://)

Évaluer les réponses

python evaluate_chatbot.py

Exécuter les tests unitaires

pytest -v tests/test_pipeline.py

📝 Recommandations

Les tests unitaires garantissent le fonctionnement après modification.

Prévoir un filtrage temporel avant FAISS pour des recherches précises par date.

Le pipeline est modulable : ajout de nouvelles sources ou LLM possible.

Les embeddings et l’index FAISS permettent une recherche rapide par similarité, mais ne remplacent pas une vérification factuelle pour la production.