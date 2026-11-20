// App.js - punto de entrada de la app GestorMaterial
// Alumno: Elías Martínez
//
// Aquí se decide qué pantallas se ven:
//   - sin sesión iniciada -> solo la pantalla de login
//   - con sesión iniciada -> inicio y escáner (y las que vayan llegando)

import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { DefaultTheme, NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { URL_API_POR_DEFECTO } from './src/config';
import { colores } from './src/tema';
import { setAlCaducar, setToken, setUrlBase } from './src/api';


const Stack = createNativeStackNavigator();

// tema de la navegación con el color de fondo de la app
const temaNavegacion = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, background: colores.fondo },
};

export default function App() {
  const [sesion, setSesion] = useState(null); // { token, nombre, rol, id_usuario } o null
  const [aviso, setAviso] = useState(''); // mensaje para el login (por ejemplo "sesión caducada")

  // esto se ejecuta una sola vez, al abrir la app
  useEffect(() => {
    async function arrancar() {
      // dirección de la API: la guardada o, si no hay, la de config.js
      const urlGuardada = await leerUrl();

      setCargando(false);
    }
    arrancar();
  }, []);

  // guarda la sesión al hacer login
  async function iniciarSesion(datos) {
    await guardarSesion(datos);
    setToken(datos.token);
    setAviso('');
    setSesion(datos);
  }

  // borra la sesión al pulsar "Cerrar sesión"
  async function cerrarSesion() {
    await borrarSesion();
    setToken(null);
    setSesion(null);
  }


  return (
    <SesionContext.Provider value={{ sesion, aviso, iniciarSesion, cerrarSesion, borrarAviso: () => setAviso('') }}>
      <NavigationContainer theme={temaNavegacion}>
        <StatusBar style="dark" />
        <Stack.Navigator>
          {sesion === null ? (
            // sin sesión: solo el login
            <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
          ) : (
            // con sesión: el resto de pantallas
            <>
              <Stack.Screen name="Inicio" component={HomeScreen} options={{ headerShown: false }} />
              <Stack.Screen
                name="Escaner"
                component={EscanerScreen}
                options={{
                  title: 'Escanear QR',
                  headerStyle: { backgroundColor: colores.azul },
                  headerTintColor: colores.blanco,
                }}
              />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SesionContext.Provider>
  );
}
