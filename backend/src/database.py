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
    conn = None
    cursor = None
    registered = {}
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT nombre, embedding FROM personas")
        rows = cursor.fetchall()

        for nombre, emb_bytes in rows:
            embedding = np.frombuffer(bytes(emb_bytes), dtype=np.float32)
            registered[nombre] = embedding

    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al cargar embeddings: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return registered


def save_persona(nombre, embedding):
    """Guarda una persona nueva con su embedding en la BD."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        emb_bytes = embedding.astype(np.float32).tobytes()

        cursor.execute(
            "INSERT INTO personas (nombre, embedding) VALUES (%s, %s)",
            (nombre, psycopg2.Binary(emb_bytes))
        )

        conn.commit()
        print(f"[OK] {nombre} guardado en la base de datos")
    except psycopg2.Error as e:
        if conn: conn.rollback()  # Deshace los cambios si hay error
        print(f"[ERROR BD] No se pudo guardar a la persona {nombre}: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def save_asistencia(persona_id, tipo):
    """Registra una entrada o salida en la BD."""
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
        print(f"[ERROR BD] No se pudo registrar la asistencia: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_persona_id(nombre):
    """Obtiene el id de una persona por su nombre."""
    conn = None
    cursor = None
    persona_id = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM personas WHERE nombre = %s", (nombre,))
        row = cursor.fetchone()
        if row:
            persona_id = row[0]

    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al obtener el ID de {nombre}: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return persona_id


def get_ultimo_estado_asistencia(persona_id):
    """
    Obtiene el tipo del último registro ('entrada' o 'salida')
    de una persona basado estrictamente en el último ID insertado.
    """
    conn = None
    cursor = None
    ultimo_tipo = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Al ordenar por id DESC, evitamos cualquier bug de zona horaria o medianoche
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
        print(f"[ERROR BD] Error al obtener el último estado: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return ultimo_tipo


def get_historial_asistencia(limite=50, nombre=None, fecha=None):
    """
    Obtiene el historial de asistencia con filtros opcionales por nombre y fecha.
    - fecha: Debe venir en formato cadena 'YYYY-MM-DD'
    """
    conn = None
    cursor = None
    historial = []
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Consulta base
        query = """
            SELECT a.id, p.nombre, a.tipo, a.fecha_hora
            FROM asistencia a
            JOIN personas p ON a.persona_id = p.id
        """

        condiciones = []
        parametros = []

        # Filtro por nombre (búsqueda parcial e insensible a mayúsculas/minúsculas)
        if nombre:
            condiciones.append("p.nombre ILIKE %s")
            parametros.append(f"%{nombre}%")

        # Filtro por fecha exacta (extrayendo solo la parte DATE del TIMESTAMP)
        if fecha:
            condiciones.append("DATE(a.fecha_hora) = %s")
            parametros.append(fecha)

        # Si existen filtros, los unimos con AND y los agregamos a la consulta
        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        # Ordenamiento y límite
        query += " ORDER BY a.fecha_hora DESC LIMIT %s"
        parametros.append(limite)

        cursor.execute(query, tuple(parametros))
        rows = cursor.fetchall()

        for row in rows:
            historial.append({
                "registro_id": row[0],
                "nombre": row[1],
                "tipo": row[2],
                "fecha_hora": row[3].isoformat()
            })

    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al obtener el historial filtrado: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return historial