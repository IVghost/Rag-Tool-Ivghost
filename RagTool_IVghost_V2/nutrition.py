# nutrition.py

import time
import json
import pandas as pd
import requests
from logging_utils import log, stop_event
from file_utils import load_csv_safely, clean_nutrition_data
from llm_client import query_llm, OLLAMA_URL

def calculate_missing_macros(protein, carbs, fats, kcal):
    try:
        p = float(protein) if protein not in [None, ""] else None
        c = float(carbs)    if carbs    not in [None, ""] else None
        f = float(fats)     if fats     not in [None, ""] else None
        k = float(kcal)     if kcal     not in [None, ""] else None

        # Si toutes les macros sont fournies
        if all(v is not None for v in [p, c, f]):
            return p, c, f, p*4 + c*4 + f*9

        # Si kcal fourni seul ou partiellement
        if k:
            known = sum([p*4 if p else 0, c*4 if c else 0, f*9 if f else 0])
            remaining = k - known
            missing = sum(1 for v in [p, c, f] if v is None)

            if missing == 1:
                if p is None: p = remaining/4
                elif c is None: c = remaining/4
                else: f = remaining/9
            elif missing == 2:
                if p is not None:
                    c = (remaining*0.6)/4
                    f = (remaining*0.4)/9
                else:
                    p = (remaining*0.3)/4
                    c = (remaining*0.4)/4
                    f = (remaining*0.3)/9
            else:
                p = (k*0.3)/4
                c = (k*0.4)/4
                f = (k*0.3)/9

            return round(p,1), round(c,1), round(f,1), k

        raise ValueError("Au moins un paramètre doit être fourni")
    except Exception as e:
        raise ValueError(f"Erreur de calcul: {e}")


def generate_nutrition_plan(file, protein, carbs, fats, kcal, diet_type, model, meals):
    start = time.time()
    log("🔄 Début génération plan nutritionnel…")

    if stop_event.is_set():
        return "❌ Opération annulée."

    # Validation du fichier
    if file is None:
        return "❌ Veuillez télécharger un fichier."
    path = getattr(file, "name", None)
    if not path:
        return "❌ Fichier non valide."

    # Conversion des inputs
    try:
        protein = float(protein) if protein not in [None, ""] else 0
        carbs   = float(carbs)   if carbs   not in [None, ""] else 0
        fats    = float(fats)    if fats    not in [None, ""] else 0
        kcal    = float(kcal)    if kcal    not in [None, ""] else (protein*4 + carbs*4 + fats*9)
    except:
        return "❌ Valeurs nutritionnelles incorrectes."

    try:
        meals = int(meals)
        if meals <= 0:
            raise ValueError()
    except:
        return "❌ Nombre de repas invalide."

    # Chargement des données aliments
    try:
        if path.endswith(".csv"):
            df = load_csv_safely(path)
        elif path.endswith(".json"):
            df = clean_nutrition_data(path)
        elif path.endswith(".xlsx"):
            df = pd.read_excel(path)
        else:
            return "❌ Format de fichier non supporté."
    except Exception as e:
        return f"❌ Erreur lecture fichier : {e}"

    records = df.head(20).to_dict("records")
    log(f"✅ {len(records)} aliments chargés.")

    # Construction du prompt
    prompt = (
        f"Tu es un assistant expert en nutrition. Génère un plan alimentaire sur 7 jours, "
        f"{meals} repas/jour, en respectant ces macros quotidiennes :\n"
        f"- {kcal:.0f} kcal\n"
        f"- {protein:.1f} g protéines ({protein/meals:.1f}g/repas)\n"
        f"- {carbs:.1f} g glucides ({carbs/meals:.1f}g/repas)\n"
        f"- {fats:.1f} g lipides ({fats/meals:.1f}g/repas)\n\n"
        "Utilise uniquement ces aliments (quantité en g) :\n" +
        json.dumps(records, indent=2) +
        "\n\nAffiche seulement un tableau sans explications, au format markdown."
    )

    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False}
    )
    if response.status_code != 200:
        return f"❌ Erreur API nutrition ({response.status_code}) : {response.text}"

    result = response.json().get("response", "").strip()
    duration = time.time() - start
    log(f"✅ Plan généré en {duration:.2f}s.")
    return result
