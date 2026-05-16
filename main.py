import cv2
import requests # <--- Nueva importación
from insightface.app import FaceAnalysis

from config import THRESHOLD, MODEL_NAME, CAMERA_INDEX, SKIP_FRAMES
from src.face_recognizer import identify_face
from src.camera import draw_result
from src.database import load_embeddings # Mantenemos esta para cargar las caras al inicio

def main():
    # Inicializar InsightFace
    print("[INFO] Cargando modelo InsightFace...")
    app = FaceAnalysis(name=MODEL_NAME, providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Cargar embeddings desde PostgreSQL
    print("[INFO] Cargando embeddings desde la base de datos...")
    registered = load_embeddings()

    if not registered:
        print("[ERROR] No hay personas registradas en la base de datos")
        print("[INFO] Ejecuta primero el script de registro de personas")
        return

    print(f"[INFO] {len(registered)} persona(s) cargada(s): {list(registered.keys())}")

    # Abrir cámara
    #cap = cv2.VideoCapture(0)
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
            print("[ERROR] No se pudo leer el frame")
            break

        frame_count += 1

        # Analizar uno de cada SKIP_FRAMES frames
        if frame_count % SKIP_FRAMES == 0:
            last_faces = app.get(frame)

        # Procesar cada cara detectada
        for face in last_faces:
            embedding = face.embedding
            name, score = identify_face(embedding, registered, THRESHOLD)

            # Registrar asistencia si es conocido y no está en cooldown
            # Registrar asistencia si es conocido y no está en cooldown
            if name != "Desconocido":
                from datetime import datetime
                ahora = datetime.now()
                ultimo = cooldown.get(name)

                if not ultimo or (ahora - ultimo).seconds > 5:
                    # 1. Construir el payload JSON
                    payload = {
                        "camera_id": "hikvision_lab",
                        "timestamp": ahora.isoformat(),
                        "recognized_faces": [
                            {
                                "nombre": name,
                                "score": float(score)  # Convertir a float nativo de Python
                            }
                        ]
                    }

                    # 2. Enviar a la API
                    try:
                        api_url = "http://localhost:8000/api/v1/asistencia/registrar"
                        respuesta = requests.post(api_url, json=payload, timeout=3)

                        if respuesta.status_code == 200:
                            cooldown[name] = ahora
                            print(f"[OK] Asistencia enviada a la API: {name} - {ahora.strftime('%H:%M:%S')}")
                        else:
                            print(f"[ERROR API] La API respondió con error: {respuesta.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"[ERROR RED] No se pudo conectar con la API: {e}")
            draw_result(frame, face.bbox, name, score)

        cv2.imshow("Control de Asistencia", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()