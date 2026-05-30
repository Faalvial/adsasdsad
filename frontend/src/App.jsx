import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Home from "./pages/Home";
import RegistrarAlumno from "./pages/RegistrarAlumno";
import Historial from "./pages/Historial";
import Supervisar from "./pages/Supervisar";

export default function App() {
  const [sistemaActivo, setSistemaActivo] = useState(false);

  // Consulta al backend para saber si el script está corriendo
  const fetchEstado = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/sistema/estado");
      const data = await res.json();
      setSistemaActivo(data.activo);
    } catch (err) {
      console.error("Error obteniendo estado del sistema", err);
    }
  };

  // Consultar estado al cargar y monitorear cada 3 segundos
  useEffect(() => {
    fetchEstado();
    const interval = setInterval(fetchEstado, 3000);
    return () => clearInterval(interval);
  }, []);

  // Función que dispara el switch
  const handleToggle = async () => {
    const nuevoEstado = !sistemaActivo;
    setSistemaActivo(nuevoEstado); // Actualización visual instantánea

    try {
      await fetch("http://localhost:8000/api/v1/sistema/estado", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activo: nuevoEstado })
      });
    } catch (err) {
      console.error("Error cambiando estado", err);
      setSistemaActivo(!nuevoEstado); // Revertir visualmente si el backend falla
    }
  };

  return (
    <Router>
      <div style={{ fontFamily: "system-ui, sans-serif", margin: "0 auto", maxWidth: "1200px", padding: "20px" }}>

        {/* BARRA DE NAVEGACIÓN SUPERIOR */}
        <nav style={{ paddingBottom: "20px", borderBottom: "1px solid #ddd", marginBottom: "30px", display: "flex", gap: "20px", justifyContent: "space-between", alignItems: "center" }}>

          <div style={{ display: "flex", gap: "20px" }}>
            <Link to="/" style={navStyle}>Inicio</Link>
            <Link to="/registrar" style={navStyle}>Registrar Alumno</Link>
            <Link to="/historial" style={navStyle}>Historial Asistencias</Link>
            <Link to="/supervisar" style={navStyle}>Supervisar</Link>
          </div>

          {/* SWITCHER DE ESTADO DEL MAIN.PY */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 15px", backgroundColor: sistemaActivo ? "#e6f4ea" : "#fce8e6", borderRadius: "8px", border: `1px solid ${sistemaActivo ? "#34a853" : "#ea4335"}` }}>
            <span style={{ fontWeight: "bold", fontSize: "0.95em", color: sistemaActivo ? "#137333" : "#c5221f" }}>
              IA de Reconocimiento: {sistemaActivo ? "ACTIVA" : "APAGADA"}
            </span>

            {/* Toggle Switch UI */}
            <label style={{ position: "relative", display: "inline-block", width: "44px", height: "24px", margin: 0 }}>
              <input type="checkbox" checked={sistemaActivo} onChange={handleToggle} style={{ opacity: 0, width: 0, height: 0 }} />
              <span style={{ position: "absolute", cursor: "pointer", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: sistemaActivo ? "#34a853" : "#ccc", transition: ".3s", borderRadius: "24px" }}>
                <span style={{ position: "absolute", content: '""', height: "16px", width: "16px", left: sistemaActivo ? "24px" : "4px", bottom: "4px", backgroundColor: "white", transition: ".3s", borderRadius: "50%" }}></span>
              </span>
            </label>
          </div>

        </nav>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/registrar" element={<RegistrarAlumno />} />
          <Route path="/historial" element={<Historial />} />
          <Route path="/supervisar" element={<Supervisar />} />
        </Routes>

      </div>
    </Router>
  );
}

const navStyle = {
  textDecoration: "none",
  color: "#333",
  fontWeight: "bold",
  padding: "10px 15px",
  backgroundColor: "#f4f4f4",
  borderRadius: "5px"
};