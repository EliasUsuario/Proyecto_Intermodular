// Boton.js - botón grande reutilizable
// Alumno: Elías Martínez
// tipo: 'principal' (azul), 'acento' (amarillo) o 'secundario' (solo borde)

import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';
import { colores } from './tema';

export default function Boton({ texto, onPress, tipo = 'principal', deshabilitado = false, cargando = false, style, estiloTexto }) {
  // si está cargando o deshabilitado no se puede pulsar
  const bloqueado = deshabilitado || cargando;

  // color de fondo y de texto según el tipo
  let fondo = 'transparent';
  let colorTexto = colores.tinta;
  if (tipo === 'principal') {
    fondo = colores.azul;
    colorTexto = colores.blanco;
  } else if (tipo === 'acento') {
    fondo = colores.amarillo;
  }

  return (
    <Pressable
      onPress={onPress}
      disabled={bloqueado}
      accessibilityRole="button"
      accessibilityLabel={texto}
      style={({ pressed }) => [
        estilos.boton,
        { backgroundColor: fondo, opacity: bloqueado ? 0.5 : pressed ? 0.85 : 1 },
        tipo === 'secundario' && estilos.secundario,
        style,
      ]}
    >
      {cargando ? (
        <ActivityIndicator color={colorTexto} />
      ) : (
        <Text style={[estilos.texto, { color: colorTexto }, estiloTexto]}>{texto}</Text>
      )}
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  boton: {
    minHeight: 58, // alto para poder pulsarlo con el pulgar y con guantes
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  secundario: {
    borderWidth: 2,
    borderColor: colores.borde,
  },
  texto: {
    fontSize: 18,
    fontWeight: '700',
  },
});
