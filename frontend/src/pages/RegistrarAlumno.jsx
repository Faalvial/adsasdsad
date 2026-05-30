import { useState, useEffect, useRef } from "react";

export default function RegistrarAlumno() {
  const [proyectos, setProyectos] = useState([]);
  const [formData, setFormData] = useState({
    codigo_alumno: "",
    nombres: "",
    apellidos: "",
    proyecto_id: ""
  });
  const [imagenes, setImagenes] = useState([]);
  const [estado, setEstado] = useState({ loading: false, error: null, success: null });

  const [mostrarFormProyecto, setMostrarFormProyecto] = useState(false);
  const [nuevoProyecto, setNuevoProyecto] = useState({ nombre_proyecto: "", descripcion: "" });
  const [estadoProyecto, setEstadoProyecto] = useState({ loading: false, error: null });
  const [streamUrl] = useState(`http://localhost:8000/api/v1/video_feed?t=${Date.now()}`);

  // Cambiamos el nombre de la referencia para que tenga sentido (ahora es una imagen, no un video)
  const imgStreamRef = useRef(null);
  // Agrega este bloque para APAGAR LA CÁMARA al cambiar de página
  useEffect(() => {
    const imgElement = imgStreamRef.current;
    return () => {
      // Cuando el componente se desmonta, vaciamos el src para abortar la petición HTTP
      if (imgElement) {
        imgElement.src = "";
      }
    };
  }, []);
  const canvasRef = useRef(null);

  const cargarProyectos = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/proyectos");
      const data = await res.json();
      if (data.status === "ok") setProyectos(data.data);
    } catch (err) {
      console.error("Error cargando proyectos:", err);
    }
  };

  useEffect(() => {
    cargarProyectos();
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
  const handleChangeProyecto = (e) => setNuevoProyecto({ ...nuevoProyecto, [e.target.name]: e.target.value });

  const handleCrearProyecto = async (e) => {
    e.preventDefault();
    setEstadoProyecto({ loading: true, error: null });
    try {
      const res = await fetch("http://localhost:8000/api/v1/proyectos", {
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

  // Lógica adaptada para capturar foto desde la etiqueta <img>
  const capturarFoto = (e) => {
    e.preventDefault();
    if (imagenes.length >= 5) return;

    const imgElement = imgStreamRef.current;
    const canvas = canvasRef.current;

    if (imgElement && canvas) {
      const context = canvas.getContext("2d");
      // Las imágenes usan naturalWidth/naturalHeight en lugar de videoWidth/videoHeight
      canvas.width = imgElement.naturalWidth || 640;
      canvas.height = imgElement.naturalHeight || 480;

      // Dibujamos el frame exacto que se está mostrando en la pantalla
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

      const res = await fetch("http://localhost:8000/api/v1/personas/registrar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        setEstado({ loading: false, error: null, success: data.mensaje });
        setFormData({ codigo_alumno: "", nombres: "", apellidos: "", proyecto_id: "" });
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
      <h2>Registrar Nuevo Alumno</h2>

      {estado.error && <div style={{ padding: "10px", backgroundColor: "#fce8e6", color: "#c5221f", marginBottom: "15px", borderRadius: "5px" }}>{estado.error}</div>}
      {estado.success && <div style={{ padding: "10px", backgroundColor: "#e6f4ea", color: "#137333", marginBottom: "15px", borderRadius: "5px" }}>{estado.success}</div>}

      <div style={{ display: "flex", gap: "30px", flexWrap: "wrap" }}>

        <div style={{ flex: "1", minWidth: "300px" }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
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

            <div style={{ padding: "15px", backgroundColor: "#f9f9f9", borderRadius: "8px", border: "1px solid #ddd" }}>
              <label style={labelStyle}>Proyecto Asignado</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
                <select name="proyecto_id" value={formData.proyecto_id} onChange={handleChange} style={{ ...inputStyle, flex: 1 }}>
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
                <div style={{ padding: "15px", backgroundColor: "#fff", borderRadius: "5px", border: "1px dashed #aaa" }}>
                  <h4 style={{ margin: "0 0 10px 0" }}>Crear Nuevo Proyecto</h4>
                  {estadoProyecto.error && <p style={{ color: "red", fontSize: "0.85em", margin: "0 0 10px 0" }}>{estadoProyecto.error}</p>}
                  <input type="text" name="nombre_proyecto" placeholder="Nombre del proyecto..." value={nuevoProyecto.nombre_proyecto} onChange={handleChangeProyecto} style={{ ...inputStyle, marginBottom: "10px" }} />
                  <input type="text" name="descripcion" placeholder="Breve descripción..." value={nuevoProyecto.descripcion} onChange={handleChangeProyecto} style={{ ...inputStyle, marginBottom: "10px" }} />
                  <button type="button" onClick={handleCrearProyecto} disabled={!nuevoProyecto.nombre_proyecto || estadoProyecto.loading} style={btnPrimaryStyle}>
                    {estadoProyecto.loading ? "Guardando..." : "Guardar Proyecto"}
                  </button>
                </div>
              )}
            </div>

            <button type="submit" disabled={estado.loading || imagenes.length !== 5} style={{ ...btnPrimaryStyle, backgroundColor: (imagenes.length === 5 && !estado.loading) ? "#1a73e8" : "#ccc", cursor: (imagenes.length === 5 && !estado.loading) ? "pointer" : "not-allowed", marginTop: "10px", padding: "15px", fontSize: "1.1em" }}>
              {estado.loading ? "Procesando Biometría IA..." : "Procesar y Guardar Alumno"}
            </button>
          </form>
        </div>

        <div style={{ flex: "1", minWidth: "350px", textAlign: "center", backgroundColor: "#f9f9f9", padding: "20px", borderRadius: "8px", border: "1px solid #ddd" }}>
          <h3 style={{ marginTop: 0 }}>Captura Biométrica RTSP ({imagenes.length}/5)</h3>

          {/* El cambio principal: ahora consumimos la cámara IP desde el backend mediante una imagen con crossOrigin */}
          <img
            ref={imgStreamRef}
            src={streamUrl}
            crossOrigin="anonymous"
            alt="Stream de Cámara"
            style={{ width: "100%", borderRadius: "8px", backgroundColor: "#000", marginBottom: "15px" }}
          />
          <canvas ref={canvasRef} style={{ display: "none" }} />

          <div style={{ display: "flex", gap: "10px", justifyContent: "center", marginBottom: "15px" }}>
            <button onClick={capturarFoto} disabled={imagenes.length >= 5} style={{ ...btnPrimaryStyle, backgroundColor: "#34a853", opacity: imagenes.length >= 5 ? 0.6 : 1 }}>
              Capturar Foto
            </button>
            <button onClick={(e) => { e.preventDefault(); setImagenes([]); }} style={{ ...btnPrimaryStyle, backgroundColor: "#ea4335" }}>
              Reiniciar
            </button>
          </div>

          <div style={{ display: "flex", gap: "8px", justifyContent: "center" }}>
            {imagenes.map((imgSrc, idx) => (
              <img key={idx} src={imgSrc} alt={`Captura ${idx + 1}`} style={{ width: "60px", height: "60px", objectFit: "cover", borderRadius: "4px", border: "2px solid #1a73e8" }} />
            ))}
            {[...Array(5 - imagenes.length)].map((_, idx) => (
              <div key={`empty-${idx}`} style={{ width: "60px", height: "60px", backgroundColor: "#eee", borderRadius: "4px", border: "2px dashed #ccc" }} />
            ))}
          </div>
          <p style={{ fontSize: "0.85em", color: "#666", marginTop: "15px", textAlign: "left" }}>
            <strong>Instrucciones:</strong> El sistema requiere 5 tomas para construir el vector facial.<br/>
            1. Mirando al frente. 2. Izquierda. 3. Derecha. 4. Arriba. 5. Abajo.
          </p>
        </div>

      </div>
    </div>
  );
}

const inputStyle = { padding: "10px", borderRadius: "4px", border: "1px solid #ccc", width: "100%", boxSizing: "border-box" };
const labelStyle = { fontWeight: "bold", display: "block", marginBottom: "5px" };
const btnPrimaryStyle = { padding: "10px 15px", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" };
const btnLightStyle = { padding: "10px", backgroundColor: "#e8eaed", color: "#3c4043", border: "1px solid #dadce0", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" };