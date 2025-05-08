import threading
import time
import torch
import logging

# Event global pour stopper les opérations
stop_event = threading.Event()

# Configuration du logging
LOG_FILE = "nutricoach.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


def log(message: str) -> None:
    """Affiche un message dans le logger et dans la console"""
    logging.info(message)


def stop_operations() -> None:
    """Déclenche l'arrêt des opérations en cours, vide le cache GPU et termine les threads."""
    stop_event.set()
    log(f"[{time.strftime('%H:%M:%S')}] 🛑 Demande d'arrêt reçue. Tentative de libération des ressources...")

    try:
        # Libération mémoire GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            log(f"[{time.strftime('%H:%M:%S')}] ✅ Mémoire GPU libérée.")
        else:
            log(f"[{time.strftime('%H:%M:%S')}] ⚠️ Pas de GPU détecté, pas de mémoire à libérer.")

        # Arrêt des threads
        for thread in threading.enumerate():
            if thread.is_alive() and thread != threading.main_thread():
                log(f"[{time.strftime('%H:%M:%S')}] ⏳ Tentative d'arrêt du thread {thread.name}...")
                thread.join(timeout=1)

        log(f"[{time.strftime('%H:%M:%S')}] ✅ Tous les threads ont été arrêtés.")

    except Exception as e:
        log(f"[{time.strftime('%H:%M:%S')}] ❌ Erreur lors de l'arrêt des opérations : {e}")
