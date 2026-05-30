// src/pages/Supervisar.jsx
import { useState, useEffect } from "react";

export default function Supervisar() {
  const [resumen, setResumen] = useState([]);
  const [proyectos, setProyectos] = useState([]);
  const [filtroProyecto, setFiltroProyecto] = useState("");
  const [cargando, setCargando] = useState(false);

  // 1. Cargar proyectos para el filtro
  const cargarProyectos = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/proyectos");
      const data = await res.json();
      if (data.status === "ok") setProyectos(data.data);
    } catch (err) { console.error(err); }
  };

  // 2. Cargar el resumen de horas
  const cargarResumen = async () => {
    setCargando(true);
    try {
      let url = "http://localhost:8000/api/v1/supervision/resumen";
      if (filtroProyecto) url += `?proyecto_id=${filtroProyecto}`;
      
      const res = await fetch(url);
      const data = await res.json();
      if (data.status === "ok") setResumen(data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarProyectos();
  }, []);

  useEffect(() => {
    cargarResumen();
  }, [filtroProyecto]);

  return (
    <div>
      <h2>Supervisión de Proyectos</h2>
      
      <div style={{ marginBottom: "20px" }}>
        <label style={{ fontWeight: "bold", marginRight: "10px" }}>Filtrar por Proyecto:</label>
        <select value={filtroProyecto} onChange={(e) => setFiltroProyecto(e.target.value)} style={{ padding: "8px" }}>
          <option value="">Todos los proyectos</option>
          {proyectos.map(p => (
            <option key={p.id} value={p.id}>{p.nombre_proyecto}</option>
          ))}
        </select>
      </div>

      {cargando ? <p>Calculando horas totales...</p> : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ backgroundColor: "#f4f4f4", textAlign: "left" }}>
              <th style={thStyle}>Código</th>
              <th style={thStyle}>Nombre Completo</th>
              <th style={thStyle}>Proyecto</th>
              <th style={thStyle}>Horas Totales</th>
            </tr>
          </thead>
          <tbody>
            {resumen.map((al) => (
              <tr key={al.codigo_alumno} style={{ borderBottom: "1px solid #ddd" }}>
                <td style={tdStyle}>{al.codigo_alumno}</td>
                <td style={tdStyle}>{al.nombres} {al.apellidos}</td>
                <td style={tdStyle}>{al.proyecto}</td>
                <td style={{ ...tdStyle, fontWeight: "bold", color: "#1a73e8" }}>
                  {al.horas_totales} h
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const thStyle = { padding: "12px", borderBottom: "2px solid #ddd" };
const tdStyle = { padding: "12px" };