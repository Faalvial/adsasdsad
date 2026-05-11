import psycopg2
import numpy as np
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_connection():
    """Crea y devuelve una conexión a PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def load_embeddings():
    """
    Carga todos los embeddings registrados desde la BD.
    Devuelve un diccionario {nombre: embedding}.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nombre, embedding FROM personas")
    rows = cursor.fetchall()
    
    registered = {}
    for nombre, emb_bytes in rows:
        embedding = np.frombuffer(bytes(emb_bytes), dtype=np.float32)
        registered[nombre] = embedding
    
    cursor.close()
    conn.close()
    
    return registered

def save_persona(nombre, embedding):
    """Guarda una persona nueva con su embedding en la BD."""
    conn = get_connection()
    cursor = conn.cursor()
    
    emb_bytes = embedding.astype(np.float32).tobytes()
    
    cursor.execute(
        "INSERT INTO personas (nombre, embedding) VALUES (%s, %s)",
        (nombre, psycopg2.Binary(emb_bytes))
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[OK] {nombre} guardado en la base de datos")

def save_asistencia(persona_id, tipo):
    """Registra una entrada o salida en la BD."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO asistencia (persona_id, tipo) VALUES (%s, %s)",
        (persona_id, tipo)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def get_persona_id(nombre):
    """Obtiene el id de una persona por su nombre."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM personas WHERE nombre = %s", (nombre,))
    row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return row[0] if row else None