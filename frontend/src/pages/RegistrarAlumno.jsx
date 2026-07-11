import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom"; // <-- NUEVO IMPORT

export default function RegistrarAlumno() {
  const navigate = useNavigate(); // <-- NUEVO: Para la redirección
  const temporizadorRef = useRef(null); // <-- NUEVO: Referencia para el reloj

  const [proyectos, setProyectos] = useState([]);
  const [formData, setFormData] = useState({ dni: "", codigo_alumno: "", nombres: "", apellidos: "", proyecto_id: "" });
  const [imagenes, setImagenes] = useState([]);
  const [estado, setEstado] = useState({ loading: false, error: null, success: null });

  const [mostrarFormProyecto, setMostrarFormProyecto] = useState(false);
  const [nuevoProyecto, setNuevoProyecto] = useState({ nombre_proyecto: "", descripcion: "" });
  const [estadoProyecto, setEstadoProyecto] = useState({ loading: false, error: null });
  const [streamUrl] = useState(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/video_feed?t=${Date.now()}`);

  const imgStreamRef = useRef(null);
  const canvasRef = useRef(null);

  // ------------------------------------------------------------------
  // NUEVO BLOQUE: LÓGICA DE INACTIVIDAD (5 MINUTOS)
  // ------------------------------------------------------------------
  const reiniciarTemporizador = () => {
    if (temporizadorRef.current) clearTimeout(temporizadorRef.current);
    
    temporizadorRef.current = setTimeout(() => {
      alert("Tiempo de inactividad de 5 minutos alcanzado. Volviendo al inicio para liberar la cámara.");
      navigate('/'); // Redirige al inicio
    }, 5 * 60 * 1000); // 5 minutos en milisegundos
  };

  useEffect(() => {
    // 1. Iniciar el reloj al entrar
    reiniciarTemporizador();

    // 2. Escuchar actividad del usuario
    window.addEventListener('mousemove', reiniciarTemporizador);
    window.addEventListener('mousedown', reiniciarTemporizador);
    window.addEventListener('keydown', reiniciarTemporizador);

    // 3. Limpiar oyentes si el usuario sale manualmente
    return () => {
      if (temporizadorRef.current) clearTimeout(temporizadorRef.current);
      window.removeEventListener('mousemove', reiniciarTemporizador);
      window.removeEventListener('mousedown', reiniciarTemporizador);
      window.removeEventListener('keydown', reiniciarTemporizador);
    };
  }, []);
  // ------------------------------------------------------------------


  useEffect(() => {
      const apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

      // 1. Al entrar a la pestaña: Se activa el candado en el backend
      fetch(`${apiBaseUrl}/api/v1/sistema/registro/iniciar`, { method: "POST" })
        .catch(err => console.error("Error al inicializar el candado lógico:", err));

      const imgElement = imgStreamRef.current;
      
      return () => { 
        // 2. Limpieza de memoria RAM
        if (imgElement) imgElement.src = ""; 

        // 3. Al salir de la pestaña: Se libera el candado en el backend
        fetch(`${apiBaseUrl}/api/v1/sistema/registro/finalizar`, { method: "POST" })
          .catch(err => console.error("Error al liberar el candado lógico:", err));
      };
    }, []);

  const cargarProyectos = async () => {
    try {
      const res = await fetch(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/proyectos`);
      const data = await res.json();
      if (data.status === "ok") setProyectos(data.data);
    } catch (err) { console.error("Error cargando proyectos:", err); }
  };

  useEffect(() => { cargarProyectos(); }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
  const handleChangeProyecto = (e) => setNuevoProyecto({ ...nuevoProyecto, [e.target.name]: e.target.value });

  const handleCrearProyecto = async (e) => {
    e.preventDefault();
    setEstadoProyecto({ loading: true, error: null });
    try {
      const res = await fetch(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/proyectos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nuevoProyecto)
      });
      const data = await res.json();

      if (res.ok) {
        await cargarProyectos();
        setFormData({ ...formData, proyecto_id: data.proyecto_id.toString() });
        setMostrarFormProyecto(false);
        setNuevoProyecto({ nombre_proyecto: "", descripcion: "" });
        setEstadoProyecto({ loading: false, error: null });
      } else {
        setEstadoProyecto({ loading: false, error: data.detail || "Error al crear proyecto" });
      }
    } catch (err) {
      setEstadoProyecto({ loading: false, error: "Error de red" });
    }
  };

  const capturarFoto = (e) => {
    e.preventDefault();
    if (imagenes.length >= 5) return;
    const imgElement = imgStreamRef.current;
    const canvas = canvasRef.current;
    if (imgElement && canvas) {
      const context = canvas.getContext("2d");
      canvas.width = imgElement.naturalWidth || 640;
      canvas.height = imgElement.naturalHeight || 480;
      context.drawImage(imgElement, 0, 0, canvas.width, canvas.height);
      const imageData = canvas.toDataURL("image/jpeg", 0.9);
      setImagenes(prev => [...prev, imageData]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (imagenes.length !== 5) {
      setEstado({ loading: false, error: "Faltan fotos. Deben ser exactamente 5.", success: null });
      return;
    }
    setEstado({ loading: true, error: null, success: null });

    try {
      const payload = {
        ...formData,
        proyecto_id: formData.proyecto_id ? parseInt(formData.proyecto_id) : null,
        imagenes: imagenes
      };

      const res = await fetch(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/personas/registrar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        setEstado({ loading: false, error: null, success: data.mensaje });
        // Limpiar el DNI también al terminar el registro
        setFormData({ dni: "", codigo_alumno: "", nombres: "", apellidos: "", proyecto_id: "" });
        setImagenes([]);
      } else {
        setEstado({ loading: false, error: data.detail || "Error en el servidor", success: null });
      }
    } catch (err) {
      setEstado({ loading: false, error: "Error de red al conectar con el servidor.", success: null });
    }
  };

  return (
    <div>
      <h2 style={{ color: "#1e293b", marginBottom: "25px" }}>Registrar Nuevo Alumno</h2>

      {estado.error && <div style={{ padding: "12px 15px", backgroundColor: "#fef2f2", color: "#dc2626", marginBottom: "20px", borderRadius: "6px", border: "1px solid #f87171", fontWeight: "500" }}>{estado.error}</div>}
      {estado.success && <div style={{ padding: "12px 15px", backgroundColor: "#ecfdf5", color: "#059669", marginBottom: "20px", borderRadius: "6px", border: "1px solid #34d399", fontWeight: "500" }}>{estado.success}</div>}

      <div style={{ display: "flex", gap: "25px", flexWrap: "wrap", alignItems: "flex-start" }}>

        {/* TARJETA IZQUIERDA: FORMULARIO */}
        <div style={{ flex: "1", minWidth: "300px", backgroundColor: "#ffffff", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", padding: "25px" }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>

            {/* NUEVO CAMPO: DNI */}
            <div>
              <label style={labelStyle}>DNI</label>
              <input type="text" name="dni" maxLength="8" value={formData.dni} onChange={handleChange} required style={inputStyle} />
            </div>

            <div>
              <label style={labelStyle}>Código de Alumno</label>
              <input type="text" name="codigo_alumno" value={formData.codigo_alumno} onChange={handleChange} required style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Nombres</label>
              <input type="text" name="nombres" value={formData.nombres} onChange={handleChange} required style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Apellidos</label>
              <input type="text" name="apellidos" value={formData.apellidos} onChange={handleChange} required style={inputStyle} />
            </div>

            <div style={{ padding: "18px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <label style={labelStyle}>Proyecto Asignado</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
                <select name="proyecto_id" value={formData.proyecto_id} onChange={handleChange} style={{ ...inputStyle, flex: 1, cursor: "pointer" }}>
                  <option value="">-- Seleccionar Proyecto --</option>
                  {proyectos.map(p => (
                    <option key={p.id} value={p.id}>{p.nombre_proyecto}</option>
                  ))}
                </select>
                <button type="button" onClick={() => setMostrarFormProyecto(!mostrarFormProyecto)} style={btnLightStyle}>
                  {mostrarFormProyecto ? "Cancelar" : "+ Nuevo"}
                </button>
              </div>

              {mostrarFormProyecto && (
                <div style={{ padding: "15px", backgroundColor: "#ffffff", borderRadius: "6px", border: "1px dashed #cbd5e1", marginTop: "15px" }}>
                  <h4 style={{ margin: "0 0 12px 0", color: "#334155" }}>Crear Nuevo Proyecto</h4>
                  {estadoProyecto.error && <p style={{ color: "#dc2626", fontSize: "0.85em", margin: "0 0 10px 0" }}>{estadoProyecto.error}</p>}
                  <input type="text" name="nombre_proyecto" placeholder="Nombre del proyecto..." value={nuevoProyecto.nombre_proyecto} onChange={handleChangeProyecto} style={{ ...inputStyle, marginBottom: "12px" }} />
                  <input type="text" name="descripcion" placeholder="Breve descripción..." value={nuevoProyecto.descripcion} onChange={handleChangeProyecto} style={{ ...inputStyle, marginBottom: "12px" }} />
                  <button type="button" onClick={handleCrearProyecto} disabled={!nuevoProyecto.nombre_proyecto || estadoProyecto.loading} style={{ ...btnPrimaryStyle, backgroundColor: "#0f172a", width: "100%" }}>
                    {estadoProyecto.loading ? "Guardando..." : "Guardar Proyecto"}
                  </button>
                </div>
              )}
            </div>

            <button type="submit" disabled={estado.loading || imagenes.length !== 5} style={{ ...btnPrimaryStyle, backgroundColor: (imagenes.length === 5 && !estado.loading) ? "#0284c7" : "#cbd5e1", cursor: (imagenes.length === 5 && !estado.loading) ? "pointer" : "not-allowed", marginTop: "15px", padding: "16px", fontSize: "1.05em" }}>
              {estado.loading ? "Procesando Biometría IA..." : "Completar Registro de Alumno"}
            </button>
          </form>
        </div>

        {/* TARJETA DERECHA: BIOMETRÍA */}
        <div style={{ flex: "1", minWidth: "350px", textAlign: "center", backgroundColor: "#ffffff", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", padding: "25px" }}>
          <h3 style={{ marginTop: 0, color: "#1e293b", fontSize: "1.2rem", marginBottom: "20px" }}>Captura Biométrica ({imagenes.length}/5)</h3>

          <img
            ref={imgStreamRef}
            src={streamUrl}
            crossOrigin="anonymous"
            alt="Stream de Cámara"
            style={{ width: "100%", borderRadius: "8px", backgroundColor: "#000", marginBottom: "20px" }}
          />
          <canvas ref={canvasRef} style={{ display: "none" }} />

          <div style={{ display: "flex", gap: "10px", justifyContent: "center", marginBottom: "20px" }}>
            <button onClick={capturarFoto} disabled={imagenes.length >= 5} style={{ ...btnPrimaryStyle, backgroundColor: "#213547", color: "white", opacity: imagenes.length >= 5 ? 0.6 : 1 }}>
              Capturar Foto
            </button>
            <button onClick={(e) => { e.preventDefault(); setImagenes([]); }} style={btnLightStyle}>
              Reiniciar
            </button>
          </div>

          <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
            {imagenes.map((imgSrc, idx) => (
              <img key={idx} src={imgSrc} alt={`Captura ${idx + 1}`} style={{ width: "65px", height: "65px", objectFit: "cover", borderRadius: "6px", border: "2px solid #0284c7" }} />
            ))}
            {[...Array(5 - imagenes.length)].map((_, idx) => (
              <div key={`empty-${idx}`} style={{ width: "65px", height: "65px", backgroundColor: "#f1f5f9", borderRadius: "6px", border: "2px dashed #cbd5e1" }} />
            ))}
          </div>
          <p style={{ fontSize: "0.85em", color: "#64748b", marginTop: "20px", textAlign: "left", lineHeight: "1.5", padding: "15px", backgroundColor: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <strong style={{ color: "#334155" }}>Instrucciones:</strong> Se requieren 5 tomas para construir el vector facial.<br/>
            1. Mirando al frente. 2. Izquierda. 3. Derecha. 4. Arriba. 5. Abajo.
          </p>
        </div>

      </div>
    </div>
  );
}

/* Estilos extraídos para limpieza */
const inputStyle = { padding: "12px", borderRadius: "6px", border: "1px solid #cbd5e1", width: "100%", boxSizing: "border-box", color: "#334155", outline: "none", fontSize: "0.95rem" };
const labelStyle = { fontWeight: "600", display: "block", marginBottom: "8px", color: "#475569", fontSize: "0.9rem" };
const btnPrimaryStyle = { padding: "12px 18px", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600", transition: "all 0.2s" };
const btnLightStyle = { padding: "12px 18px", backgroundColor: "#f1f5f9", color: "#475569", border: "1px solid #cbd5e1", borderRadius: "6px", cursor: "pointer", fontWeight: "600", transition: "all 0.2s" };