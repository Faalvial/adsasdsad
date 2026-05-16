import cv2
from insightface.app import FaceAnalysis
from config import MODEL_NAME,CAMERA_INDEX
from src.database import save_persona

def register_person():
    print("[INFO] Cargando modelo InsightFace...")
    app = FaceAnalysis(name=MODEL_NAME, providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    nombre = input("Ingresa el nombre de la persona: ").strip()
    if not nombre:
        print("[ERROR] El nombre no puede estar vacío")
        return

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara")
        return

    print(f"[INFO] Registrando a: {nombre}")
    print("[INFO] Presiona ESPACIO para capturar foto, Q para salir")

    embeddings = []
    fotos_tomadas = 0
    FOTOS_NECESARIAS = 5

    while fotos_tomadas < FOTOS_NECESARIAS:
        ret, frame = cap.read()
        if not ret:
            break

        # Mostrar contador en pantalla
        cv2.putText(frame, f"Fotos: {fotos_tomadas}/{FOTOS_NECESARIAS}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "ESPACIO: capturar | Q: salir",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Registro de persona", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("[INFO] Registro cancelado")
            break

        if key == ord(" "):
            faces = app.get(frame)

            if len(faces) == 0:
                print("[AVISO] No se detectó cara, intenta de nuevo")
                continue

            embeddings.append(faces[0].embedding)
            fotos_tomadas += 1
            print(f"[OK] Foto {fotos_tomadas}/{FOTOS_NECESARIAS} capturada")

    cap.release()
    cv2.destroyAllWindows()

    if fotos_tomadas == FOTOS_NECESARIAS:
        import numpy as np
        embedding_promedio = np.mean(embeddings, axis=0)
        save_persona(nombre, embedding_promedio)
        print(f"[OK] {nombre} registrado exitosamente en la base de datos")
    else:
        print("[ERROR] Registro incompleto, no se guardó nada")

if __name__ == "__main__":
    register_person()