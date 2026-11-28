// tema.js - colores y estilos que se repiten en varias pantallas
// Alumno: Elías Martínez
// Colores pensados para un taller: mucho contraste y botones grandes, porque el operario puede llevar guantes o tener una mano ocupada.

import { StyleSheet } from 'react-native';

export const colores = {
  tinta: '#1B2430', // texto principal
  fondo: '#F5F6F8', // fondo de las pantallas
  blanco: '#FFFFFF',
  azul: '#1D4E89', // botones principales
  amarillo: '#F2B705', // el botón de escanear, que es lo más importante
  gris: '#5B6573', // texto secundario
  borde: '#D9DEE5',
  error: '#B3261E', //se reserva el "tipico rojo" solo para los errores que se muestran al usuario
  errorFondo: '#FBE9E7',
};

// un color para cada estado de una máquina
export const coloresEstado = {
  disponible: '#2E7D32',
  en_uso: '#1D4E89',
  en_mantenimiento: '#B45309',
  reservada: '#6B5B95',
};

// estilos que uso en varias pantallas
export const estilos = StyleSheet.create({
  pantalla: {
    flex: 1,
    backgroundColor: colores.fondo,
  },
  titulo: {
    fontSize: 30,
    fontWeight: '800',
    color: colores.tinta,
  },
  texto: {
    fontSize: 17,
    color: colores.tinta,
  },
  textoSecundario: {
    fontSize: 15,
    color: colores.gris,
  },
  input: {
    height: 56,
    borderWidth: 2,
    borderColor: colores.borde,
    borderRadius: 12,
    backgroundColor: colores.blanco,
    paddingHorizontal: 16,
    fontSize: 18,
    color: colores.tinta,
  },
  cajaError: {
    backgroundColor: colores.errorFondo,
    borderRadius: 12,
    padding: 14,
  },
  textoError: {
    fontSize: 16,
    color: colores.error,
  },
});
