# Lógica de comparación y decisión
import numpy as np

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similitud coseno entre dos embeddings normalizados."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def identify_face(embedding: np.ndarray, registered: dict, threshold: float) -> tuple:
    """
    Compara el embedding de la cara detectada contra todos los registrados.
    Devuelve (nombre, similitud) si supera el threshold.
    Devuelve ("Desconocido", mejor_similitud) si no supera.
    """
    best_name = "Desconocido"
    best_score = -1.0

    for name, registered_embedding in registered.items():
        score = cosine_similarity(embedding, registered_embedding)
        if score > best_score:
            best_score = score
            best_name = name

    if best_score >= threshold:
        return best_name, best_score

    return "Desconocido", best_score