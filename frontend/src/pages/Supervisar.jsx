// src/pages/Supervisar.jsx
import { useState, useEffect } from "react";

export default function Supervisar() {
  const [resumen, setResumen] = useState([]);
  const [proyectos, setProyectos] = useState([]);
  const [filtroProyecto, setFiltroProyecto] = useState("");
  const [cargando, setCargando] = useState(false);
  const [refreshToggle, setRefreshToggle] = useState(false);

  const cargarProyectos = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/proyectos`);
      const data = await res.json();
      if (data.status === "ok") setProyectos(data.data);
    } catch (err) { console.error(err); }
  };

  const cargarResumen = async () => {
    setCargando(true);
    try {
      let url = `${import.meta.env.VITE_API_URL}/api/v1/supervision/resumen`;
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
    const wsUrl = import.meta.env.VITE_API_URL.replace(/^http/, "ws") + "/api/v1/ws";
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "update") {
          setRefreshToggle(prev => !prev);
        }
      } catch (err) {
        console.error("Error WebSocket", err);
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => { cargarProyectos(); }, [refreshToggle]);
  useEffect(() => { cargarResumen(); }, [filtroProyecto, refreshToggle]);

  return (
    <div>
      <h2 style={{ color: "#1e293b", marginBottom: "25px" }}>Supervisión de Proyectos</h2>

      {/* CONTENEDOR TIPO TARJETA */}
      <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1)", border: "1px solid #e2e8f0", overflow: "hidden" }}>

        {/* ZONA DE FILTROS */}
        <div style={{ display: "flex", alignItems: "center", gap: "15px", padding: "15px 20px", borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc", flexWrap: "wrap" }}>
          <label style={{ fontWeight: "600", color: "#475569", fontSize: "0.95rem" }}>Filtrar por Proyecto:</label>
          <select
            value={filtroProyecto}
            onChange={(e) => setFiltroProyecto(e.target.value)}
            style={{ padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#334155", outline: "none", minWidth: "250px", cursor: "pointer" }}
          >
            <option value="">Todos los proyectos</option>
            {proyectos.map(p => (
              <option key={p.id} value={p.id}>{p.nombre_proyecto}</option>
            ))}
          </select>
        </div>

        {/* ZONA DE DATOS */}
        {cargando ? (
          <div style={{ padding: "40px", textAlign: "center", color: "#64748b", fontWeight: "500" }}>Calculando horas totales...</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.95rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>DNI</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Código</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Nombre Completo</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Proyecto</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Primer Registro</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Último Registro</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Horas Totales</th>
                </tr>
              </thead>
              <tbody>
                {resumen.length === 0 ? (
                  <tr><td colSpan="6" style={{ padding: "30px", textAlign: "center", color: "#94a3b8" }}>No hay datos para mostrar.</td></tr>
                ) : (
                  resumen.map((reg, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "14px 20px", color: "#475569", fontWeight: "500" }}>{reg.dni}</td>
                      <td style={{ padding: "14px 20px", color: "#1e293b", fontFamily: "monospace", fontSize: "0.9rem" }}>{reg.codigo_alumno}</td>
                      <td style={{ padding: "14px 20px", fontWeight: "600", color: "#1e293b" }}>{reg.nombres} {reg.apellidos}</td>
                      <td style={{ padding: "14px 20px", color: "#1e293b" }}>{reg.proyecto}</td>

                      <td style={{ padding: "14px 20px", fontSize: "0.9em", color: "#1e293b" }}>{reg.primera_asistencia}</td>
                      <td style={{ padding: "14px 20px", fontSize: "0.9em", color: "##1e293b" }}>{reg.ultima_asistencia}</td>

                      {/* Horas Totales destacadas en azul corporativo */}
                      <td style={{ padding: "14px 20px", fontWeight: "bold", color: "#1e293b", fontSize: "1.05em" }}>
                        {reg.horas_totales} h
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}