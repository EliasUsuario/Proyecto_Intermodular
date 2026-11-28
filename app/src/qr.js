// qr.js - saber de qué tipo es un código QR
// Alumno: Elías Martínez
//
// Los QR de GestorMaterial empiezan por un prefijo:
//   CON-0001  -> consumible (material a granel)
//   MAQ-0001  -> máquina o herramienta (una unidad concreta)
// *A TENER EN CUENTA: las etiquetas QR reales que se impriman tienen que seguir esta regla.


// devuelve 'consumible', 'maquina' o null si el código no es de GestorMaterial
export function tipoDeQr(texto) {
  const codigo = limpiarCodigo(texto).toUpperCase(); // paso a mayúsculas para comparar
  if (codigo.startsWith('CON-')) {
    return 'consumible';
  }
  if (codigo.startsWith('MAQ-')) {
    return 'maquina';
  }
  return null; // no empieza por ninguno de los dos
}
