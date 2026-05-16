# Archivo: api/server.py
from src.database import save_asistencia, get_persona_id, load_embeddings
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

# Importamos tus funciones de base de datos
from src.database import save_asistencia, get_persona_id

app = FastAPI(title="API Control de Asistencia - Tech Lab")


# 1. Esquema de datos (Actualizado para usar 'nombre' en lugar de un ID de texto)
class Reconocimiento(BaseModel):
    nombre: str
    score: float


class PayloadAsistencia(BaseModel):
    camera_id: str
    timestamp: str
    recognized_faces: List[Reconocimiento]


# 2. Rutas de la API
@app.get("/health")
def check_health():
    return {"status": "ok", "mensaje": "API del Tech Lab operativa"}


@app.post("/api/v1/asistencia/registrar")
def registrar_asistencia(payload: PayloadAsistencia):
    procesados = 0
    errores = []

    print(f"[API] Recibiendo datos de {payload.camera_id}...")

    for face in payload.recognized_faces:
        # 1. Buscar el ID real de la persona en la base de datos usando tu función
        persona_id = get_persona_id(face.nombre)

        if persona_id:
            # 2. Guardar la asistencia (por ahora forzado a "entrada" como en tu script original)
            save_asistencia(persona_id, "entrada")
            procesados += 1
            print(f" -> [OK] Asistencia guardada en BD: {face.nombre}")
        else:
            # Si el nombre no existe en la tabla 'personas'
            errores.append(face.nombre)
            print(f" -> [ALERTA] Persona no encontrada en BD: {face.nombre}")

    return {
        "status": "completado",
        "registros_guardados": procesados,
        "no_encontrados": errores
    }


@app.get("/api/v1/embeddings")
def obtener_embeddings():
    """Descarga los rostros registrados desde la base de datos hacia el nodo Edge."""
    print("[API] Solicitud de descarga de embeddings recibida...")
    try:
        registered = load_embeddings()

        # Convertir los ndarray de NumPy a listas nativas para poder enviarlos por JSON
        datos_serializados = {
            nombre: embedding.tolist() for nombre, embedding in registered.items()
        }

        print(f"[API] Enviando {len(datos_serializados)} perfiles registrados.")
        return datos_serializados

    except Exception as e:
        return {"error": f"Error al cargar embeddings: {str(e)}"}