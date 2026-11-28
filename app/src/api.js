// api.js - todas las llamadas a la API de GestorMaterial (con fetch)

// Alumno: Elías Martínez
// Está todo en un fichero para tenerlo localizado. 
// Cada función devuelve el JSON que manda la API, o lanza un Error con un mensaje para enseñar al usuario.
// El error lleva también "status" con el código HTTP (0 = no se pudo conectar).

// *A TENER EN CUENTA: este fichero no usa nada de React Native, solo fetch.

import { tipoDeQr, limpiarCodigo } from './qr.js';

let urlBase = ''; // dirección de la API, por ejemplo http://192.168.1.20:8000
let token = null; // token JWT del usuario que ha iniciado sesión
let alCaducar = null; // función que se llama si la API contesta 401 con un token puesto

const TIEMPO_MAXIMO = 8000; // si la API no contesta en 8 segundos, doy error

//AJUSTES
// *Las direciones quedan muy mal en la pantalla de la app. buscar si se pueden ocultar o poner en otra línea:

export function getUrlBase() {
  return urlBase;
}

export function setToken(nuevo) {
  token = nuevo;
}

export function setAlCaducar(funcion) {
  alCaducar = funcion;
}

//PETICIONES:

//Sale el mensaje de error que ha mandado la API (FastAPI lo manda en "detail")

function textoDeError(datos, status) {
  if (datos && typeof datos.detail === 'string') {
    return datos.detail;
  }
  if (status === 422) {
    return 'Los datos enviados no son válidos.';
  }
  return 'Error del servidor (' + status + ').';
}

async function peticion(metodo, ruta, cuerpo) {
  if (urlBase === '') {
    const err = new Error('Falta la dirección del servidor. Escríbela en el apartado "Servidor".');
    err.status = 0;
    throw err;
  }


  const cabeceras = { 'Content-Type': 'application/json' };
  if (token) {
    cabeceras['Authorization'] = 'Bearer ' + token; // así lo espera seguridad.py en la API
  }

  let respuesta;
  try {
    respuesta = await fetch(urlBase + ruta, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
      signal: control.signal,
    });
  } catch (e) {
    clearTimeout(temporizador);
    const err = new Error(
      'No se puede conectar con el servidor. Comprueba la dirección y que el móvil esté en la misma wifi que el ordenador.'
    );
    err.status = 0;
    throw err;
  }
  clearTimeout(temporizador);

  // Para leer el JSON de la respuesta (puede que no venga nada)
  let datos = null;
  try {
    datos = await respuesta.json();
  } catch (e) {
    // Respuesta sin JSON, no pasa nada
  }

  if (!respuesta.ok) {
    const err = new Error(textoDeError(datos, respuesta.status));
    err.status = respuesta.status;
    // 401 con un token puesto = el token ha caducado o no vale: aviso a la app para cerrar sesión
    if (respuesta.status === 401 && token && alCaducar) {
      alCaducar();
    }
    throw err;
  }
  return datos;
}

// LOGIN Y USUARIO:

export function probarConexion() {
  return peticion('GET', '/'); // la ruta "/" de la API solo dice que está funcionando
}

export function login(email, password) {
  return peticion('POST', '/auth/login', { email: email, password: password });
}

export function yo() {
  return peticion('GET', '/auth/me');
}

// CATALOGO:

export function listarCategorias() {
  return peticion('GET', '/categorias');
}

export function listarArticulos(buscar, tipo) {
  const parametros = [];
  if (buscar) {
    parametros.push('buscar=' + encodeURIComponent(buscar));
  }
  if (tipo) {
    parametros.push('tipo=' + encodeURIComponent(tipo));
  }
  const texto = parametros.length > 0 ? '?' + parametros.join('&') : '';
  return peticion('GET', '/articulos' + texto);
}

//CONSUMIBLES:

export function consumiblePorQr(codigo) {
  return peticion('GET', '/consumibles/qr/' + encodeURIComponent(limpiarCodigo(codigo)));
}

// cantidad positiva = añadir stock, negativa = gastar (botones +1 y -1)
export function moverStock(idArticulo, cantidad) {
  return peticion('POST', '/consumibles/' + idArticulo + '/movimiento', { cantidad: cantidad });
}

export function historialConsumible(idArticulo) {
  return peticion('GET', '/consumibles/' + idArticulo + '/historial'); // solo administrador
}

// MAQUINAS:

export function maquinaPorQr(codigo) {
  return peticion('GET', '/maquinas/qr/' + encodeURIComponent(limpiarCodigo(codigo)));
}


// Las incidencia son un texto opcional: si hay texto, la máquina pasa a mantenimiento
export function devolverMaquina(idMaquina, incidencia) {
  return peticion('POST', '/maquinas/' + idMaquina + '/devolucion', { incidencia: incidencia || null });
}

// INCIDENCIAS: (administrador)

// Resuelta: true, false o undefined (todas)
export function listarIncidencias(resuelta) {
  const texto = resuelta === undefined ? '' : '?resuelta=' + (resuelta ? 'true' : 'false');
  return peticion('GET', '/incidencias' + texto);
}

export function resolverIncidencia(idIncidencia) {
  return peticion('PUT', '/incidencias/' + idIncidencia + '/resolver');
}

// ESCANER

// según el prefijo del QR (CON- o MAQ-) busco en un sitio o en otro
// devuelve tipo: 'consumible' o 'maquina'. Si no encaja, error con mensaje para el usuario.

export async function buscarPorQr(codigo) {
  const tipo = tipoDeQr(codigo);
  if (tipo === 'consumible') {
    return { tipo: tipo, datos: await consumiblePorQr(codigo) };
  }
  if (tipo === 'maquina') {
    return { tipo: tipo, datos: await maquinaPorQr(codigo) };
  }
  const err = new Error('Este código no es de GestorMaterial. Los códigos empiezan por CON- (consumible) o MAQ- (máquina).');
  err.status = 0;
  throw err;
}
