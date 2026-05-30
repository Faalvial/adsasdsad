import psycopg2
import numpy as np
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def get_proyectos():
    conn = None
    cursor = None
    proyectos = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_proyecto, descripcion FROM proyectos ORDER BY id DESC")
        rows = cursor.fetchall()
        for row in rows:
            proyectos.append({
                "id": row[0],
                "nombre_proyecto": row[1],
                "descripcion": row[2]
            })
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al cargar proyectos: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return proyectos


def save_proyecto(nombre_proyecto, descripcion=""):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO proyectos (nombre_proyecto, descripcion) VALUES (%s, %s) RETURNING id",
            (nombre_proyecto, descripcion)
        )
        proyecto_id = cursor.fetchone()[0]
        conn.commit()
        return proyecto_id
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al crear proyecto: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def load_embeddings():
    conn = None
    cursor = None
    registered = {}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_alumno, embedding FROM personas")
        rows = cursor.fetchall()
        for codigo_alumno, emb_bytes in rows:
            embedding = np.frombuffer(bytes(emb_bytes), dtype=np.float32)
            registered[codigo_alumno] = embedding
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al cargar embeddings: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return registered


def save_persona(codigo_alumno, nombres, apellidos, proyecto_id, embedding):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        emb_bytes = embedding.astype(np.float32).tobytes()
        cursor.execute(
            """
            INSERT INTO personas (codigo_alumno, nombres, apellidos, proyecto_id, embedding) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (codigo_alumno, nombres, apellidos, proyecto_id, psycopg2.Binary(emb_bytes))
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al guardar a la persona: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_persona_id(codigo_alumno):
    conn = None
    cursor = None
    persona_id = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM personas WHERE codigo_alumno = %s", (codigo_alumno,))
        row = cursor.fetchone()
        if row:
            persona_id = row[0]
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al obtener el ID: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return persona_id


def save_asistencia(persona_id, tipo):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO asistencia (persona_id, tipo) VALUES (%s, %s)",
            (persona_id, tipo)
        )
        conn.commit()
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al registrar asistencia: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_ultimo_estado_asistencia(persona_id):
    conn = None
    cursor = None
    ultimo_tipo = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT tipo 
            FROM asistencia 
            WHERE persona_id = %s 
            ORDER BY id DESC 
            LIMIT 1
        """
        cursor.execute(query, (persona_id,))
        row = cursor.fetchone()
        if row:
            ultimo_tipo = row[0]
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al obtener último estado: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return ultimo_tipo


def get_historial_asistencia(limite=50, texto_busqueda=None, fecha=None):
    conn = None
    cursor = None
    historial = []
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT a.id, p.codigo_alumno, p.nombres, p.apellidos, pr.nombre_proyecto, a.tipo, a.fecha_hora
            FROM asistencia a
            JOIN personas p ON a.persona_id = p.id
            LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
        """
        condiciones = []
        parametros = []

        if texto_busqueda:
            condiciones.append("(p.nombres ILIKE %s OR p.apellidos ILIKE %s OR p.codigo_alumno ILIKE %s)")
            parametros.extend([f"%{texto_busqueda}%", f"%{texto_busqueda}%", f"%{texto_busqueda}%"])

        if fecha:
            condiciones.append("DATE(a.fecha_hora) = %s")
            parametros.append(fecha)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        query += " ORDER BY a.fecha_hora DESC LIMIT %s"
        parametros.append(limite)

        cursor.execute(query, tuple(parametros))
        rows = cursor.fetchall()

        for row in rows:
            historial.append({
                "registro_id": row[0],
                "codigo_alumno": row[1],
                "nombre_completo": f"{row[2]} {row[3]}",
                "proyecto": row[4] or "Sin proyecto",
                "tipo": row[5],
                "fecha_hora": row[6].isoformat()
            })
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al obtener el historial filtrado: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return historial