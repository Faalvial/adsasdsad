import { useState, useEffect } from "react";
import Identicon from "../components/Identicon";

export default function Home() {
  const [enLaboratorio, setEnLaboratorio] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [menuExportarAbierto, setMenuExportarAbierto] = useState(false);

  const descargarCSV = (tabla) => {
    const endpoint = tabla === "personas" ? "/api/v1/personas/exportar" : "/api/v1/reportes/exportar";
    const url = `${(import.meta.env.VITE_API_URL || "http://localhost:8000")}${endpoint}`;
    window.open(url, "_blank");
    setMenuExportarAbierto(false);
  };

  const cargarEnLaboratorio = async () => {
    try {
      const res = await fetch(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/asistencia/en-laboratorio`);
      const data = await res.json();
      if (data.status === "ok") {
        setEnLaboratorio(data.data);
      }
    } catch (err) {
      console.error("Error cargando personas en laboratorio", err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarEnLaboratorio();

    // Conectar WebSocket para actualizaciones en tiempo real
    const wsUrl = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/^http/, "ws") + "/api/v1/ws";
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Si el backend avisa que cambió una asistencia, recargar datos
        if (data.type === "update" && data.entity === "asistencia") {
          cargarEnLaboratorio();
        }
      } catch (err) {
        console.error("Error procesando mensaje WebSocket", err);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minHeight: "60vh", gap: "30px", marginTop: "20px" }}>
      


      <div style={{
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05)",
        border: "1px solid #e2e8f0",
        padding: "30px",
        width: "100%",
        maxWidth: "900px"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e2e8f0", paddingBottom: "15px" }}>
          <h2 style={{ color: "#1e293b", margin: 0 }}>
            Actualmente en el Laboratorio ({enLaboratorio.length})
          </h2>

          <div style={{ position: "relative" }}>
            <button
              onClick={() => setMenuExportarAbierto(!menuExportarAbierto)}
              style={{
                padding: "10px 15px",
                backgroundColor: "#10b981",
                color: "white",
                border: "none",
                borderRadius: "6px",
                fontWeight: "600",
                cursor: "pointer",
                transition: "opacity 0.2s"
              }}
              onMouseOver={(e) => e.target.style.opacity = 0.85}
              onMouseOut={(e) => e.target.style.opacity = 1}
            >
              ↓ Exportar
            </button>

            {menuExportarAbierto && (
              <div style={{
                position: "absolute",
                right: 0,
                top: "calc(100% + 6px)",
                backgroundColor: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "6px",
                boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
                overflow: "hidden",
                zIndex: 10,
                minWidth: "180px"
              }}>
                <button
                  onClick={() => descargarCSV("personas")}
                  style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 15px", border: "none", backgroundColor: "transparent", cursor: "pointer", color: "#1e293b", fontSize: "0.9rem" }}
                  onMouseOver={(e) => e.target.style.backgroundColor = "#f1f5f9"}
                  onMouseOut={(e) => e.target.style.backgroundColor = "transparent"}
                >
                  Tabla de Personas
                </button>
                <button
                  onClick={() => descargarCSV("asistencia")}
                  style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 15px", border: "none", backgroundColor: "transparent", cursor: "pointer", color: "#1e293b", fontSize: "0.9rem", borderTop: "1px solid #f1f5f9" }}
                  onMouseOver={(e) => e.target.style.backgroundColor = "#f1f5f9"}
                  onMouseOut={(e) => e.target.style.backgroundColor = "transparent"}
                >
                  Tabla de Asistencia
                </button>
              </div>
            )}
          </div>
        </div>
        
        {cargando && enLaboratorio.length === 0 ? (
          <p style={{ textAlign: "center", color: "#64748b" }}>Cargando datos...</p>
        ) : enLaboratorio.length === 0 ? (
          <p style={{ textAlign: "center", color: "#64748b", padding: "20px" }}>No hay personas en el laboratorio en este momento.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <th style={{ padding: "12px", color: "#64748b", fontWeight: "600" }}>Nombre Completo</th>
                </tr>
              </thead>
              <tbody>
                {enLaboratorio.map((p, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "12px", color: "#1e293b" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <Identicon value={p.dni} size={32} />
                        <span style={{ fontWeight: "bold" }}>
                          {p.nombres?.split(' ')[0]} {p.apellidos?.split(' ')[0]}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
