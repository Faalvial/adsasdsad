# Archivo: api/server.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # <--- Nueva importación
from typing import List

# Importamos tus funciones de base de datos
from src.database import save_asistencia, get_persona_id, load_embeddings, get_ultimo_estado_asistencia, get_historial_asistencia

app = FastAPI(title="API Control de Asistencia - Tech Lab")

# Configuración de CORS para permitir que React se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen (ideal para desarrollo)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todas las cabeceras
)

# 1. Esquema de datos
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

@app.post("/api/v1/asistencia/registrar")
def registrar_asistencia(payload: PayloadAsistencia):
    procesados = 0
    errores = []

    print(f"[API] Recibiendo datos de {payload.camera_id}...")

    for face in payload.recognized_faces:
        persona_id = get_persona_id(face.nombre)

        if persona_id:
            # Forzar la lectura y mostrarla en consola
            ultimo_estado = get_ultimo_estado_asistencia(persona_id)
            print(f"[DEBUG] ID Persona: {persona_id} | Último estado leído de BD: '{ultimo_estado}'")

            # Lógica de alternancia
            if ultimo_estado == "entrada":
                nuevo_estado = "salida"
            else:
                nuevo_estado = "entrada"

            print(f"[DEBUG] Calculado nuevo estado -> {nuevo_estado}")

            # Guardar en PostgreSQL
            save_asistencia(persona_id, nuevo_estado)
            procesados += 1
            print(f" -> [OK] Registrada {nuevo_estado.upper()}: {face.nombre}")
        else:
            errores.append(face.nombre)
            print(f" -> [ALERTA] Persona no encontrada en BD: {face.nombre}")

    return {
        "status": "completado",
        "registros_guardados": procesados,
        "no_encontrados": errores
    }


@app.get("/api/v1/reportes/asistencia")
def reporte_asistencia(limite: int = 50, nombre: str = None, fecha: str = None):
    """
    Endpoint para consultar el historial de asistencia del Tech Lab.
    Soporta filtros opcionales:
    - nombre: Filtra por coincidencia parcial (ej. 'Far')
    - fecha: Filtra por un día específico en formato 'YYYY-MM-DD'
    """
    print(f"[API] Generando reporte. Filtros -> Nombre: {nombre} | Fecha: {fecha} | Límite: {limite}")

    registros = get_historial_asistencia(limite=limite, nombre=nombre, fecha=fecha)

    return {
        "status": "ok",
        "total_registros": len(registros),
        "filtros_aplicados": {
            "nombre": nombre,
            "fecha": fecha,
            "limite": limite
        },
        "data": registros
    }