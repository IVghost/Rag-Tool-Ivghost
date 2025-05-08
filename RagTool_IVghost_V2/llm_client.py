# llm_client.py

import time
import requests
from logging_utils import log

# === Configuration Ollama ===
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODELS_URL = "http://localhost:11434/api/tags"

def query_llm(prompt: str, model: str, provider: str, api_key: str) -> str:
    """
    Envoie un prompt texte à un modèle LLM (Ollama local ou externe) et retourne la réponse.
    """
    log(f"[{time.strftime('%H:%M:%S')}] 🔄 Envoi du prompt au LLM ({provider})...")
    start_time = time.time()

    # Préparation de la requête
    if provider == "Ollama (local)":
        url = OLLAMA_URL
        payload = {"model": model, "prompt": prompt, "stream": False}
        headers = {}
    elif provider == "OpenAI":
        if "gpt" in model.lower():
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
        else:
            url = "https://api.openai.com/v1/completions"
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.7
            }
        headers = {"Authorization": f"Bearer {api_key}"}
    elif provider == "Anthropic":
        url = "https://api.anthropic.com/v1/complete"
        payload = {
            "model": model,
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 1000
        }
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    elif provider == "Perplexity":
        url = "https://api.perplexity.ai/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        headers = {"Authorization": f"Bearer {api_key}"}
    else:
        return "❌ Fournisseur IA non pris en charge."

    # Envoi de la requête (sans timeout pour Ollama local)
    try:
        if provider == "Ollama (local)":
            response = requests.post(url, json=payload, headers=headers)
        else:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
        duration = time.time() - start_time
    except Exception as e:
        log(f"❌ Exception lors de l’appel LLM : {e}")
        return f"❌ Erreur lors de l'interrogation de l'IA : {e}"

    # Vérification HTTP
    if response.status_code != 200:
        try:
            err = response.json()
        except:
            err = response.text
        log(f"❌ Erreur API {provider} : {response.status_code} - {err}")
        return f"❌ Erreur API ({response.status_code}) : {err}"

    data = response.json()

    # --- Ollama local utilise le champ "response" ---
    if provider == "Ollama (local)":
        result = data.get("response", "").strip()
        if not result:
            log("⚠️ Réponse vide du modèle Ollama.")
            return "⚠️ Le modèle Ollama n'a pas renvoyé de réponse."
        return result

    # --- Autres providers : on cherche dans "choices" ---
    choices = data.get("choices", [])
    if not choices:
        log("⚠️ Réponse vide du LLM.")
        return "⚠️ Le modèle n'a pas renvoyé de réponse."

    first = choices[0]
    # Chat format
    if "message" in first and "content" in first["message"]:
        return first["message"]["content"].strip()
    # Completions format
    if "text" in first:
        return first["text"].strip()

    log("⚠️ Format de réponse inattendu du modèle.")
    return "⚠️ Format de réponse inattendu du modèle."


def query_llm_vision(prompt: str, file_bytes: bytes, model: str, provider: str, api_key: str) -> str:
    """
    Envoie un fichier image/PDF image à un modèle vision et retourne la réponse.
    """
    log(f"[{time.strftime('%H:%M:%S')}] 🧠 Envoi d'une image vers un modèle Vision ({provider})...")
    try:
        if provider == "Ollama (local)":
            files = {"image": ("document.png", file_bytes, "image/png")}
            # Ollama attend le même endpoint /api/generate
            response = requests.post(OLLAMA_URL, data={"model": model, "prompt": prompt}, files=files)
        elif provider == "OpenAI":
            import base64
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": f"![image](data:image/png;base64,{encoded})"}
                ],
                "max_tokens": 1000
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
        else:
            return "❌ Fournisseur vision non pris en charge."

        if response.status_code != 200:
            try:
                err = response.json()
            except:
                err = response.text
            log(f"❌ Erreur Vision API {provider} : {response.status_code} - {err}")
            return f"❌ Erreur Vision API ({response.status_code}) : {err}"

        data = response.json()
        # OpenAI chat vision
        if "choices" in data and data["choices"]:
            msg = data["choices"][0].get("message", {}).get("content")
            return msg.strip() if msg else "⚠️ Réponse vision vide."
        # Ollama local
        return data.get("response", "⚠️ Réponse vision vide.").strip()

    except Exception as e:
        log(f"❌ Exception Vision : {e}")
        return f"❌ Erreur lors de l'appel au modèle vision : {e}"
