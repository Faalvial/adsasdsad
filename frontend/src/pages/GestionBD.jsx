import { useState, useEffect } from "react";

export default function GestionBD() {
  const [tab, setTab] = useState("proyectos");

  // Estados Proyectos
  const [proyectos, setProyectos] = useState([]);
  const [proyectosCargando, setProyectosCargando] = useState(false);
  const [formProyecto, setFormProyecto] = useState({ id: null, nombre: "", descripcion: "" });
  const [busquedaProyecto, setBusquedaProyecto] = useState("");

  // Estados Personas
  const [personas, setPersonas] = useState([]);
  const [personasCargando, setPersonasCargando] = useState(false);
  const [formPersona, setFormPersona] = useState({ id: null, dni: "", codigo: "", nombres: "", apellidos: "", proyecto_id: "", estado_activo: true });
  const [busquedaPersona, setBusquedaPersona] = useState("");

  const cargarProyectos = async () => {
    setProyectosCargando(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/proyectos`);
      const data = await res.json();
      if (data.status === "ok") setProyectos(data.data);
    } catch (err) {
      console.error(err);
    }
    setProyectosCargando(false);
  };

  const cargarPersonas = async () => {
    setPersonasCargando(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/personas`);
      const data = await res.json();
      if (data.status === "ok") setPersonas(data.data);
    } catch (err) {
      console.error(err);
    }
    setPersonasCargando(false);
  };

  useEffect(() => {
    cargarProyectos();
    cargarPersonas();

    const wsUrl = import.meta.env.VITE_API_URL.replace(/^http/, "ws") + "/api/v1/ws";
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "update") {
          if (data.entity === "proyectos") cargarProyectos();
          if (data.entity === "personas") cargarPersonas();
        }
      } catch (err) {
        console.error("Error procesando mensaje WebSocket", err);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const guardarProyecto = async (e) => {
    e.preventDefault();
    try {
      if (formProyecto.id) {
        await fetch(`${import.meta.env.VITE_API_URL}/api/v1/proyectos/${formProyecto.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombre_proyecto: formProyecto.nombre, descripcion: formProyecto.descripcion })
        });
      } else {
        await fetch(`${import.meta.env.VITE_API_URL}/api/v1/proyectos`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombre_proyecto: formProyecto.nombre, descripcion: formProyecto.descripcion })
        });
      }
      setFormProyecto({ id: null, nombre: "", descripcion: "" });
      cargarProyectos();
    } catch (err) {
      alert("Error guardando proyecto");
    }
  };

  const eliminarProyecto = async (id) => {
    if (!confirm("¿Seguro que deseas eliminar este proyecto?")) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL}/api/v1/proyectos/${id}`, { method: "DELETE" });
      cargarProyectos();
    } catch (err) {
      alert("Error eliminando proyecto");
    }
  };

  const guardarPersona = async (e) => {
    e.preventDefault();
    if (!formPersona.id) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL}/api/v1/personas/${formPersona.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dni: formPersona.dni,
          codigo_alumno: formPersona.codigo,
          nombres: formPersona.nombres,
          apellidos: formPersona.apellidos,
          proyecto_id: formPersona.proyecto_id ? parseInt(formPersona.proyecto_id) : null,
          estado_activo: formPersona.estado_activo
        })
      });
      setFormPersona({ id: null, dni: "", codigo: "", nombres: "", apellidos: "", proyecto_id: "", estado_activo: true });
      cargarPersonas();
    } catch (err) {
      alert("Error guardando persona");
    }
  };

  const eliminarPersona = async (id) => {
    if (!confirm("¿Seguro que deseas eliminar esta persona? Esto borrará sus asistencias.")) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL}/api/v1/personas/${id}`, { method: "DELETE" });
      cargarPersonas();
    } catch (err) {
      alert("Error eliminando persona");
    }
  };

  const inputStyle = { padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#334155", outline: "none", width: "100%", marginBottom: "10px" };
  const btnStyle = { padding: "10px 15px", backgroundColor: "#10b981", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600", transition: "opacity 0.2s" };
  const tabStyle = (active) => ({ padding: "10px 20px", cursor: "pointer", borderBottom: active ? "2px solid #10b981" : "2px solid transparent", fontWeight: active ? "600" : "500", color: active ? "#1e293b" : "#64748b", transition: "all 0.2s" });

  return (
    <div>
      <h2 style={{ color: "#1e293b", marginBottom: "25px" }}>Gestión de Base de Datos</h2>

      <div style={{ display: "flex", gap: "20px", marginBottom: "20px", borderBottom: "1px solid #e2e8f0" }}>
        <div style={tabStyle(tab === "proyectos")} onClick={() => setTab("proyectos")}>Proyectos</div>
        <div style={tabStyle(tab === "personas")} onClick={() => setTab("personas")}>Personas</div>
      </div>

      <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1)", border: "1px solid #e2e8f0", padding: "25px" }}>
        
        {/* PESTAÑA PROYECTOS */}
        {tab === "proyectos" && (
          <div>
            <form onSubmit={guardarProyecto} style={{ marginBottom: "20px", padding: "15px", backgroundColor: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <h4 style={{ marginTop: 0 }}>{formProyecto.id ? "Editar Proyecto" : "Nuevo Proyecto"}</h4>
              <div style={{ display: "flex", gap: "10px" }}>
                <input style={inputStyle} required type="text" placeholder="Nombre" value={formProyecto.nombre} onChange={e => setFormProyecto({ ...formProyecto, nombre: e.target.value })} />
                <input style={inputStyle} type="text" placeholder="Descripción" value={formProyecto.descripcion} onChange={e => setFormProyecto({ ...formProyecto, descripcion: e.target.value })} />
                <button style={{ ...btnStyle, height: "fit-content", alignSelf: "flex-start" }} type="submit">{formProyecto.id ? "Actualizar" : "Crear"}</button>
                {formProyecto.id && <button type="button" onClick={() => setFormProyecto({ id: null, nombre: "", descripcion: "" })} style={{ ...btnStyle, backgroundColor: "#94a3b8", height: "fit-content", alignSelf: "flex-start" }}>Cancelar</button>}
              </div>
            </form>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
              <h3 style={{ margin: 0, color: "#1e293b" }}>Lista de Proyectos</h3>
              <input 
                type="text" 
                placeholder="Buscar proyecto..." 
                value={busquedaProyecto} 
                onChange={(e) => setBusquedaProyecto(e.target.value)}
                style={{ ...inputStyle, width: "250px", marginBottom: 0 }}
              />
            </div>

            {proyectosCargando ? <p>Cargando proyectos...</p> : (
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>ID</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Nombre</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Descripción</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {proyectos.filter(p => p.nombre_proyecto.toLowerCase().includes(busquedaProyecto.toLowerCase()) || p.descripcion?.toLowerCase().includes(busquedaProyecto.toLowerCase())).map(p => (
                    <tr key={p.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "14px 20px", color: "#94a3b8" }}>{p.id}</td>
                      <td style={{ padding: "14px 20px", fontWeight: "600", color: "#1e293b" }}>{p.nombre_proyecto}</td>
                      <td style={{ padding: "14px 20px", color: "#475569" }}>{p.descripcion}</td>
                      <td style={{ padding: "14px 20px", display: "flex", gap: "10px" }}>
                        <button onClick={() => setFormProyecto({ id: p.id, nombre: p.nombre_proyecto, descripcion: p.descripcion })} style={{ ...btnStyle, backgroundColor: "#64748b", padding: "4px 8px", fontSize: "0.8rem" }}>Editar</button>
                        <button onClick={() => eliminarProyecto(p.id)} style={{ ...btnStyle, backgroundColor: "#ea4335", padding: "4px 8px", fontSize: "0.8rem" }}>Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* PESTAÑA PERSONAS */}
        {tab === "personas" && (
          <div>
            {formPersona.id && (
              <form onSubmit={guardarPersona} style={{ marginBottom: "20px", padding: "15px", backgroundColor: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <h4 style={{ marginTop: 0 }}>Editar Persona</h4>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                  <input style={{...inputStyle, width: "150px"}} required type="text" placeholder="DNI" value={formPersona.dni} onChange={e => setFormPersona({ ...formPersona, dni: e.target.value })} />
                  <input style={{...inputStyle, width: "150px"}} required type="text" placeholder="Código" value={formPersona.codigo} onChange={e => setFormPersona({ ...formPersona, codigo: e.target.value })} />
                  <input style={{...inputStyle, width: "200px"}} required type="text" placeholder="Nombres" value={formPersona.nombres} onChange={e => setFormPersona({ ...formPersona, nombres: e.target.value })} />
                  <input style={{...inputStyle, width: "200px"}} required type="text" placeholder="Apellidos" value={formPersona.apellidos} onChange={e => setFormPersona({ ...formPersona, apellidos: e.target.value })} />
                  
                  <select style={{...inputStyle, width: "200px"}} value={formPersona.proyecto_id} onChange={e => setFormPersona({ ...formPersona, proyecto_id: e.target.value })}>
                    <option value="">Sin Proyecto</option>
                    {proyectos.map(p => <option key={p.id} value={p.id}>{p.nombre_proyecto}</option>)}
                  </select>

                  <label style={{ display: "flex", alignItems: "center", gap: "5px", marginBottom: "10px" }}>
                    <input type="checkbox" checked={formPersona.estado_activo} onChange={e => setFormPersona({ ...formPersona, estado_activo: e.target.checked })} />
                    Activo
                  </label>

                  <div style={{ width: "100%", display: "flex", gap: "10px" }}>
                    <button style={btnStyle} type="submit">Actualizar</button>
                    <button type="button" onClick={() => setFormPersona({ id: null, dni: "", codigo: "", nombres: "", apellidos: "", proyecto_id: "", estado_activo: true })} style={{ ...btnStyle, backgroundColor: "#94a3b8" }}>Cancelar</button>
                  </div>
                </div>
              </form>
            )}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
              <h3 style={{ margin: 0, color: "#1e293b" }}>Lista de Personas</h3>
              <input 
                type="text" 
                placeholder="Buscar por DNI, Nombre o Código..." 
                value={busquedaPersona} 
                onChange={(e) => setBusquedaPersona(e.target.value)}
                style={{ ...inputStyle, width: "300px", marginBottom: 0 }}
              />
            </div>

            {personasCargando ? <p>Cargando personas...</p> : (
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>DNI / Código</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Nombre Completo</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Proyecto</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Estado</th>
                    <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {personas.filter(p => 
                    p.nombres.toLowerCase().includes(busquedaPersona.toLowerCase()) || 
                    p.apellidos.toLowerCase().includes(busquedaPersona.toLowerCase()) ||
                    p.dni.includes(busquedaPersona) ||
                    p.codigo_alumno.includes(busquedaPersona)
                  ).map(p => (
                    <tr key={p.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "14px 20px" }}>
                        <div style={{ color: "#475569", fontWeight: "500" }}>{p.dni}</div>
                        <div style={{ fontSize: "0.85rem", color: "#1e293b", fontFamily: "monospace", marginTop: "4px" }}>{p.codigo_alumno}</div>
                      </td>
                      <td style={{ padding: "14px 20px", fontWeight: "600", color: "#1e293b" }}>{p.nombres} {p.apellidos}</td>
                      <td style={{ padding: "14px 20px", color: "#475569" }}>{p.proyecto_nombre || '---'}</td>
                      <td style={{ padding: "14px 20px" }}>
                        <span style={{ padding: "4px 10px", borderRadius: "12px", fontSize: "0.8rem", fontWeight: "600", backgroundColor: p.estado_activo ? "#dcfce7" : "#fee2e2", color: p.estado_activo ? "#166534" : "#991b1b" }}>
                          {p.estado_activo ? "Activo" : "Inactivo"}
                        </span>
                      </td>
                      <td style={{ padding: "14px 20px", display: "flex", gap: "10px" }}>
                        <button onClick={() => setFormPersona({ id: p.id, dni: p.dni, codigo: p.codigo_alumno, nombres: p.nombres, apellidos: p.apellidos, proyecto_id: p.proyecto_id || "", estado_activo: p.estado_activo })} style={{ ...btnStyle, backgroundColor: "#64748b", padding: "4px 8px", fontSize: "0.8rem" }}>Editar</button>
                        <button onClick={() => eliminarPersona(p.id)} style={{ ...btnStyle, backgroundColor: "#ea4335", padding: "4px 8px", fontSize: "0.8rem" }}>Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
