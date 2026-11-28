// formato.js - funciones para mostrar los "datos bonitos" en pantalla

// Alumno: Elías Martínez

// nombre que se enseña al usuario para cada estado de una máquina
const etiquetasEstado = {
  disponible: 'Disponible',
  en_uso: 'En uso',
  en_mantenimiento: 'En mantenimiento',
  reservada: 'Reservada por gerencia',
};

export function etiquetaEstado(estado) {
  // si llega un estado que no conozco, enseño tal cual viene
  return etiquetasEstado[estado] || estado;
}

// convierte la fecha que manda la API (2026-10-27T19:35:00) en algo como "27/10, 19:35"
export function formatearFecha(texto) {
  if (!texto) {
    return '';
  }
  if (isNaN(fecha.getTime())) {
    return ''; // la fecha no era válida
  }
  return fecha.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
