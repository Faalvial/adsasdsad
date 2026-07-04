-- ==============================================================================
-- SCRIPT MAESTRO DE BASE DE DATOS - TECH LAB (POSTGRESQL)
-- Ejecutar conectado inicialmente como superusuario (ej. postgres)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- PARTE 1: CREACIÓN DE USUARIO Y BASE DE DATOS
-- ------------------------------------------------------------------------------
-- CREATE USER asistencia_user WITH PASSWORD 'admin123';
-- CREATE DATABASE control_asistencia OWNER asistencia_user;

-- Cambiar a la nueva base de datos (Comando exclusivo de la terminal psql)
-- \c control_asistencia


-- ------------------------------------------------------------------------------
-- PARTE 2: CREACIÓN DE ESTRUCTURA (ESQUEMA)
-- ------------------------------------------------------------------------------

-- 1. Tabla para los proyectos del Tech Lab
CREATE TABLE proyectos (
    id SERIAL PRIMARY KEY,
    nombre_proyecto VARCHAR(150) UNIQUE NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado_activo BOOLEAN DEFAULT TRUE
);

-- 2. Tabla para alumnos (personas)
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    dni VARCHAR(15) UNIQUE NOT NULL,
    codigo_alumno VARCHAR(50) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE SET NULL,
    embedding BYTEA NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado_activo BOOLEAN DEFAULT TRUE
);

-- 3. Tabla para el historial de asistencia
CREATE TABLE asistencia (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL, -- 'entrada' o 'salida'
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Índices para optimizar la velocidad de búsqueda
CREATE INDEX idx_dni ON personas(dni);
CREATE INDEX idx_codigo_alumno ON personas(codigo_alumno);
CREATE INDEX idx_persona_proyecto ON personas(proyecto_id);
CREATE INDEX idx_asistencia_persona ON asistencia(persona_id);
CREATE INDEX idx_asistencia_fecha ON asistencia(fecha_hora);


-- ------------------------------------------------------------------------------
-- PARTE 3: ASIGNACIÓN DE PERMISOS (PRINCIPIO DE MÍNIMO PRIVILEGIO)
-- ------------------------------------------------------------------------------

-- Permitir conexión a la base de datos y uso del esquema público
GRANT CONNECT ON DATABASE control_asistencia TO asistencia_user;
GRANT USAGE ON SCHEMA public TO asistencia_user;

-- Permisos de manipulación de datos sobre tablas
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE proyectos TO asistencia_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE personas TO asistencia_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE asistencia TO asistencia_user;

-- Permisos sobre las secuencias SERIAL (Vitales para el auto-incremento de IDs)
GRANT USAGE, SELECT ON SEQUENCE proyectos_id_seq TO asistencia_user;
GRANT USAGE, SELECT ON SEQUENCE personas_id_seq TO asistencia_user;
GRANT USAGE, SELECT ON SEQUENCE asistencia_id_seq TO asistencia_user;