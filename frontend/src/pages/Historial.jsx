import { useState, useEffect } from "react";

export default function Historial() {
  const [registros, setRegistros] = useState([]);
  const [filtro, setFiltro] = useState("");
  const [fecha, setFecha] = useState("");
  const [limite, setLimite] = useState(50);
  const [cargando, setCargando] = useState(false);

  const cargarHistorial = async () => {
    setCargando(true);
    try {
      let url = `http://localhost:8000/api/v1/reportes/asistencia?limite=${limite}`;
      if (filtro) url += `&filtro=${filtro}`;
      if (fecha) url += `&fecha=${fecha}`;

      const respuesta = await fetch(url);
      const resultado = await respuesta.json();

      if (resultado.status === "ok") {
        setRegistros(resultado.data);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      cargarHistorial();
    }, 300);
    return () => clearTimeout(timer);
  }, [filtro, fecha, limite]);

  return (
    <div>
      <h2 style={{ color: "#1e293b", marginBottom: "25px" }}>Historial de Asistencias</h2>

      {/* CONTENEDOR TIPO TARJETA */}
      <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1)", border: "1px solid #e2e8f0", overflow: "hidden" }}>

        {/* ZONA DE FILTROS */}
        <div style={{ display: "flex", gap: "15px", padding: "15px 20px", borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc", flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="Buscar por nombre o código..."
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
            style={{ flex: 1, minWidth: "250px", padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#334155", outline: "none" }}
          />
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            style={{ padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#475569", outline: "none" }}
          />
          <select
            value={limite}
            onChange={(e) => setLimite(Number(e.target.value))}
            style={{ padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#475569", outline: "none", cursor: "pointer" }}
          >
            <option value={10}>10 registros</option>
            <option value={50}>50 registros</option>
            <option value={100}>100 registros</option>
          </select>
        </div>

        {/* ZONA DE DATOS (O ESTADO DE CARGA) */}
        {cargando ? (
          <div style={{ padding: "40px", textAlign: "center", color: "#64748b", fontWeight: "500" }}>
            Cargando datos...
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.95rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>ID</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Código</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Nombre Completo</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Proyecto</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Entrada</th>
                  <th style={{ padding: "14px 20px", color: "#64748b", fontWeight: "600", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Salida</th>
                </tr>
              </thead>
              <tbody>
                {registros.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ padding: "30px", textAlign: "center", color: "#94a3b8" }}>No se encontraron registros de asistencia.</td>
                  </tr>
                ) : (
                  registros.map((reg, index) => (
                    <tr key={reg.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "14px 20px", color: "#94a3b8" }}>{index + 1}</td>
                      <td style={{ padding: "14px 20px", color: "#1e293b", fontFamily: "monospace", fontSize: "0.9rem" }}>{reg.codigo}</td>
                      <td style={{ padding: "14px 20px", fontWeight: "600", color: "#1e293b" }}>{reg.nombre_completo}</td>
                      <td style={{ padding: "14px 20px", color: "#1e293b" }}>{reg.proyecto}</td>

                      <td style={{ padding: "14px 20px", color: "#059669", fontWeight: "500" }}>
                        {reg.entrada}
                      </td>

{/* Hora Salida: Naranja si sigue adentro, Rojo mate si ya salió */}
                      <td style={{
                        padding: "14px 20px",
                        color: reg.salida.includes("Aún") ? "#d97706" : "#dc2626",
                        fontWeight: reg.salida.includes("Aún") ? "normal" : "500"
                      }}>
                        {reg.salida}
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