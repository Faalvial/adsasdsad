# Manejo de la cámara con OpenCV
import cv2
import numpy as np

def draw_result(frame, bbox, name: str, score: float):
    """
    Dibuja el recuadro y el nombre sobre el frame.
    Verde si fue reconocido, rojo si es desconocido.
    """
    x1, y1, x2, y2 = bbox.astype(int)
    is_known = name != "Desconocido"

    color = (0, 200, 0) if is_known else (0, 0, 220)
    label = f"{name} ({score:.2f})" if is_known else "Desconocido"

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Fondo del texto
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1)

    # Texto
    cv2.putText(frame, label, (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)