# document.py

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import chunk_text, extract_text_from_pdf
from llm_client import query_llm

logger = logging.getLogger(__name__)


def summarize_chunk(chunk: str, provider: str, model: str, api_key: str) -> str:
    """Résume un chunk de texte en ciblant obligations, risques et engagements."""
    prompt = (
        "Voici un extrait de contrat. Résume les points clés en identifiant :\n"
        "- Les obligations des parties\n"
        "- Les clauses à risques\n"
        "- Les engagements réciproques\n\n"
        "Sois synthétique, mais rigoureux et utile juridiquement.\n\n"
        f"---\n{chunk}\n---"
    )
    try:
        return query_llm(prompt, model, provider, api_key)
    except Exception as e:
        logger.error(f"Erreur lors du résumé d’un chunk : {e}")
        return "[Erreur pendant le résumé de cette section]"


def analyze_document(file, question, model, full_analysis, provider, api_key, *args):
    """
    - file: le chemin ou objet fichier à analyser
    - question: texte de la question (utilisé si full_analysis=False)
    - model: nom du modèle LLM
    - full_analysis: bool, True pour analyse juridique détaillée
    - provider: nom du fournisseur IA (Ollama, OpenAI, etc.)
    - api_key: clé API (vide si Ollama local)
    - *args: absorb any extra args from Gradio
    """
    start = time.time()
    logger.info(f"[{time.strftime('%H:%M:%S')}] 🔍 Début de l'analyse du document...")

    # 1. Extraction du texte
    text = extract_text_from_pdf(file)

    # 2. Si on veut juste répondre à une question
    if not full_analysis:
        if not question:
            return "❌ Veuillez fournir une question pour l'analyse."
        prompt = f"Voici un document :\n{text}\n\nQuestion : {question}"
        logger.info("🔄 Envoi du prompt question au LLM...")
        result = query_llm(prompt, model, provider, api_key)
        elapsed = round(time.time() - start, 2)
        logger.info(f"✅ Analyse terminée en {elapsed}s.")
        return result

    # 3. Analyse complète en mode chunk + synthèse
    logger.info("🔀 Chunking du document pour résumé parallèle...")
    chunks = chunk_text(text, max_tokens=600)

    summaries = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(summarize_chunk, chunk, provider, model, api_key): idx
            for idx, chunk in enumerate(chunks)
        }
        for future in as_completed(futures):
            idx = futures[future]
            logger.info(f"🔖 Résumé chunk {idx + 1}/{len(chunks)}")
            try:
                summaries.append(future.result())
            except Exception as e:
                summaries.append("[Erreur dans ce chunk]")
                logger.error(f"Erreur chunk {idx + 1}: {e}")

    combined_summary = "\n\n".join(summaries)

    # 4. Synthèse finale
    final_prompt = (
        "À partir des résumés ci-dessous d’un contrat, réalise une synthèse claire :\n"
        "- Liste les obligations principales pour chaque partie\n"
        "- Identifie les clauses à risques ou ambiguës\n"
        "- Reformule les engagements mutuels\n\n"
        f"{combined_summary}"
    )
    logger.info("🔄 Envoi du prompt de synthèse finale au LLM...")
    result = query_llm(final_prompt, model, provider, api_key)

    elapsed = round(time.time() - start, 2)
    logger.info(f"✅ Analyse complète terminée en {elapsed}s.")
    return result
