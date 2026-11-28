// almacen.js - guardar datos en el móvil para la próxima vez que se abra la app

// Alumno: Elías Martínez
// Uso AsyncStorage, que guarda texto con una clave.

import AsyncStorage from '@react-native-async-storage/async-storage';

const CLAVE_SESION = 'gm_sesion';
const CLAVE_URL = 'gm_url_api';

// guarda la sesión: { token, nombre, rol, id_usuario }
export async function guardarSesion(sesion) {
  try {
    await AsyncStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
  } catch (e) {
    console.log('No se pudo guardar la sesión:', e);
  }
}

// lee la sesión guardada, o null si no hay ninguna
export async function leerSesion() {
  try {
    const texto = await AsyncStorage.getItem(CLAVE_SESION);
    return texto ? JSON.parse(texto) : null;
  } catch (e) {
    console.log('No se pudo leer la sesión:', e);
    return null;
  }
}

export async function borrarSesion() {
  try {
    await AsyncStorage.removeItem(CLAVE_SESION);
  } catch (e) {
    console.log('No se pudo borrar la sesión:', e);
  }
}

// guarda la dirección de la API que ha escrito el usuario
export async function guardarUrl(url) {
  try {
    await AsyncStorage.setItem(CLAVE_URL, url);
  } catch (e) {
    console.log('No se pudo guardar la dirección:', e);
  }
}

export async function leerUrl() {
  try {
    return await AsyncStorage.getItem(CLAVE_URL);
  } catch (e) {
    console.log('No se pudo leer la dirección:', e);
    return null;
  }
}
