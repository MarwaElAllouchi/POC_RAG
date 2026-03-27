# evaluate_chatbot.py
import json
import time  # <--- Ajouté pour gérer le temps
from tqdm import tqdm
from chatbot_agent import get_chatbot_response
from LangChain.vectorize_events import get_vectorstore

# -----------------------------
# Charger le dataset d'évaluation
# -----------------------------
with open("tests/dataset_test.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)

vectorstore = get_vectorstore()
if not vectorstore:
    raise RuntimeError("Vectorstore non chargé, impossible d'évaluer le chatbot.")

# -----------------------------
# Métriques
# -----------------------------
def precision_recall_f1(predicted, expected):
    predicted_set = set(predicted)
    expected_set = set(expected)
    tp = len(predicted_set & expected_set)
    precision = tp / len(predicted_set) if predicted_set else 0
    recall = tp / len(expected_set) if expected_set else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1

# -----------------------------
# Évaluation
# -----------------------------
results = []

for item in tqdm(test_data, desc="Évaluation des questions"):
    question = item["question"]
    expected_uids = item["expected_uids"]

    # --- Gestion du Rate Limit (Retry Logic) ---
    success = False
    attempts = 0
    while not success and attempts < 3:
        try:
            response_text, predicted_uids = get_chatbot_response(question, vectorstore)
            success = True
        except Exception as e:
            if "429" in str(e):
                print(f"\n⚠️ Rate limit atteint. Pause de 20s avant nouvel essai (Essai {attempts+1}/3)...")
                time.sleep(20) # On attend que le quota se libère
                attempts += 1
            else:
                print(f"\n❌ Erreur inattendue : {e}")
                predicted_uids = []
                success = True # On passe à la suite pour ne pas bloquer tout le script

    # Pause de sécurité entre chaque question pour le Free Tier
    time.sleep(2) 

    precision, recall, f1 = precision_recall_f1(predicted_uids, expected_uids)

    results.append({
        "question": question,
        "expected_uids": expected_uids,
        "predicted_uids": predicted_uids,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3)
    })

# -----------------------------
# Affichage console
# -----------------------------
print("\n" + "="*60)
for r in results:
    print(f"Question : {r['question']}")
    print(f"Expected : {r['expected_uids']}")
    print(f"Predicted : {r['predicted_uids']}")
    print(f"Precision: {r['precision']}, Recall: {r['recall']}, F1: {r['f1']}")
    print("-" * 60)

# 🔹 Moyenne globale
if results:
    avg_precision = sum(r['precision'] for r in results) / len(results)
    avg_recall = sum(r['recall'] for r in results) / len(results)
    avg_f1 = sum(r['f1'] for r in results) / len(results)
    print(f"✅ Moyenne globale - Precision: {avg_precision:.2f}, Recall: {avg_recall:.2f}, F1: {avg_f1:.2f}")
else:
    print("❌ Aucun résultat n'a pu être calculé.")