import time
import pandas as pd
import json
from PyPDF2 import PdfReader
from docx import Document
from logging_utils import log, stop_event


def extract_content(file_path: str) -> str:
    """Extrait le contenu texte des fichiers PDF, DOCX, CSV ou XLSX."""
    lines = []
    start = time.time()
    log(f"🔄 Début de l'extraction : {file_path}")

    if stop_event.is_set():
        log("🛑 Extraction annulée avant début.")
        return ""

    try:
        if file_path.endswith('.pdf'):
            log("📄 Lecture PDF...")
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                if stop_event.is_set():
                    log("🛑 Extraction PDF interrompue.")
                    break
                text = page.extract_text() or ''
                lines.append(text)
                log(f"✅ Page {i+1} extraite.")

        elif file_path.endswith('.docx'):
            log("📄 Lecture DOCX...")
            doc = Document(file_path)
            for i, para in enumerate(doc.paragraphs):
                if stop_event.is_set():
                    log("🛑 Extraction DOCX interrompue.")
                    break
                lines.append(para.text)
                log(f"✅ Paragraphe {i+1}.")

        elif file_path.endswith('.csv'):
            log("📊 Lecture CSV via load_csv_safely...")
            df = load_csv_safely(file_path)
            lines.append(df.to_string())

        elif file_path.endswith('.xlsx'):
            log("📊 Lecture Excel...")
            df = pd.read_excel(file_path)
            lines.append(df.to_string())

        else:
            log(f"❌ Format non supporté : {file_path}")

    except Exception as e:
        log(f"❌ Erreur extraction {e}")

    total = time.time() - start
    log(f"✅ Extraction terminée en {total:.2f}s.")
    return "\n".join(lines)


def is_pdf_image_based(file_path: str) -> bool:
    """Détecte si un PDF ne contient pas de texte (images uniquement)."""
    reader = PdfReader(file_path)
    for page in reader.pages:
        if page.extract_text() and page.extract_text().strip():
            return False
    return True


def load_csv_safely(file_path: str) -> pd.DataFrame:
    """Charge un CSV en détectant le séparateur et gère les erreurs d'encodage/format."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline()

    seps = [',', ';', '\t', '|']
    sep = max(seps, key=lambda s: header.count(s))
    print(f"Séparateur détecté : {repr(sep)}")

    try:
        df = pd.read_csv(file_path, sep=sep, engine='python', on_bad_lines='warn')
    except UnicodeDecodeError:
        print("Encodage différent, réessai ISO-8859-1...")
        df = pd.read_csv(file_path, sep=sep, engine='python', encoding='ISO-8859-1', on_bad_lines='warn')

    print(f"Chargé : {df.shape[0]}x{df.shape[1]}")
    return df


def clean_nutrition_data(json_path: str) -> pd.DataFrame:
    """Nettoie les données nutritionnelles d'un JSON en assurant des types cohérents."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        for k, v in item.items():
            if isinstance(v, str):
                v = v.strip().replace(',', '.')
                try:
                    item[k] = float(v) if v else None
                except ValueError:
                    pass
        # Champs nutritionnels clés
        for key in ['Energie (kcal/100 g)', 'Protéines (g/100 g)', 'Glucides (g/100 g)',
                    'Lipides (g/100 g)', 'Fibres alimentaires (g/100 g)']:
            item[key] = item.get(key) or 0

    return pd.DataFrame(data)
