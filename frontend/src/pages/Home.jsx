export default function Home() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
      <div style={{
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03)",
        border: "1px solid #e2e8f0",
        padding: "50px",
        textAlign: "center",
        maxWidth: "600px",
        width: "100%"
      }}>
        <h1 style={{ color: "#1e293b", margin: "0 0 15px 0", fontSize: "2.2rem" }}>Panel de Control</h1>
        <p style={{ color: "#64748b", fontSize: "1.1rem", lineHeight: "1.6", margin: 0 }}>
          Sistema de gestión de asistencia por reconocimiento facial. Seleccione una opción en el menú superior para comenzar a operar.
        </p>
      </div>
    </div>
  );
}