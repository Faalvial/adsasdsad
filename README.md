# Sistema de Control de Asistencia Automatizado

Este proyecto es una solución para el control de asistencia mediante reconocimiento facial en tiempo real. Está diseñado con una arquitectura cliente-servidor que separa claramente la interfaz de usuario del procesamiento biométrico y la base de datos.

## Arquitectura del Proyecto

El sistema está dividido en dos módulos principales, cada uno con su propia configuración y control de versiones (`.gitignore`):

- **`backend/`**: API REST construida en Python. Maneja la conexión a cámaras IP, el procesamiento de reconocimiento facial usando redes neuronales y la gestión de la base de datos PostgreSQL.
- **`frontend/`**: Interfaz de usuario interactiva construida con React y Vite.

---

## Requisitos Previos

Antes de iniciar, asegúrate de tener instalados:

- Python 3.x
- Node.js y npm
- PostgreSQL

---

## Guía de Instalación y Despliegue

### 1. Configuración de la Base de Datos

Es necesario crear la base de datos y conectarla al backend antes de iniciar el sistema.

1. Crea una base de datos en PostgreSQL.
2. Ejecuta el script `schema.sql` para inicializar las tablas necesarias.
3. Verifica que las credenciales en `backend/config.py` coincidan con tu configuración local.

---

### 2. Despliegue del Backend

Se recomienda utilizar un entorno virtual para aislar las dependencias del proyecto.

```bash
# Navegar a la carpeta del backend
cd backend

# Crear y activar el entorno virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# Crear y activar el entorno virtual (Ubuntu)
python3 -m venv .venv
source .venv/bin/activate


# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor API
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

#### Dependencias principales

- opencv-python
- insightface
- numpy
- onnxruntime
- psycopg2
- fastapi
- uvicorn

---

### 3. Despliegue del Frontend

Abre una nueva terminal para levantar la interfaz gráfica.

```bash
# Navegar a la carpeta del frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar el servidor de desarrollo
npm run dev -- --host
```

---

## Notas para el Control de Versiones (Git)

Para mantener el repositorio limpio y profesional:

### Backend

Asegúrate de incluir en `backend/.gitignore`:

```gitignore
.venv/
__pycache__/
*.pyc
```

### Frontend

Asegúrate de incluir en `frontend/.gitignore`:

```gitignore
node_modules/
dist/
```

---

## Tecnologías Utilizadas

### Backend

- Python
- FastAPI
- Uvicorn
- InsightFace
- OpenCV
- PostgreSQL

### Frontend

- React
- Vite
- JavaScript

---

## Objetivo del Proyecto

El sistema busca automatizar el registro de asistencia mediante reconocimiento facial en tiempo real, ofreciendo una solución moderna, escalable y desacoplada entre frontend y backend.

