# ui.py

import gradio as gr
import requests
from llm_client import OLLAMA_MODELS_URL
from file_utils import extract_content  # si besoin
from document import analyze_document
from nutrition import generate_nutrition_plan

def check_connection():
    try:
        res = requests.get(OLLAMA_MODELS_URL, timeout=2)
        return "🟢 Connecté à Ollama" if res.status_code == 200 else "🔴 Ollama non disponible"
    except Exception as e:
        return f"🔴 Ollama non disponible ({e})"

def get_available_models():
    try:
        res = requests.get(OLLAMA_MODELS_URL, timeout=2)
        names = [m["name"] for m in res.json().get("models", [])]
        return names or ["Aucun modèle disponible"]
    except Exception as e:
        return [f"Erreur de connexion: {e}"]

def build_general_assistant_tab():
    with gr.Tab("💬 Assistant Général"):
        gr.Markdown("## Analyse des documents")
        with gr.Row():
            doc_input = gr.File(label="Document (PDF/CSV/Excel)")
            question_input = gr.Textbox(label="Question", lines=3)
            full_analysis = gr.Checkbox(label="🔍 Analyse juridique", value=False)
            full_analysis.change(lambda chk: gr.update(visible=not chk), inputs=full_analysis, outputs=question_input)
        output = gr.Textbox(label="Réponse", lines=10, interactive=False)
        gr.Button("🔍 Analyser").click(
            analyze_document,
            inputs=[doc_input, question_input, model_selector, full_analysis, llm_provider, api_key_input],
            outputs=output
        )

def build_nutrition_tab():
    with gr.Tab("🍎 Assistant Nutrition"):
        gr.Markdown("## Générateur de plan nutritionnel")
        with gr.Row():
            file_input = gr.File(label="Fichier aliments (.csv/.json/.xlsx)")
            with gr.Column():
                protein_input = gr.Number(label="Protéines (g/jour)")
                carbs_input   = gr.Number(label="Glucides (g/jour)")
                fats_input    = gr.Number(label="Lipides (g/jour)")
                kcal_input    = gr.Number(label="Calories cibles")
                meals_input   = gr.Number(label="Repas/jour", precision=0)
        diet_type = gr.Dropdown(label="Type de régime", choices=["Standard","Végétarien","Vegan","Cétogène"], value="Standard")
        nutrition_output = gr.Markdown()
        gr.Button("🚀 Générer").click(
            generate_nutrition_plan,
            inputs=[file_input, protein_input, carbs_input, fats_input, kcal_input, diet_type, model_selector, meals_input],
            outputs=nutrition_output
        )

def build_ui():
    with gr.Blocks(title="IvGhost RAG tool", theme=gr.themes.Soft()) as app:
        gr.Markdown("# RAG AI Tool")
        status = gr.Markdown(value=check_connection(), elem_id="status")
        gr.Button("🔄 Vérifier connexion").click(lambda: check_connection(), outputs=status)

        global model_selector, llm_provider, api_key_input
        model_selector = gr.Dropdown(label="Modèle LLM", choices=get_available_models(), interactive=True)
        llm_provider   = gr.Dropdown(label="Fournisseur IA", choices=["Ollama (local)","OpenAI","Anthropic","Perplexity"], value="Ollama (local)", interactive=True)
        api_key_input  = gr.Textbox(label="🔑 Clé API (si externe)", type="password", interactive=True)

        gr.Button("🛑 Stop").click(lambda: None)  # à relier stop_operations si importé

        with gr.Tabs():
            build_general_assistant_tab()
            build_nutrition_tab()

    return app
