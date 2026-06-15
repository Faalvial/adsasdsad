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
import csv
import io
import time
from config import CAMERA_INDEX, RECONNECT_DELAY

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
    dni: str  # <--- NUEVO CAMPO
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
    from datetime import datetime, date
    procesados = 0
    errores = []

    for face in payload.recognized_faces:
        persona_id = get_persona_id(face.nombre)
        if not persona_id:
            errores.append(face.nombre)
            continue

        ultimo = get_ultimo_estado_asistencia(persona_id)

        if ultimo is None:
            # Nunca ha marcado → entrada
            nuevo_estado = "entrada"

        elif ultimo["tipo"] == "entrada":
            fecha_ultimo = ultimo["fecha_hora"].date()
            hoy = date.today()

            if fecha_ultimo < hoy:
                # Entrada de un día anterior sin salida → sesión abandonada
                # Cerramos con salida igual a la entrada (suma 0) y marcamos nueva entrada
                save_asistencia(persona_id, "salida", ultimo["fecha_hora"])
                nuevo_estado = "entrada"
            else:
                # Entrada de hoy → salida normal
                nuevo_estado = "salida"

        else:
            # Último fue salida → nueva entrada
            nuevo_estado = "entrada"

        save_asistencia(persona_id, nuevo_estado)
        procesados += 1

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
    # Pasamos el DNI a la base de datos
    exito = save_persona(
        dni=payload.dni,
        codigo_alumno=payload.codigo_alumno,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        proyecto_id=payload.proyecto_id,
        embedding=embedding_promedio
    )
    if exito:
        return {"status": "ok", "mensaje": f"Alumno {payload.nombres} enrolado correctamente"}
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
WITH pares_asistencia AS (
                        SELECT 
                            persona_id,
                            fecha_hora AS entrada,
                            LEAD(tipo) OVER (PARTITION BY persona_id ORDER BY fecha_hora) AS sig_tipo,
                            LEAD(fecha_hora) OVER (PARTITION BY persona_id ORDER BY fecha_hora) AS salida
                        FROM asistencia
                    ),
                    horas_por_persona AS (
                        SELECT 
                            persona_id,
                            SUM(EXTRACT(EPOCH FROM (salida - entrada)) / 3600) AS horas
                        FROM pares_asistencia
                        WHERE sig_tipo = 'salida'
                        GROUP BY persona_id
                    ),
                    extremos_asistencia AS (
                        SELECT 
                            persona_id,
                            MIN(fecha_hora) AS primera_vez,
                            MAX(fecha_hora) AS ultima_vez
                        FROM asistencia
                        GROUP BY persona_id
                    )
                    SELECT 
                        p.dni,
                        p.codigo_alumno, 
                        p.nombres, 
                        p.apellidos, 
                        COALESCE(pr.nombre_proyecto, 'Sin proyecto') AS proyecto,
                        COALESCE(ROUND(hp.horas::numeric, 2), 0.0) AS horas_totales,
                        ea.primera_vez,
                        ea.ultima_vez
                    FROM personas p
                    LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
                    LEFT JOIN horas_por_persona hp ON p.id = hp.persona_id
                    LEFT JOIN extremos_asistencia ea ON p.id = ea.persona_id
                """

        params = []
        if proyecto_id:
            query += " WHERE p.proyecto_id = %s"
            params.append(proyecto_id)

        query += " ORDER BY p.id ASC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        resumen = []
        formato = "%d/%m/%Y, %I:%M %p"

        for row in rows:
            primera = row[6].strftime(formato) if row[6] else "Aún sin asistencias"
            ultima = row[7].strftime(formato) if row[7] else "---"

            resumen.append({
                "dni": row[0] if row[0] else "---",
                "codigo_alumno": row[1],
                "nombres": row[2],
                "apellidos": row[3],
                "proyecto": row[4],
                "horas_totales": float(row[5]),
                "primera_asistencia": primera,
                "ultima_asistencia": ultima
            })

        return {"status": "ok", "data": resumen}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def generador_frames_rtsp():
    """Conecta a la cámara y genera un flujo continuo de imágenes JPEG con reconexión automática"""
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("[WARN] No se pudo conectar a la cámara inicialmente. Reintentando...")

    while True:
        # Si la cámara no está abierta, intentar reconectar
        if not cap.isOpened():
            time.sleep(RECONNECT_DELAY)
            cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print(f"[WARN] Reconexión fallida. Reintentando en {RECONNECT_DELAY}s...")
                continue
            print("[INFO] Cámara reconectada en video feed.")

        ret, frame = cap.read()
        if not ret:
            print("[WARN] Video feed perdido. Intentando reconectar...")
            cap.release()
            continue  # vuelve al inicio, donde detecta que no está abierta y reintenta

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.get("/api/v1/video_feed")
def video_feed():
    """Endpoint que consume el frontend para ver la cámara en vivo"""
    return StreamingResponse(
        generador_frames_rtsp(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Access-Control-Allow-Origin": "*"} # Permiso vital para que el frontend pueda recortar la foto
    )


@app.get("/api/v1/reportes/exportar")
def exportar_historial_csv(fecha: str = None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            WITH eventos AS (
                SELECT 
                    a.id, p.dni, p.codigo_alumno, p.nombres || ' ' || p.apellidos AS nombre_completo,
                    COALESCE(pr.nombre_proyecto, 'Sin proyecto') AS proyecto, a.tipo, a.fecha_hora AS entrada,
                    LEAD(a.tipo) OVER (PARTITION BY a.persona_id ORDER BY a.fecha_hora) AS sig_tipo,
                    LEAD(a.fecha_hora) OVER (PARTITION BY a.persona_id ORDER BY a.fecha_hora) AS salida
                FROM asistencia a
                JOIN personas p ON a.persona_id = p.id
                LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
            )
            SELECT dni, codigo_alumno, nombre_completo, proyecto, entrada, 
                   CASE WHEN sig_tipo = 'salida' THEN salida ELSE NULL END AS salida
            FROM eventos
            WHERE tipo = 'entrada'
        """
        params = []
        if fecha:
            query += " AND DATE(entrada) = %s"
            params.append(fecha)

        query += " ORDER BY entrada DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["DNI", "Código de Alumno", "Nombre Completo", "Proyecto", "Hora de Entrada", "Hora de Salida"])

        formato = "%d/%m/%Y %H:%M:%S"
        for row in rows:
            entrada_str = row[4].strftime(formato) if row[4] else "---"
            salida_str = row[5].strftime(formato) if row[5] else "Aún en laboratorio"
            # row[0] es DNI, si es None enviamos vacío
            dni_str = row[0] if row[0] else "Sin DNI"
            writer.writerow([dni_str, row[1], row[2], row[3], entrada_str, salida_str])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=historial_asistencia_{fecha or 'completo'}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()