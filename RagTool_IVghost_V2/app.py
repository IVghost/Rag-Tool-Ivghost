import os
from ui import build_ui

if __name__ == "__main__":
    # Lecture de l'option de partage public Gradio via variable d'env
    share_env = os.getenv("GRADIO_SHARE", "False").lower()
    share = share_env in ("1", "true", "yes")

    # Construire et lancer l'application
    app = build_ui()
    app.launch(server_port=7860, share=share)
