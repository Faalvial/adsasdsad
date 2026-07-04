# Threshold y otras configuraciones
RECONNECT_DELAY = 5  #segundos entre intentos de reconexión
THRESHOLD = 0.5 #umbral 
DET_THRESHOLD = 0.7
MODEL_NAME = "buffalo_sc"
CAMERA_INDEX = "rtsp://admin:Hik12345@172.16.9.114:554/Streaming/Channels/101"
SKIP_FRAMES = 5
COOLDOWN = 15

import os

# PostgreSQL
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "control_asistencia")
DB_USER = os.environ.get("DB_USER", "asistencia_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "admin123")