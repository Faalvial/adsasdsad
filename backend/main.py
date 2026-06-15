import cv2
import requests
from insightface.app import FaceAnalysis
#import winsound
#import winsound
import time
from datetime import datetime

from config import THRESHOLD, MODEL_NAME, CAMERA_INDEX, SKIP_FRAMES, COOLDOWN, DET_THRESHOLD, RECONNECT_DELAY
from src.face_recognizer import identify_face
from src.camera import draw_result
import numpy as np

def main():
    # Inicializar InsightFace
    print("[INFO] Cargando modelo InsightFace...")
    app = FaceAnalysis(name=MODEL_NAME, providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Cargar embeddings desde la API
    print("[INFO] Obteniendo embeddings desde la API central...")
    registered = {}

    try:
        url_embeddings = "http://localhost:8000/api/v1/embeddings"
        respuesta = requests.get(url_embeddings, timeout=5)

        if respuesta.status_code == 200:
            datos_json = respuesta.json()
            registered = {
                nombre: np.array(emb_list, dtype=np.float32)
                for nombre, emb_list in datos_json.items()
            }
        else:
            print(f"[ERROR] La API respondió con código: {respuesta.status_code}")
            return

    except requests.exceptions.RequestException as e:
        print(f"[ERROR RED] No se pudo conectar a la API para cargar embeddings: {e}")
        return

    if not registered:
        print("[ERROR] No se recibieron personas desde la API.")
        return

    print(f"[INFO] {len(registered)} persona(s) cargada(s): {list(registered.keys())}")

    # Abrir cámara
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara")
        return

    print("[INFO] Sistema iniciado. Presiona 'q' para salir.")
    frame_count = 0
    last_faces = []
    cooldown = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Cámara desconectada. Intentando reconectar...")
            cap.release()

            while True:
                time.sleep(RECONNECT_DELAY)
                cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)
                if cap.isOpened():
                    print("[INFO] Cámara reconectada exitosamente.")
                    frame_count = 0
                    last_faces = []
                    break
                print(f"[WARN] Reconexión fallida. Reintentando en {RECONNECT_DELAY}s...")

            continue

        frame_count += 1

        # Cada SKIP_FRAMES: primero detección ligera, luego embedding solo si hay rostros confiables
        if frame_count % SKIP_FRAMES == 0:
            bboxes, _ = app.det_model.detect(frame, input_size=(640, 640))
            rostros_confiables = [b for b in bboxes if b[4] >= DET_THRESHOLD] if bboxes is not None else []

            if len(rostros_confiables) > 0:
                last_faces = app.get(frame)
            else:
                last_faces = []

        # Procesar cada cara detectada
        for face in last_faces:
            embedding = face.embedding
            name, score = identify_face(embedding, registered, THRESHOLD)

            if name != "Desconocido":
                ahora = datetime.now()
                ultimo = cooldown.get(name)

                if not ultimo or (ahora - ultimo).total_seconds() > COOLDOWN:
                    payload = {
                        "camera_id": "hikvision_lab",
                        "timestamp": ahora.isoformat(),
                        "recognized_faces": [
                            {
                                "nombre": name,
                                "score": float(score)
                            }
                        ]
                    }

                    try:
                        api_url = "http://localhost:8000/api/v1/asistencia/registrar"
                        respuesta = requests.post(api_url, json=payload, timeout=3)

                        if respuesta.status_code == 200:
                            cooldown[name] = ahora
                            print(f"[OK] Asistencia enviada a la API: {name} - {ahora.strftime('%H:%M:%S')}")
                            #winsound.Beep(1500, 300)
                        else:
                            print(f"[ERROR API] La API respondió con error: {respuesta.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"[ERROR RED] No se pudo conectar con la API: {e}")
            #draw_result(frame, face.bbox, name, score)

            draw_result(frame, face.bbox, name, score)

        #cv2.imshow("Control de Asistencia", frame)

        #if cv2.waitKey(1) & 0xFF == ord("q"):
            #break

    cap.release()
    #cv2.destroyAllWindows()

if __name__ == "__main__":
    main()