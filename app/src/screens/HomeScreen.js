// HomeScreen.js - pantalla de inicio después del login

// Alumno: Elías Martínez
// El botón de escanear va abajo y grande, para poder pulsarlo con el pulgar.

import { useContext } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { SesionContext } from '../sesion';
import { colores, estilos } from '../tema';
import Boton from '../Boton';
import { getUrlBase } from '../api';

export default function HomeScreen({ navigation }) {
  const { sesion, cerrarSesion } = useContext(SesionContext);
  const insets = useSafeAreaInsets();
  const esAdmin = sesion.rol === 'administrador';

  return (
    <View style={[estilos.pantalla, { paddingTop: insets.top + 32, paddingBottom: insets.bottom + 20, paddingHorizontal: 24 }]}>
      {/* arriba: quién ha entrado */}
      <View>
        <Text style={estilos.titulo}>Hola, {sesion.nombre}</Text>
        <Text style={[estilos.textoSecundario, { marginTop: 6 }]}>{esAdmin ? 'Administrador' : 'Operario'}</Text>
      </View>

      {/* en medio: el botón principal, que es lo que más se usa */}
      <View style={{ flex: 1, justifyContent: 'flex-end', paddingBottom: 20 }}>
        <Boton
          texto="Escanear QR"
          tipo="acento"
          onPress={() => navigation.navigate('Escaner')}
          style={propios.botonEscanear}
          estiloTexto={{ fontSize: 28 }}
        />
      </View>

      {/* abajo: cerrar sesión y la dirección del servidor */}
      <Boton texto="Cerrar sesión" tipo="secundario" onPress={cerrarSesion} />
      <Text style={[estilos.textoSecundario, { marginTop: 12, textAlign: 'center', fontSize: 13 }]}>
        Servidor: {getUrlBase()}
      </Text>
    </View>
  );
}

const propios = StyleSheet.create({
  botonEscanear: {
    minHeight: 150, // botón muy grande
    borderRadius: 20,
    backgroundColor: colores.amarillo,
  },
});
