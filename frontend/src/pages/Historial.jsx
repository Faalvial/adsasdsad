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
      <h2>Historial de Asistencias</h2>
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
        <input type="text" placeholder="Buscar por nombre o código..." value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ padding: "8px", flex: 1 }} />
        <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} style={{ padding: "8px" }} />
        <select value={limite} onChange={(e) => setLimite(Number(e.target.value))} style={{ padding: "8px" }}>
          <option value={10}>10 registros</option>
          <option value={50}>50 registros</option>
          <option value={100}>100 registros</option>
        </select>
      </div>

      {cargando ? <p>Cargando datos...</p> : (
<table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
  <thead>
    <tr style={{ backgroundColor: "#f4f4f4", borderBottom: "2px solid #ddd" }}>
      <th style={{ padding: "12px" }}>ID</th>
      <th style={{ padding: "12px" }}>Código</th>
      <th style={{ padding: "12px" }}>Nombre Completo</th>
      <th style={{ padding: "12px" }}>Proyecto</th>
      <th style={{ padding: "12px" }}>Hora Entrada</th>
      <th style={{ padding: "12px" }}>Hora Salida</th>
    </tr>
  </thead>
  <tbody>
    {registros.map((reg) => (
      <tr key={reg.id} style={{ borderBottom: "1px solid #ddd" }}>
        <td style={{ padding: "12px" }}>{reg.id}</td>
        <td style={{ padding: "12px" }}>{reg.codigo}</td>
        <td style={{ padding: "12px", fontWeight: "bold" }}>{reg.nombre_completo}</td>
        <td style={{ padding: "12px" }}>{reg.proyecto}</td>

        {/* Columna Entrada: En verde para distinguirla rápido */}
        <td style={{ padding: "12px", color: "#137333", fontWeight: "bold" }}>
          {reg.entrada}
        </td>

        {/* Columna Salida: Naranja si no ha salido, Gris si ya salió */}
        <td style={{ padding: "12px", color: reg.salida.includes("Aún") ? "#e37400" : "#555" }}>
          {reg.salida}
        </td>
      </tr>
    ))}
  </tbody>
</table>
      )}
    </div>
  );
}