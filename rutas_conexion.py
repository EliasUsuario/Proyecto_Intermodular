# Alumno: Elías Martínez | 2º DAM

#   POST /auth/login  -> iniciar sesión, devuelve el token
#   GET  /auth/me     -> datos del usuario logueado (para saber su rol en la app)


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel  # para definir qué datos llegan en el body
from conexion import conectar
from seguridad import comprobar_password, crear_token, usuario_actual

# router con prefijo /auth, así no lo repito en cada ruta.
router = APIRouter(prefix="/auth", tags=["Autenticación"])

# modelo de los datos que manda la app al hacer login
class LoginDatos(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(datos: LoginDatos):
    conn = conectar()  # abro conexión
    try:
        cur = conn.cursor()  # cursor para ejecutar la consulta
        # busco al usuario por su email (con %s para que no haya inyección SQL)
        cur.execute(
            "SELECT id_usuario, nombre, password_hash, rol, activo FROM usuarios WHERE email = %s",
            (datos.email,),
        )
        usuario = cur.fetchone()  # si no existe devuelve None

        # si no existe o la contraseña está mal, mismo mensaje para los dos casos
        if usuario is None or not comprobar_password(datos.password, usuario["password_hash"]):
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

        # si el usuario está desactivado no le dejo entrar
        if not usuario["activo"]:
            raise HTTPException(status_code=403, detail="Usuario desactivado")

        # creo el token con sus datos
        token = crear_token(usuario["id_usuario"], usuario["nombre"], usuario["rol"])

        # devuelvo el token y los datos que necesita la app
        return {
            "access_token": token,
            "token_type": "bearer",
            "nombre": usuario["nombre"],
            "rol": usuario["rol"],
        }
    except HTTPException as e:
        #** esto me dio guerra: si no lo pongo, el "except Exception" de abajo se come los errores 401/403 y siempre devuelve 500
        raise e
    except Exception as e:
        print("Error en login:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()  # cierro la conexión pase lo que pase


@router.get("/me")
def me(usuario=Depends(usuario_actual)):
    # usuario_actual ya ha comprobado el token, solo devuelvo lo que trae
    return usuario