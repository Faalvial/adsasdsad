import cv2
import numpy as np


def draw_result(frame, bbox, name: str, score: float):
    """
    Dibuja el recuadro y el nombre sobre el frame.
    Verde si fue reconocido, rojo si es desconocido.
    Ajusta dinámicamente la posición del texto si sale del frame.
    """
    x1, y1, x2, y2 = bbox.astype(int)
    is_known = name != "Desconocido"

    color = (0, 200, 0) if is_known else (0, 0, 220)
    label = f"{name} ({score:.2f})" if is_known else "Desconocido"

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Calcular tamaño del texto
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)

    # Lógica para evitar que el texto salga por arriba
    margen = 10
    if y1 - text_h - margen < 0:
        # Si no hay espacio arriba, lo ponemos dentro del recuadro, abajo de la línea superior
        text_y_bg_start = y1
        text_y_bg_end = y1 + text_h + margen
        text_y_pos = y1 + text_h + (margen // 2)
    else:
        # Comportamiento normal (arriba del recuadro)
        text_y_bg_start = y1 - text_h - margen
        text_y_bg_end = y1
        text_y_pos = y1 - 6

    # Dibujar fondo y texto con las coordenadas seguras
    cv2.rectangle(frame, (x1, text_y_bg_start), (x1 + text_w, text_y_bg_end), color, -1)
    cv2.putText(frame, label, (x1, text_y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)