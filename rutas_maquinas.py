# rutas_maquinas.py - maquinaria (activos únicos) y préstamos
# Alumno: Elías Martínez

#   GET  /maquinas/qr/{codigo_qr}   = buscar una unidad escaneando su QR (cualquier usuario)
#   GET  /maquinas                  = listar unidades, con ?estado= ?id_articulo= ?mias=true (cualquier usuario)
#   POST /maquinas                  = dar de alta una unidad física (solo admin)
#   POST /maquinas/{id}/prestamo    = coger una máquina (cualquier usuario)
#   POST /maquinas/{id}/devolucion  = devolverla, con incidencia opcional (el titular o un admin)



from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from conexion import conectar
from seguridad import usuario_actual, solo_admin

router = APIRouter(tags=["Maquinaria"])

# estados que puede tener una máquina (los mismos que el CHECK de la tabla)
ESTADOS = ("disponible", "en_uso", "en_mantenimiento", "reservada")

# consulta base de las máquinas, la uso en el QR y en el listado
# el LEFT JOIN con prestamos (solo los abiertos) saca quién la tiene ahora mismo (como solo puede haber un préstamo abierto por máquina, no salen filas repetidas)
SQL_MAQUINAS = """
    SELECT m.id_maquina, m.id_articulo, a.nombre, a.descripcion, c.nombre AS categoria,
           m.numero_serie, m.codigo_qr, m.estado, a.activo,
           p.id_prestamo, p.fecha_salida, p.id_usuario AS id_usuario_titular, u.nombre AS titular
    FROM maquinas m
    JOIN articulos a ON a.id_articulo = m.id_articulo
    LEFT JOIN categorias c ON c.id_categoria = a.id_categoria
    LEFT JOIN prestamos p ON p.id_maquina = m.id_maquina AND p.fecha_devolucion IS NULL
    LEFT JOIN usuarios u ON u.id_usuario = p.id_usuario
    WHERE 1 = 1
"""


# datos para dar de alta una unidad
class MaquinaNueva(BaseModel):
    id_articulo: int
    codigo_qr: str
    numero_serie: Optional[str] = None


# datos al devolver una máquina
class DevolucionDatos(BaseModel):
    incidencia: Optional[str] = None  # texto si la máquina ha sufrido daños


# *A TENER EN CUENTA: esta ruta tiene que ir antes que las de /maquinas/{id}/...
@router.get("/maquinas/qr/{codigo_qr}")
def buscar_maquina_por_qr(codigo_qr: str, usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()
        sql = SQL_MAQUINAS + " AND m.codigo_qr = %s"
        # el operario no ve el material bloqueado
        if usuario["rol"] != "administrador":
            sql += " AND a.activo = TRUE"
        cur.execute(sql, (codigo_qr,))
        maquina = cur.fetchone()

        if maquina is None:
            raise HTTPException(status_code=404, detail="No existe ninguna máquina con ese QR")
        return maquina
    except HTTPException as e:
        raise e  # si no, el except de abajo se come el 404
    except Exception as e:
        print("Error al buscar máquina por QR:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.get("/maquinas")
def listar_maquinas(estado: Optional[str] = None, id_articulo: Optional[int] = None,
                    mias: bool = False, usuario=Depends(usuario_actual)):
    # compruebo que el estado que piden existe
    if estado is not None and estado not in ESTADOS:
        raise HTTPException(status_code=400, detail="Estado no válido")

    conn = conectar()
    try:
        cur = conn.cursor()
        sql = SQL_MAQUINAS
        params = []

        # el operario no ve el material bloqueado, el admin lo ve todo
        if usuario["rol"] != "administrador":
            sql += " AND a.activo = TRUE"

        if estado is not None:
            sql += " AND m.estado = %s"
            params.append(estado)

        if id_articulo is not None:
            sql += " AND m.id_articulo = %s"
            params.append(id_articulo)

        # mias=true -> solo las máquinas que tiene ahora mismo el usuario logueado
        if mias:
            sql += " AND p.id_usuario = %s"
            params.append(usuario["id_usuario"])

        sql += " ORDER BY a.nombre, m.codigo_qr"
        cur.execute(sql, params)
        return cur.fetchall()
    except Exception as e:
        print("Error al listar máquinas:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.post("/maquinas", status_code=201)
def crear_maquina(datos: MaquinaNueva, usuario=Depends(solo_admin)):
    if not datos.codigo_qr.strip():
        raise HTTPException(status_code=400, detail="El codigo_qr no puede estar vacío")

    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que el artículo existe y que es de tipo maquinaria
        cur.execute("SELECT tipo FROM articulos WHERE id_articulo = %s", (datos.id_articulo,))
        articulo = cur.fetchone()
        if articulo is None:
            raise HTTPException(status_code=400, detail="El artículo no existe")
        if articulo["tipo"] != "maquinaria":
            raise HTTPException(status_code=400, detail="El artículo no es de tipo maquinaria")

        # compruebo que el QR no esté repetido
        cur.execute("SELECT 1 FROM maquinas WHERE codigo_qr = %s", (datos.codigo_qr,))
        if cur.fetchone() is not None:
            raise HTTPException(status_code=400, detail="Ya existe una máquina con ese QR")

        # y el número de serie, si han mandado uno
        if datos.numero_serie:
            cur.execute("SELECT 1 FROM maquinas WHERE numero_serie = %s", (datos.numero_serie,))
            if cur.fetchone() is not None:
                raise HTTPException(status_code=400, detail="Ya existe una máquina con ese número de serie")

        # la unidad nueva empieza siempre como disponible (es el valor por defecto de la tabla)
        cur.execute(
            """INSERT INTO maquinas (id_articulo, numero_serie, codigo_qr)
               VALUES (%s, %s, %s) RETURNING id_maquina""",
            (datos.id_articulo, datos.numero_serie or None, datos.codigo_qr),
        )
        aux = cur.fetchone()
        conn.commit()
        return {"mensaje": "Máquina creada", "id_maquina": aux["id_maquina"]}
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        print("Error al crear máquina:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.post("/maquinas/{id_maquina}/prestamo", status_code=201)
def coger_maquina(id_maquina: int, usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que la máquina existe y si su artículo está bloqueado
        cur.execute(
            """SELECT a.activo
               FROM maquinas m
               JOIN articulos a ON a.id_articulo = m.id_articulo
               WHERE m.id_maquina = %s""",
            (id_maquina,),
        )
        aux = cur.fetchone()
        # si no existe, o está bloqueada y no es admin, digo que no existe
        if aux is None or (not aux["activo"] and usuario["rol"] != "administrador"):
            raise HTTPException(status_code=404, detail="Máquina no encontrada")

        # Cambio el estado a 'en_uso' con UN SOLO UPDATE que solo funciona si sigue 'disponible'. 
        # Así, si dos personas la escanean a la vez, solo una se la queda.
        cur.execute(
            """UPDATE maquinas SET estado = 'en_uso'
               WHERE id_maquina = %s AND estado = 'disponible'
               RETURNING id_maquina""",
            (id_maquina,),
        )
        if cur.fetchone() is None:
            # no estaba disponible: miro por qué para decírselo al usuario
            cur.execute("SELECT estado FROM maquinas WHERE id_maquina = %s", (id_maquina,))
            estado = cur.fetchone()["estado"]

            if estado == "en_uso":
                # saco quién la tiene
                cur.execute(
                    """SELECT p.id_usuario, u.nombre
                       FROM prestamos p
                       JOIN usuarios u ON u.id_usuario = p.id_usuario
                       WHERE p.id_maquina = %s AND p.fecha_devolucion IS NULL""",
                    (id_maquina,),
                )
                titular = cur.fetchone()
                if titular is not None and titular["id_usuario"] == usuario["id_usuario"]:
                    mensaje = "Ya tienes esta máquina asignada"
                elif titular is not None:
                    mensaje = "Esta máquina la tiene " + titular["nombre"]
                else:
                    mensaje = "Esta máquina ya está en uso"
            elif estado == "reservada":
                mensaje = "Esta máquina está reservada por gerencia"
            elif estado == "en_mantenimiento":
                mensaje = "Esta máquina está en mantenimiento"
            else:
                mensaje = "No se ha podido coger la máquina, inténtalo otra vez"
            raise HTTPException(status_code=400, detail=mensaje)

        # registro el préstamo (fecha_salida se pone sola con NOW())
        cur.execute(
            "INSERT INTO prestamos (id_maquina, id_usuario) VALUES (%s, %s) RETURNING id_prestamo",
            (id_maquina, usuario["id_usuario"]),
        )
        aux = cur.fetchone()

        conn.commit()  # guardo el UPDATE y el INSERT a la vez
        return {"mensaje": "Máquina asignada", "id_prestamo": aux["id_prestamo"], "estado": "en_uso"}
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        print("Error al coger máquina:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.post("/maquinas/{id_maquina}/devolucion")
def devolver_maquina(id_maquina: int, datos: DevolucionDatos, usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que la máquina existe
        cur.execute("SELECT 1 FROM maquinas WHERE id_maquina = %s", (id_maquina,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Máquina no encontrada")

        # busco el préstamo abierto (el que no tiene fecha de devolución)
        cur.execute(
            "SELECT id_prestamo, id_usuario FROM prestamos WHERE id_maquina = %s AND fecha_devolucion IS NULL",
            (id_maquina,),
        )
        prestamo = cur.fetchone()
        if prestamo is None:
            raise HTTPException(status_code=400, detail="Esta máquina no está prestada")

        # solo la puede devolver quien la tiene o un administrador
        if prestamo["id_usuario"] != usuario["id_usuario"] and usuario["rol"] != "administrador":
            raise HTTPException(status_code=403, detail="Esta máquina la tiene otro usuario")

        # cierro el préstamo; la condición fecha_devolucion IS NULL evita cerrarlo dos veces
        cur.execute(
            """UPDATE prestamos SET fecha_devolucion = NOW()
               WHERE id_prestamo = %s AND fecha_devolucion IS NULL
               RETURNING id_prestamo""",
            (prestamo["id_prestamo"],),
        )
        if cur.fetchone() is None:
            raise HTTPException(status_code=400, detail="Esta máquina ya se ha devuelto")

        # si han escrito una incidencia (quitando espacios) la guardo y la máquina pasa a mantenimiento
        texto = (datos.incidencia or "").strip()
        if texto != "":
            cur.execute(
                "INSERT INTO incidencias (id_prestamo, descripcion) VALUES (%s, %s)",
                (prestamo["id_prestamo"], texto),
            )
            nuevo_estado = "en_mantenimiento"
        else:
            nuevo_estado = "disponible"

        cur.execute("UPDATE maquinas SET estado = %s WHERE id_maquina = %s", (nuevo_estado, id_maquina))

        conn.commit()
        return {
            "mensaje": "Máquina devuelta",
            "estado": nuevo_estado,
            "con_incidencia": texto != "",
        }
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        print("Error al devolver máquina:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()
# *A TENER EN CUENTA (fase 2): cambiar una máquina a 'reservada' (y quitarle la reserva) lo hará el admin
# con las reservas. Aquí solo cambia de estado con el préstamo, la devolución y las incidencias.
