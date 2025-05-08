import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    """Extrait le texte d'un PDF page par page."""
    if not file_path.lower().endswith('.pdf'):
        raise ValueError("Fichier non supporté pour extract_text_from_pdf")
    
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text.append(page_text)
    return "\n".join(text)


def chunk_text(text: str, max_tokens: int = 800) -> list:
    """Découpe un texte en 'chunks' d'environ max_tokens mots."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i:i + max_tokens])
        chunks.append(chunk)
    return chunks
