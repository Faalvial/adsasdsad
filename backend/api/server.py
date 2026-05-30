# Archivo: api/server.py
import base64
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from fastapi.responses import StreamingResponse
from config import CAMERA_INDEX
import cv2
import numpy as np
import subprocess
import sys
from insightface.app import FaceAnalysis

# Variable para mantener el rastro del proceso de fondo
proceso_main = None

class EstadoRequest(BaseModel):
    activo: bool

from src.database import (
    get_connection,
    save_asistencia,
    get_persona_id,
    load_embeddings,
    get_ultimo_estado_asistencia,
    get_historial_asistencia,
    get_proyectos,
    save_proyecto,
    save_persona
)

app = FastAPI(title="API Control de Asistencia - Tech Lab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("[INFO] Inicializando modelo InsightFace en entorno API central...")
face_app = FaceAnalysis(name="buffalo_sc", providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_size=(640, 640))


class Reconocimiento(BaseModel):
    nombre: str
    score: float


class PayloadAsistencia(BaseModel):
    camera_id: str
    timestamp: str
    recognized_faces: List[Reconocimiento]


class ProyectoRequest(BaseModel):
    nombre_proyecto: str
    descripcion: Optional[str] = ""


class AlumnoRegistroRequest(BaseModel):
    codigo_alumno: str
    nombres: str
    apellidos: str
    proyecto_id: Optional[int] = None
    imagenes: List[str]


@app.get("/health")
def check_health():
    return {"status": "ok", "mensaje": "API del Tech Lab operativa"}


@app.get("/api/v1/sistema/estado")
def get_estado():
    global proceso_main
    # Si el proceso existe y no ha terminado (poll es None), está activo
    activo = proceso_main is not None and proceso_main.poll() is None
    return {"activo": activo}


@app.post("/api/v1/sistema/estado")
def set_estado(payload: EstadoRequest):
    global proceso_main
    if payload.activo:
        # Encender main.py usando el mismo entorno virtual (sys.executable)
        if proceso_main is None or proceso_main.poll() is not None:
            proceso_main = subprocess.Popen([sys.executable, "main.py"])
    else:
        # Apagar main.py destruyendo el proceso
        if proceso_main is not None and proceso_main.poll() is None:
            proceso_main.terminate()
            proceso_main = None

    return {"status": "ok", "activo": payload.activo}


@app.get("/api/v1/proyectos")
def listar_proyectos():
    return {"status": "ok", "data": get_proyectos()}


@app.post("/api/v1/proyectos")
def crear_proyecto(payload: ProyectoRequest):
    id_nuevo = save_proyecto(payload.nombre_proyecto, payload.descripcion)
    if id_nuevo:
        return {"status": "ok", "proyecto_id": id_nuevo, "mensaje": "Proyecto creado con éxito"}
    raise HTTPException(status_code=400, detail="No se pudo registrar el proyecto")


@app.get("/api/v1/embeddings")
def obtener_embeddings():
    try:
        registered = load_embeddings()
        datos_serializados = {
            codigo: embedding.tolist() for codigo, embedding in registered.items()
        }
        return datos_serializados
    except Exception as e:
        return {"error": f"Error al transferir perfiles biométricos: {str(e)}"}


@app.post("/api/v1/asistencia/registrar")
def registrar_asistencia(payload: PayloadAsistencia):
    procesados = 0
    errores = []
    for face in payload.recognized_faces:
        persona_id = get_persona_id(face.nombre)
        if persona_id:
            ultimo_estado = get_ultimo_estado_asistencia(persona_id)
            nuevo_estado = "salida" if ultimo_estado == "entrada" else "entrada"
            save_asistencia(persona_id, nuevo_estado)
            procesados += 1
        else:
            errores.append(face.nombre)
    return {"status": "completado", "registros_guardados": procesados, "no_encontrados": errores}


@app.post("/api/v1/personas/registrar")
def registrar_alumno(payload: AlumnoRegistroRequest):
    if len(payload.imagenes) != 5:
        raise HTTPException(status_code=400, detail="El sistema requiere exactamente 5 capturas espaciadas")

    embeddings = []
    for idx, img_b64 in enumerate(payload.imagenes):
        try:
            if "," in img_b64:
                img_b64 = img_b64.split(",")[1]
            img_bytes = base64.b64decode(img_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                raise HTTPException(status_code=400, detail=f"Fallo en decodificación de la toma {idx + 1}")

            faces = face_app.get(frame)
            if len(faces) == 0:
                raise HTTPException(status_code=400, detail=f"No se localizó ningún rostro en la toma {idx + 1}")
            embeddings.append(faces[0].embedding)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error en procesamiento de toma {idx + 1}: {str(e)}")

    embedding_promedio = np.mean(embeddings, axis=0)
    exito = save_persona(
        codigo_alumno=payload.codigo_alumno,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        proyecto_id=payload.proyecto_id,
        embedding=embedding_promedio
    )
    if exito:
        return {"status": "ok", "mensaje": f"Alumno {payload.codigo_alumno} enrolado correctamente"}
    raise HTTPException(status_code=500, detail="Error de inserción en el almacenamiento relacional")


@app.get("/api/v1/reportes/asistencia")
def reporte_asistencia(limite: int = 50, filtro: str = None, fecha: str = None):
    registros = get_historial_asistencia(limite=limite, texto_busqueda=filtro, fecha=fecha)
    return {"status": "ok", "total_registros": len(registros), "data": registros}


@app.get("/api/v1/supervision/resumen")
def resumen_supervision(proyecto_id: Optional[int] = None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT p.id, p.codigo_alumno, p.nombres, p.apellidos, pr.nombre_proyecto, a.tipo, a.fecha_hora
            FROM personas p
            LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
            LEFT JOIN asistencia a ON p.id = a.persona_id
        """
        params = []
        if proyecto_id:
            query += " WHERE p.proyecto_id = %s"
            params.append(proyecto_id)
        query += " ORDER BY p.id, a.fecha_hora ASC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        alumnos_map = {}
        for row in rows:
            p_id, codigo, nom, ape, proj_nom, tipo, f_hora = row
            if p_id not in alumnos_map:
                alumnos_map[p_id] = {
                    "codigo_alumno": codigo,
                    "nombres": nom,
                    "apellidos": ape,
                    "proyecto": proj_nom or "Sin proyecto",
                    "asistencias_raw": []
                }
            if tipo and f_hora:
                alumnos_map[p_id]["asistencias_raw"].append((tipo, f_hora))

        resumen = []
        for p_id, info in alumnos_map.items():
            horas_totales = 0.0
            logs = info["asistencias_raw"]
            i = 0
            while i < len(logs):
                tipo, hora = logs[i]
                if tipo == "entrada" and (i + 1) < len(logs):
                    sig_tipo, sig_hora = logs[i + 1]
                    if sig_tipo == "salida":
                        diff = sig_hora - hora
                        horas_totales += diff.total_seconds() / 3600.0
                        i += 2
                        continue
                i += 1
            resumen.append({
                "codigo_alumno": info["codigo_alumno"],
                "nombres": info["nombres"],
                "apellidos": info["apellidos"],
                "proyecto": info["proyecto"],
                "horas_totales": round(horas_totales, 2)
            })
        return {"status": "ok", "data": resumen}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def generador_frames_rtsp():
    """Conecta a la cámara y genera un flujo continuo de imágenes JPEG"""
    # Usamos la cámara del laboratorio con el motor de red FFMPEG
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("[ERROR] No se pudo conectar a la cámara para el streaming web")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        # Se ejecuta SIEMPRE que el cliente web (React) corta la conexión
        print("[INFO] Cliente web desconectado. Apagando cámara...")
        cap.release()


@app.get("/api/v1/video_feed")
def video_feed():
    """Endpoint que consume el frontend para ver la cámara en vivo"""
    return StreamingResponse(
        generador_frames_rtsp(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Access-Control-Allow-Origin": "*"} # Permiso vital para que el frontend pueda recortar la foto
    )