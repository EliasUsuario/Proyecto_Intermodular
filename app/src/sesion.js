// sesion.js - contexto para que todas las pantallas sepan quién ha iniciado sesión
// Alumno: Elías Martínez
// (el contexto es lo que vimos para no pasar los datos pantalla por pantalla)

import { createContext } from 'react';

// valor que guarda: { sesion, aviso, iniciarSesion, cerrarSesion, borrarAviso }
export const SesionContext = createContext(null);
