
# seguridad.py - Autenticación por tokens JWT, contraseñas y comprobación de roles.

# Fuente: documentación oficial de FastAPI, "OAuth2 with Password (and hashing), Bearer with JWT tokens" https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# Lo he adaptado: uso HTTPBearer en vez de OAuth2PasswordBearer, el login va con JSON y compruebo las contraseñas con bcrypt directamente.

import os
import datetime  # para poner la fecha de caducidad al token
import bcrypt  # para comprobar las contraseñas con hash
import jwt  # PyJWT, para crear y leer los tokens
from dotenv import load_dotenv
from fastapi import Depends, HTTPException  # Depends sirve para que FastAPI nos pase el usuario logueado
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

# clave para firmar los tokens. La saco del .env, si no está uso la de clase
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_de_clase")
ALGORITMO = "HS256"  # el algoritmo que usamos en clase
HORAS_TOKEN = 24  # el token dura un día y luego hay que volver a hacer login


# esto le dice a FastAPI que el token viene en la cabecera "Authorization: Bearer <token>" y de paso sale el botón "Authorize" en /docs para probar
esquema_bearer = HTTPBearer()

def comprobar_password(password_plano, password_hash):
    # compara la contraseña que escribe el usuario con el hash de la base de datos
    # bcrypt trabaja con bytes, por eso el encode()
    return bcrypt.checkpw(password_plano.encode('utf-8'), password_hash.encode('utf-8'))
    # Se especifica utf-8 para que no falle con tildes o eñes


def crear_token(id_usuario, nombre, rol):
    # datos que van dentro del token
    datos = {
        "sub": str(id_usuario),  # el id del usuario (tiene que ser texto)
        "nombre": nombre,
        "rol": rol,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=HORAS_TOKEN),  # cuándo caduca
    }
    # firmo el token con la clave secreta y lo devuelvo
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO)


def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer)):
    # esta función la usan todos los endpoints que necesitan estar logueado
    token = credenciales.credentials  # saco el token de la cabecera
    try:
        datos = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])  # lo descifro y compruebo la firma
        # devuelvo un diccionario con lo que me interesa del usuario
        return {
            "id_usuario": int(datos["sub"]),
            "nombre": datos["nombre"],
            "rol": datos["rol"],
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha caducado, vuelve a iniciar sesión")
    except Exception as e:
        print("Error al leer el token:", e)  # lo saco por consola para ver qué pasa
        raise HTTPException(status_code=401, detail="Token no válido")


def solo_admin(usuario=Depends(usuario_actual)):
    # igual que usuario_actual pero además comprueba que sea administrador
    if usuario["rol"] != "administrador":
        raise HTTPException(status_code=403, detail="Solo el administrador puede hacer esto")
    return usuario

# OJO: el token no comprueba si el usuario sigue activo en la BD, si bloqueo a alguien
# puede seguir usando su token hasta que caduque.
# TODO: mirar si se arregla consultando la BD en usuario_actual
