# Archivo: api/server.py
import base64
from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from fastapi.responses import StreamingResponse
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

async def notify_update(entity: str):
    await manager.broadcast({"type": "update", "entity": entity})
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
usuarios_en_registro = 0

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
    save_persona,
    update_proyecto,
    delete_proyecto,
    get_personas_info,
    update_persona,
    delete_persona,
    get_personas_en_laboratorio,
    cerrar_sesiones_abandonadas,
    delete_registro_asistencia
)

app = FastAPI(title="API Control de Asistencia - Tech Lab")

"""from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()

def job_cerrar_sesiones():
    procesados = cerrar_sesiones_abandonadas()
    if procesados > 0:
        print(f"[CRON] Se cerraron {procesados} sesiones abandonadas.")
        asyncio.create_task(notify_update("asistencia"))

@app.on_event("startup")
def start_scheduler():
    # Ejecutar la limpieza una vez al iniciar el servidor por si hubo caídas
    job_cerrar_sesiones()
    
    # Programar la limpieza recurrente a las 00:00
    scheduler.add_job(job_cerrar_sesiones, 'cron', hour=0, minute=0)
    scheduler.start()
    print("[INFO] Tarea programada de cierre a las 00:00 y en startup inicializada.")"""


from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Asegúrate de importar asyncio si no lo tenías arriba
import asyncio

scheduler = AsyncIOScheduler()

# 1. Cambiamos a 'async def'
async def job_cerrar_sesiones():
    procesados = cerrar_sesiones_abandonadas()
    if procesados > 0:
        print(f"[CRON] Se cerraron {procesados} sesiones abandonadas.")
        # 2. Ahora podemos usar 'await' directamente sin usar create_task
        await notify_update("asistencia")

# 3. Cambiamos el startup a 'async def' también
@app.on_event("startup")
async def start_scheduler():
    # Ejecutar la limpieza una vez al iniciar el servidor
    await job_cerrar_sesiones()
    
    # Programar la limpieza recurrente a las 00:00
    scheduler.add_job(job_cerrar_sesiones, 'cron', hour=00, minute=00)
    scheduler.start()
    print("[INFO] Tarea programada de cierre a las 00:00 y en startup inicializada.")

    # ---------------------------------------------------------
    # NUEVO: Encendido autónomo del motor de IA
    # ---------------------------------------------------------
    global proceso_main
    if proceso_main is None or proceso_main.poll() is not None:
        proceso_main = subprocess.Popen([sys.executable, "main.py"])
        print("[INFO] Motor de IA iniciado automáticamente de forma autónoma.")

@app.on_event("shutdown")
async def shutdown_event():
    global proceso_main
    if proceso_main is not None and proceso_main.poll() is None:
        proceso_main.terminate()
        print("[INFO] Proceso main.py (cámara) terminado de forma segura para evitar duplicados.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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

class ProyectoUpdateRequest(BaseModel):
    nombre_proyecto: str
    descripcion: Optional[str] = ""

class PersonaUpdateRequest(BaseModel):
    dni: str
    codigo_alumno: str
    nombres: str
    apellidos: str
    proyecto_id: Optional[int] = None
    estado_activo: bool


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
async def set_estado(payload: EstadoRequest):
    global proceso_main, usuarios_en_registro
    
    # Solo rechazamos si alguien pide ENCENDER y hay AL MENOS UNA persona registrando
    if payload.activo and usuarios_en_registro > 0:
        raise HTTPException(
            status_code=403, 
            detail=f"Recurso bloqueado: Hay {usuarios_en_registro} persona(s) usando la cámara."
        )

    if payload.activo:
        if proceso_main is None or proceso_main.poll() is not None:
            proceso_main = subprocess.Popen([sys.executable, "main.py"])
    else:
        if proceso_main is not None and proceso_main.poll() is None:
            proceso_main.terminate()
            proceso_main = None

    await notify_update("estado_sistema")
    return {"status": "ok", "activo": payload.activo}


@app.get("/api/v1/proyectos")
def listar_proyectos():
    return {"status": "ok", "data": get_proyectos()}


@app.post("/api/v1/proyectos")
def crear_proyecto(payload: ProyectoRequest, background_tasks: BackgroundTasks):
    id_nuevo = save_proyecto(payload.nombre_proyecto, payload.descripcion)
    if id_nuevo:
        background_tasks.add_task(notify_update, "proyectos")
        return {"status": "ok", "proyecto_id": id_nuevo, "mensaje": "Proyecto creado con éxito"}
    raise HTTPException(status_code=400, detail="No se pudo registrar el proyecto")


@app.put("/api/v1/proyectos/{proyecto_id}")
def modificar_proyecto(proyecto_id: int, payload: ProyectoUpdateRequest, background_tasks: BackgroundTasks):
    exito = update_proyecto(proyecto_id, payload.nombre_proyecto, payload.descripcion)
    if exito:
        background_tasks.add_task(notify_update, "proyectos")
        return {"status": "ok", "mensaje": "Proyecto actualizado"}
    raise HTTPException(status_code=400, detail="Error al actualizar proyecto")


@app.delete("/api/v1/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int, background_tasks: BackgroundTasks):
    exito = delete_proyecto(proyecto_id)
    if exito:
        background_tasks.add_task(notify_update, "proyectos")
        return {"status": "ok", "mensaje": "Proyecto eliminado"}
    raise HTTPException(status_code=400, detail="Error al eliminar proyecto")


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
def registrar_asistencia(payload: PayloadAsistencia, background_tasks: BackgroundTasks):
    from datetime import datetime
    procesados = 0
    errores = []

    for face in payload.recognized_faces:
        persona_id = get_persona_id(face.nombre)
        if not persona_id:
            errores.append(face.nombre)
            continue

        ultimo = get_ultimo_estado_asistencia(persona_id)
        ahora = datetime.now()

        # CASO 1: Es su primera vez en la vida o no hay registros
        if ultimo is None:
            save_asistencia(persona_id, "entrada")
            procesados += 1
            continue

        # Calculamos cuánto tiempo ha pasado desde su último evento
        diferencia = ahora - ultimo["fecha_hora"]
        minutos_transcurridos = diferencia.total_seconds() / 60.0

        # CASO 2: Su último evento fue una ENTRADA
        if ultimo["tipo"] == "entrada":
            # Si entró hace menos de 5 minutos, sigue en la puerta. Ignoramos.
            if minutos_transcurridos < 5:
                continue 
            else:
                # Ya pasó un buen rato, esto es definitivamente su salida.
                save_asistencia(persona_id, "salida")
                procesados += 1

        # CASO 3: Su último evento fue una SALIDA
        elif ultimo["tipo"] == "salida":
            # Si salió hace menos de 5 minutos, sigue en la puerta despidiéndose. Ignoramos.
            if minutos_transcurridos < 5:
                continue
            
            # Si regresó entre 5 y 30 minutos, fue al baño. Borramos la salida.
            elif 5 <= minutos_transcurridos < 30:
                delete_registro_asistencia(ultimo["id"])
                procesados += 1
                
            # Si pasaron más de 30 minutos, es un nuevo día o una nueva sesión.
            else:
                save_asistencia(persona_id, "entrada")
                procesados += 1

    # Notificamos a React por WebSocket solo si hubo cambios reales
    if procesados > 0:
        background_tasks.add_task(notify_update, "asistencia")

    return {"status": "completado", "registros_guardados": procesados, "no_encontrados": errores}


@app.post("/api/v1/personas/registrar")
def registrar_alumno(payload: AlumnoRegistroRequest, background_tasks: BackgroundTasks):
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
        background_tasks.add_task(notify_update, "personas")
        return {"status": "ok", "mensaje": f"Alumno {payload.nombres} agregado correctamente"}
    raise HTTPException(status_code=500, detail="Error de inserción en el almacenamiento relacional")


@app.get("/api/v1/personas")
def listar_personas():
    return {"status": "ok", "data": get_personas_info()}

@app.get("/api/v1/personas/exportar")
def exportar_personas_csv():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.dni, p.codigo_alumno, p.nombres, p.apellidos,
                   COALESCE(pr.nombre_proyecto, 'Sin proyecto') AS proyecto,
                   p.fecha_registro, p.estado_activo
            FROM personas p
            LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
            ORDER BY p.apellidos, p.nombres
        """)
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["DNI", "Código de Alumno", "Nombres", "Apellidos", "Proyecto", "Fecha de Registro", "Activo"])

        formato = "%d/%m/%Y %H:%M:%S"
        for row in rows:
            fecha_str = row[5].strftime(formato) if row[5] else "---"
            activo_str = "Sí" if row[6] else "No"
            writer.writerow([row[0] or "Sin DNI", row[1], row[2], row[3], row[4], fecha_str, activo_str])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=personas.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.put("/api/v1/personas/{persona_id}")
def modificar_persona(persona_id: int, payload: PersonaUpdateRequest, background_tasks: BackgroundTasks):
    exito = update_persona(
        persona_id, payload.dni, payload.codigo_alumno, 
        payload.nombres, payload.apellidos, payload.proyecto_id, payload.estado_activo
    )
    if exito:
        background_tasks.add_task(notify_update, "personas")
        return {"status": "ok", "mensaje": "Persona actualizada"}
    raise HTTPException(status_code=400, detail="Error al actualizar persona")


@app.delete("/api/v1/personas/{persona_id}")
def eliminar_persona(persona_id: int, background_tasks: BackgroundTasks):
    exito = delete_persona(persona_id)
    if exito:
        background_tasks.add_task(notify_update, "personas")
        return {"status": "ok", "mensaje": "Persona eliminada"}
    raise HTTPException(status_code=400, detail="Error al eliminar persona")

@app.get("/api/v1/reportes/asistencia")
def reporte_asistencia(limite: int = 50, filtro: str = None, fecha: str = None):
    registros = get_historial_asistencia(limite=limite, texto_busqueda=filtro, fecha=fecha)
    return {"status": "ok", "total_registros": len(registros), "data": registros}

@app.get("/api/v1/asistencia/en-laboratorio")
def personas_en_laboratorio():
    data = get_personas_en_laboratorio()
    return {"status": "ok", "data": data}


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
                            -- CORRECCIÓN: Aseguramos el orden estricto por id ante empates de hora
                            LEAD(tipo) OVER (PARTITION BY persona_id ORDER BY fecha_hora ASC, id ASC) AS sig_tipo,
                            LEAD(fecha_hora) OVER (PARTITION BY persona_id ORDER BY fecha_hora ASC, id ASC) AS salida
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
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("[WARN] No se pudo conectar a la cámara inicialmente.")
        
    try:
        while True:
            if not cap.isOpened():
                time.sleep(RECONNECT_DELAY)
                cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)
                continue

            ret, frame = cap.read()
            if not ret:
                cap.release()
                continue  

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        # ¡ESTO ES VITAL! Se ejecuta obligatoriamente cuando el usuario sale de la pestaña
        if cap is not None:
            cap.release()
            print("[INFO] Cámara liberada correctamente por el servidor web.")


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

        query += " ORDER BY CASE WHEN salida IS NULL THEN 0 ELSE 1 END ASC, COALESCE(salida, entrada) DESC"

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

@app.post("/api/v1/sistema/registro/iniciar")
def iniciar_registro():
    global usuarios_en_registro
    usuarios_en_registro += 1
    print(f"[SEMAFORO] Candado activado. Usuarios en registro: {usuarios_en_registro}")
    return {"status": "candado_activado", "usuarios": usuarios_en_registro}

@app.post("/api/v1/sistema/registro/finalizar")
def finalizar_registro():
    global usuarios_en_registro
    # Evitamos que el contador baje de 0 en caso de múltiples llamadas accidentales
    if usuarios_en_registro > 0:
        usuarios_en_registro -= 1
        
    print(f"[SEMAFORO] Candado liberado. Usuarios restantes: {usuarios_en_registro}")
    return {"status": "candado_liberado", "usuarios": usuarios_en_registro}