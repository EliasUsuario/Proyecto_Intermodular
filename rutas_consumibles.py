# Alumno: Elías Martínez | 2º DAM

#   GET/consumibles/qr/{codigo_qr}      =   buscar un consumible escaneando su QR (cualquier usuario)
#   POST/consumibles/{id}/movimiento    =   sumar o restar stock, botones +1 / -1 (cualquier usuario)
#   GET/consumibles/{id}/historial      =   histórico de movimientos (solo admin)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from conexion import conectar
from seguridad import usuario_actual, solo_admin
from rutas_articulos import SQL_ARTICULOS  # reutilizo la consulta del catálogo (Sustituyo la concatenación de cadenas (str) por (%s) para evitar inyecciones SQL)

router = APIRouter(tags=["Consumibles"])


# datos que manda la app al pulsar +1 / -1
class MovimientoDatos(BaseModel):
    cantidad: int  # positivo = añadir stock, negativo = gastar (el botón +1 manda 1 y el -1 manda -1)


# **A TENER EN CUENTA: esta ruta tiene que ir antes que las de /consumibles/{id}/...
@router.get("/consumibles/qr/{codigo_qr}")
def buscar_por_qr(codigo_qr: str, usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()
        # parto de la consulta del catálogo y filtro por el QR (solo los consumibles tienen codigo_qr en esa tabla, una máquina no sale aquí)
        sql = SQL_ARTICULOS + " AND co.codigo_qr = %s"
        # el operario no ve el material bloqueado
        if usuario["rol"] != "administrador":
            sql += " AND a.activo = TRUE"
        cur.execute(sql, (codigo_qr,))
        consumible = cur.fetchone()

        if consumible is None:
            raise HTTPException(status_code=404, detail="No existe ningún consumible con ese QR")

        # añado cuánto se puede coger de verdad (stock menos lo reservado por gerencia)
        consumible["disponible"] = consumible["stock_actual"] - consumible["stock_reservado"]
        return consumible
    except HTTPException as e:
        raise e  # **si no, el except de abajo se come el 404
    except Exception as e:
        print("Error al buscar por QR:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.post("/consumibles/{id_articulo}/movimiento")
def registrar_movimiento(id_articulo: int, datos: MovimientoDatos, usuario=Depends(usuario_actual)):
    # una cantidad de 0 no tiene sentido
    if datos.cantidad == 0:
        raise HTTPException(status_code=400, detail="La cantidad no puede ser 0")

    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que el consumible existe y miro si está bloqueado
        cur.execute(
            """SELECT a.activo
               FROM consumibles co
               JOIN articulos a ON a.id_articulo = co.id_articulo
               WHERE co.id_articulo = %s""",
            (id_articulo,),
        )
        aux = cur.fetchone()
        # si no existe, o está bloqueado y quien lo pide no es admin, digo que no existe
        if aux is None or (not aux["activo"] and usuario["rol"] != "administrador"):
            raise HTTPException(status_code=404, detail="Consumible no encontrado")

        # Actualizo el stock con un solo UPDATE que lleva la condición dentro (solo se hace si después de sumar la cantidad queda stock >= reservado).
        # (Así, si dos operarios restan a la vez, no se puede gastar más de lo disponible).
        cur.execute(
            """UPDATE consumibles
               SET stock_actual = stock_actual + %s
               WHERE id_articulo = %s
                 AND stock_actual + %s - stock_reservado >= 0
               RETURNING stock_actual, stock_minimo, stock_reservado""",
            (datos.cantidad, id_articulo, datos.cantidad),
        )
        fila = cur.fetchone()

        # si no ha actualizado ninguna fila es que no hay stock disponible suficiente
        if fila is None:
            cur.execute(
                "SELECT stock_actual, stock_reservado FROM consumibles WHERE id_articulo = %s",
                (id_articulo,),
            )
            stock = cur.fetchone()
            disponible = stock["stock_actual"] - stock["stock_reservado"]
            raise HTTPException(
                status_code=400,
                detail="No hay stock suficiente: disponible " + str(disponible)
                + " (hay " + str(stock["stock_actual"]) + " y " + str(stock["stock_reservado"]) + " están reservados)",
            )

        # guardo el movimiento en el histórico (quién, cuánto y cuándo)
        cur.execute(
            "INSERT INTO movimientos_consumible (id_articulo, id_usuario, cantidad) VALUES (%s, %s, %s)",
            (id_articulo, usuario["id_usuario"], datos.cantidad),
        )

        conn.commit()  # guardo el UPDATE y el INSERT a la vez

        # Devuelvo el stock nuevo para que la app lo "pinte" sin volver a pedirlo
        return {
            "mensaje": "Movimiento registrado",
            "stock_actual": fila["stock_actual"],
            "stock_reservado": fila["stock_reservado"],
            "disponible": fila["stock_actual"] - fila["stock_reservado"],
            "stock_bajo": fila["stock_actual"] < fila["stock_minimo"],  # True si ha caído por debajo del mínimo
        }
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        print("Error al registrar movimiento:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()
# *A TENER EN CUENTA: cuando haya reservas, el admin tendrá que reducir la reserva antes de poder gastar ese stock, porque aquí nadie puede bajar de stock_reservado.


@router.get("/consumibles/{id_articulo}/historial")
def historial_consumible(id_articulo: int, usuario=Depends(solo_admin)):
    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que el consumible existe
        cur.execute("SELECT 1 FROM consumibles WHERE id_articulo = %s", (id_articulo,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Consumible no encontrado")

        # últimos movimientos con el nombre de quien los hizo (JOIN con usuarios)
        cur.execute(
            """SELECT m.id_movimiento, m.cantidad, m.fecha, u.nombre AS usuario
               FROM movimientos_consumible m
               JOIN usuarios u ON u.id_usuario = m.id_usuario
               WHERE m.id_articulo = %s
               ORDER BY m.fecha DESC
               LIMIT 50""",  # 50 para no devolver una lista enorme
            (id_articulo,),
        )
        return cur.fetchall()
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error al sacar el historial:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()
