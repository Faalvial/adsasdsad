import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import Home from "./pages/Home";
import RegistrarAlumno from "./pages/RegistrarAlumno";
import Historial from "./pages/Historial";
import Supervisar from "./pages/Supervisar";
import GestionBD from "./pages/GestionBD";

function Layout() {
  const [sistemaActivo, setSistemaActivo] = useState(false);
  const location = useLocation();

  // NUEVO: Memoria para saber de qué pestaña venimos
  const prevPath = useRef(location.pathname);

  const cambiarEstadoBackend = async (activar) => {
    setSistemaActivo(activar);
    try {
      await fetch(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/sistema/estado`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activo: activar })
      });
    } catch (err) {
      console.error("Error cambiando estado del sistema", err);
    }
  };

  // EFECTO 1: Comportamiento por defecto al abrir la aplicación
  useEffect(() => {
    if (location.pathname !== '/registrar') {
      cambiarEstadoBackend(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // EFECTO 2: Navegación inteligente
  useEffect(() => {
    if (location.pathname === '/registrar') {
      // Regla A: Si entramos a registrar, forzamos el APAGADO para liberar cámara
      cambiarEstadoBackend(false);
    }
    else if (prevPath.current === '/registrar') {
      // Regla B: Si vamos SALIENDO de registrar hacia otra página, forzamos el ENCENDIDO
      cambiarEstadoBackend(true);
    }
    // Regla C: Si navegamos entre Inicio, Historial o Supervisar... ¡No hacemos nada!
    // Esto es lo que conserva el estado manual que hayas elegido.

    // Actualizamos la memoria para el próximo clic
    prevPath.current = location.pathname;

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  const fetchEstado = async () => {
    try {
      const res = await fetch(`${(import.meta.env.VITE_API_URL || "http://localhost:8000")}/api/v1/sistema/estado`);
      const data = await res.json();
      setSistemaActivo(data.activo);
    } catch (err) {}
  };

  useEffect(() => {
    const interval = setInterval(fetchEstado, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", margin: "0 auto", maxWidth: "1200px", padding: "20px" }}>

      {/* BARRA DE NAVEGACIÓN SUPERIOR */}
      <nav style={{ paddingBottom: "20px", borderBottom: "1px solid #ddd", marginBottom: "30px", display: "flex", gap: "20px", justifyContent: "space-between", alignItems: "center" }}>

        <div style={{ display: "flex", gap: "20px" }}>
          <Link to="/" style={navStyle}>Inicio</Link>
          <Link to="/registrar" style={navStyle}>Registrar Alumno</Link>
          <Link to="/historial" style={navStyle}>Historial Asistencias</Link>
          <Link to="/supervisar" style={navStyle}>Supervisar</Link>
          <Link to="/gestion" style={navStyle}>Gestión BD</Link>
        </div>

        {/* SWITCHER DE ESTADO DEL MAIN.PY */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 15px", backgroundColor: sistemaActivo ? "#e6f4ea" : "#fce8e6", borderRadius: "8px", border: `1px solid ${sistemaActivo ? "#34a853" : "#ea4335"}` }}>
          <span style={{ fontWeight: "bold", fontSize: "0.95em", color: sistemaActivo ? "#137333" : "#c5221f" }}>
            IA de Reconocimiento: {sistemaActivo ? "ACTIVA" : "APAGADA"}
          </span>

          <label style={{ position: "relative", display: "inline-block", width: "44px", height: "24px", margin: 0 }}>
            <input
              type="checkbox"
              checked={sistemaActivo}
              onChange={() => cambiarEstadoBackend(!sistemaActivo)}
              disabled={location.pathname === '/registrar'}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span style={{
              position: "absolute",
              cursor: location.pathname === '/registrar' ? "not-allowed" : "pointer",
              top: 0, left: 0, right: 0, bottom: 0,
              backgroundColor: sistemaActivo ? "#34a853" : "#ccc",
              transition: ".3s",
              borderRadius: "24px",
              opacity: location.pathname === '/registrar' ? 0.4 : 1
            }}>
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
        <Route path="/gestion" element={<GestionBD />} />
      </Routes>

    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Layout />
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
