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


def save_persona(dni, codigo_alumno, nombres, apellidos, proyecto_id, embedding):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        emb_bytes = embedding.astype(np.float32).tobytes()
        cursor.execute(
            """
            INSERT INTO personas (dni, codigo_alumno, nombres, apellidos, proyecto_id, embedding) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (dni, codigo_alumno, nombres, apellidos, proyecto_id, psycopg2.Binary(emb_bytes))
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


def save_asistencia(persona_id, tipo, fecha_hora=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if fecha_hora:
            cursor.execute(
                "INSERT INTO asistencia (persona_id, tipo, fecha_hora) VALUES (%s, %s, %s)",
                (persona_id, tipo, fecha_hora)
            )
        else:
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
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT tipo, fecha_hora
            FROM asistencia 
            WHERE persona_id = %s 
            ORDER BY id DESC 
            LIMIT 1
        """
        cursor.execute(query, (persona_id,))
        row = cursor.fetchone()
        if row:
            return {"tipo": row[0], "fecha_hora": row[1]}
        return None
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al obtener último estado: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_historial_asistencia(limite=50, texto_busqueda=None, fecha=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # El corazón de la consulta: Emparejamos eventos con Window Functions (LEAD)
        query = """
                    WITH eventos_emparejados AS (
                        SELECT 
                            a.id,
                            p.dni,
                            p.codigo_alumno,
                            p.nombres || ' ' || p.apellidos AS nombre_completo,
                            COALESCE(pr.nombre_proyecto, 'Sin proyecto') AS proyecto,
                            a.tipo,
                            a.fecha_hora AS entrada_hora,
                            LEAD(a.tipo) OVER (PARTITION BY a.persona_id ORDER BY a.fecha_hora) AS siguiente_tipo,
                            LEAD(a.fecha_hora) OVER (PARTITION BY a.persona_id ORDER BY a.fecha_hora) AS salida_hora
                        FROM asistencia a
                        JOIN personas p ON a.persona_id = p.id
                        LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
                    ),
                    pares_filtrados AS (
                        SELECT 
                            id, dni, codigo_alumno, nombre_completo, proyecto, entrada_hora,
                            CASE WHEN siguiente_tipo = 'salida' THEN salida_hora ELSE NULL END AS salida_hora
                        FROM eventos_emparejados
                        WHERE tipo = 'entrada'
                    )
                    SELECT * FROM pares_filtrados WHERE 1=1
                """
        params = []

        # Los filtros se aplican DESPUÉS de emparejar, para no romper las parejas
        if texto_busqueda:
            query += " AND (codigo_alumno ILIKE %s OR nombre_completo ILIKE %s)"
            params.extend([f"%{texto_busqueda}%", f"%{texto_busqueda}%"])

        if fecha:
            # Asume que el filtro de fecha de React envía formato 'YYYY-MM-DD'
            query += " AND DATE(entrada_hora) = %s"
            params.append(fecha)

        query += " ORDER BY entrada_hora DESC LIMIT %s"
        params.append(limite)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        resultados = []
        for row in rows:
            formato = "%d/%m/%Y, %I:%M:%S %p"
            resultados.append({
                "id": row[0],
                "dni": row[1] if row[1] else "---",
                "codigo": row[2],
                "nombre_completo": row[3],
                "proyecto": row[4],
                "entrada": row[5].strftime(formato) if row[5] else "---",
                "salida": row[6].strftime(formato) if row[6] else "Aún en laboratorio..."
            })

        return resultados

    except Exception as e:
        print(f"[ERROR BD] {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def update_proyecto(proyecto_id, nombre_proyecto, descripcion=""):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE proyectos SET nombre_proyecto = %s, descripcion = %s WHERE id = %s",
            (nombre_proyecto, descripcion, proyecto_id)
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al actualizar proyecto: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def delete_proyecto(proyecto_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proyectos WHERE id = %s", (proyecto_id,))
        conn.commit()
        return True
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al eliminar proyecto: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_personas_info():
    conn = None
    cursor = None
    personas = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT p.id, p.dni, p.codigo_alumno, p.nombres, p.apellidos, 
                   p.proyecto_id, pr.nombre_proyecto, p.estado_activo
            FROM personas p
            LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
            ORDER BY p.id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            personas.append({
                "id": row[0],
                "dni": row[1],
                "codigo_alumno": row[2],
                "nombres": row[3],
                "apellidos": row[4],
                "proyecto_id": row[5],
                "proyecto_nombre": row[6],
                "estado_activo": row[7]
            })
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al listar personas: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return personas


def update_persona(persona_id, dni, codigo_alumno, nombres, apellidos, proyecto_id, estado_activo):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE personas 
            SET dni = %s, codigo_alumno = %s, nombres = %s, apellidos = %s, 
                proyecto_id = %s, estado_activo = %s
            WHERE id = %s
            """,
            (dni, codigo_alumno, nombres, apellidos, proyecto_id, estado_activo, persona_id)
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al actualizar persona: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def delete_persona(persona_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
        conn.commit()
        return True
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"[ERROR BD] Error al eliminar persona: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_personas_en_laboratorio():
    conn = None
    cursor = None
    en_lab = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            WITH ultimo_evento AS (
                SELECT persona_id, tipo, fecha_hora,
                       ROW_NUMBER() OVER (PARTITION BY persona_id ORDER BY fecha_hora DESC) as rn
                FROM asistencia
            )
            SELECT p.dni, p.codigo_alumno, p.nombres, p.apellidos, 
                   COALESCE(pr.nombre_proyecto, 'Sin proyecto') AS proyecto, 
                   ue.fecha_hora
            FROM ultimo_evento ue
            JOIN personas p ON ue.persona_id = p.id
            LEFT JOIN proyectos pr ON p.proyecto_id = pr.id
            WHERE ue.rn = 1 AND ue.tipo = 'entrada'
            ORDER BY ue.fecha_hora DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            formato = "%d/%m/%Y, %I:%M:%S %p"
            en_lab.append({
                "dni": row[0],
                "codigo_alumno": row[1],
                "nombres": row[2],
                "apellidos": row[3],
                "proyecto": row[4],
                "hora_entrada": row[5].strftime(formato) if row[5] else "---"
            })
    except psycopg2.Error as e:
        print(f"[ERROR BD] Error al buscar personas en el laboratorio: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
