-- 1. Crear la base de datos (ejecutar por separado si es necesario)
-- CREATE DATABASE control_asistencia;

-- 2. Tabla para almacenar a los usuarios registrados
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    embedding BYTEA NOT NULL, -- Almacena el array de numpy como binario
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla para el historial de asistencia
CREATE TABLE asistencia (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL, -- 'entrada' o 'salida'
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Opcional: Índice para búsquedas rápidas por nombre
CREATE INDEX idx_nombre_persona ON personas(nombre);