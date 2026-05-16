import { useState, useEffect } from "react";

function App() {
  const [registros, setRegistros] = useState([]);
  const [nombre, setNombre] = useState("");
  const [fecha, setFecha] = useState("");
  const [limite, setLimite] = useState(50);
  const [cargando, setCargando] = useState(false);

  // Función para obtener los datos de la API aplicando los filtros
  const cargarHistorial = async () => {
    setCargando(true);
    try {
      // Construcción dinámica de la URL con query parameters
      let url = `http://localhost:8000/api/v1/reportes/asistencia?limite=${limite}`;
      if (nombre) url += `&nombre=${nombre}`;
      if (fecha) url += `&fecha=${fecha}`;

      const respuesta = await fetch(url);
      const resultado = await respuesta.json();

      if (resultado.status === "ok") {
        setRegistros(resultado.data);
      }
    } catch (error) {
      console.error("Error al conectar con la API:", error);
    } finally {
      setCargando(false);
    }
  };

  // Ejecuta la consulta automáticamente al cargar la página o al cambiar los filtros
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      cargarHistorial();
    }, 300); // Pequeña pausa para no saturar la API mientras el usuario escribe el nombre

    return () => clearTimeout(delayDebounceFn);
  }, [nombre, fecha, limite]);

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif", maxWidth: "1000px", margin: "0 auto" }}>
      <h1>Control de Asistencia - Tech Lab</h1>

      {/* Sección de Filtros */}
      <div style={{ display: "flex", gap: "15px", marginBottom: "20px", flexWrap: "wrap" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
          <label>Buscar por Nombre:</label>
          <input
            type="text"
            placeholder="Ej. Farid"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
          <label>Filtrar por Fecha:</label>
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
          <label>Límite de registros:</label>
          <select
            value={limite}
            onChange={(e) => setLimite(Number(e.target.value))}
            style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Tabla de Resultados */}
      {cargando ? (
        <p>Cargando registros históricos...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "10px" }}>
          <thead>
            <tr style={{ backgroundColor: "#f4f4f4", textAlign: "left" }}>
              <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>ID Registro</th>
              <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>Nombre</th>
              <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>Tipo de Movimiento</th>
              <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>Fecha y Hora</th>
            </tr>
          </thead>
          <tbody>
            {registros.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ padding: "20px", textAlign: "center", color: "#666" }}>
                  No se encontraron registros que coincidan con los filtros aplicados.
                </td>
              </tr>
            ) : (
              registros.map((reg) => (
                <tr key={reg.registro_id} style={{ borderBottom: "1px solid #ddd" }}>
                  <td style={{ padding: "12px" }}>{reg.registro_id}</td>
                  <td style={{ padding: "12px", fontWeight: "bold" }}>{reg.nombre}</td>
                  <td style={{ padding: "12px" }}>
                    <span style={{
                      padding: "4px 8px",
                      borderRadius: "4px",
                      fontSize: "0.9em",
                      backgroundColor: reg.tipo === "entrada" ? "#e6f4ea" : "#fce8e6",
                      color: reg.tipo === "entrada" ? "#137333" : "#c5221f",
                      textTransform: "uppercase"
                    }}>
                      {reg.tipo}
                    </span>
                  </td>
                  <td style={{ padding: "12px" }}>
                    {new Date(reg.fecha_hora).toLocaleString("es-PE")}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;