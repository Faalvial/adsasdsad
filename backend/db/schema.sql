-- 1. Tabla para los proyectos del Tech Lab
CREATE TABLE proyectos (
    id SERIAL PRIMARY KEY,
    nombre_proyecto VARCHAR(150) UNIQUE NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla modificada para alumnos (personas)
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    codigo_alumno VARCHAR(50) UNIQUE NOT NULL, -- Identificador único indispensable
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE SET NULL, -- Relación con proyectos
    embedding BYTEA NOT NULL, -- Vector de características promediado (5 fotos)
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla para el historial de asistencia
CREATE TABLE asistencia (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL, -- 'entrada' o 'salida'
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar la velocidad de los filtros y búsquedas en tiempo real
CREATE INDEX idx_codigo_alumno ON personas(codigo_alumno);
CREATE INDEX idx_persona_proyecto ON personas(proyecto_id);
CREATE INDEX idx_asistencia_persona ON asistencia(persona_id);
CREATE INDEX idx_asistencia_fecha ON asistencia(fecha_hora);