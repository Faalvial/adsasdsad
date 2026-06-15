import React from 'react';

// Generador de números pseudoaleatorios simple (Linear Congruential Generator)
const lcg = (seed) => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

export default function Identicon({ value, size = 40, gridSize = 5, bg = "#f8fafc" }) {
  if (!value) return null;

  // 1. Generar un hash matemático del DNI (o cualquier string)
  let hash = 0;
  const str = String(value);
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  hash = Math.abs(hash);

  // 2. Inicializar generador pseudoaleatorio con la semilla (hash)
  const random = lcg(hash === 0 ? 1 : hash);

  // 3. Determinar el color único para esa persona
  const color = `hsl(${Math.floor(random() * 360)}, 65%, 55%)`;

  // 4. Calcular el patrón del bloque base (mitad izquierda)
  const cols = Math.ceil(gridSize / 2);
  const bits = [];
  for (let i = 0; i < cols * gridSize; i++) {
    bits.push(random() > 0.5); // ¿Se pinta o no se pinta el cuadrito?
  }

  // 5. Dibujar el SVG simétrico
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox={`-0.5 -0.5 ${gridSize + 1} ${gridSize + 1}`} 
      style={{ backgroundColor: bg, borderRadius: "6px", minWidth: size }}
    >
      {Array.from({ length: gridSize * gridSize }).map((_, i) => {
        const fila = Math.floor(i / gridSize);
        const col = i % gridSize;
        
        // Magia simétrica: si estamos en la mitad derecha, leemos el patrón de la izquierda
        const colReflejada = col < cols ? col : gridSize - 1 - col;
        const estaPintado = bits[fila * cols + colReflejada];

        return estaPintado ? <rect key={i} x={col} y={fila} width="1" height="1" fill={color} /> : null;
      })}
    </svg>
  );
}
