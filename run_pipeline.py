
#run_pipeline.py
from LangChain.fetch_events import fetch_openagenda_events
from LangChain.filter_events import filter_cultural_events
from LangChain.vectorize_events import create_faiss_index
import os 
import json
from dotenv import load_dotenv

load_dotenv()
AGENDA_UID = "56500817"
TOKEN =  os.getenv("OPENAGENDA_API_KEY")
output_path = "LangChain/data/filtered_events.json"

# 1. Fetch
events = fetch_openagenda_events(
    agenda_uid=AGENDA_UID,
    token=TOKEN,
    page_size=300,
    output_file="LangChain/data/events.json"
)

# 2. Filter
filtered = filter_cultural_events(events)
# Sauvegarde JSON
with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

# 3. Vectorisation + FAISS
index, metadata = create_faiss_index(filtered)