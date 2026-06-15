import { useState, useEffect } from "react";
import Identicon from "../components/Identicon";

export default function Home() {
  const [enLaboratorio, setEnLaboratorio] = useState([]);
  const [cargando, setCargando] = useState(true);

  const cargarEnLaboratorio = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/asistencia/en-laboratorio`);
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
    const wsUrl = import.meta.env.VITE_API_URL.replace(/^http/, "ws") + "/api/v1/ws";
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
        <h2 style={{ color: "#1e293b", marginTop: 0, borderBottom: "1px solid #e2e8f0", paddingBottom: "15px" }}>
          Actualmente en el Laboratorio ({enLaboratorio.length})
        </h2>
        
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
                  <th style={{ padding: "12px", color: "#64748b", fontWeight: "600" }}>Hora de Entrada</th>
                </tr>
              </thead>
              <tbody>
                {enLaboratorio.map((p, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "12px", color: "#1e293b" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <Identicon value={p.dni} size={32} />
                        <span style={{ fontWeight: "bold" }}>{p.nombres} {p.apellidos}</span>
                      </div>
                    </td>
                    <td style={{ padding: "12px", color: "#059669", fontWeight: "500" }}>{p.hora_entrada}</td>
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