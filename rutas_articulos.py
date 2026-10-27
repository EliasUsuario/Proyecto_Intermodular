
# rutas_articulos.py - catálogo maestro (artículos y categorías)
# Alumno: Elías Martínez


#   GET  /categorias         =   lista de categorías (cualquier usuario)
#   GET  /articulos          =      lista del catálogo, con ?buscar= y ?tipo= (cualquier usuario)
#   GET  /articulos/{id}    =   un artículo (cualquier usuario)
#   POST /articulos         =   dar de alta un artículo (solo admin)
#   PUT  /articulos/{id}    =   editar o bloquear un artículo (solo admin)

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from conexion import conectar
from pydantic import BaseModel
from seguridad import usuario_actual, solo_admin

router = APIRouter(tags=["Catálogo"])

# esta consulta la uso en el listado y en el detalle, así no la escribo dos veces
# el LEFT JOIN con consumibles es porque las máquinas no tienen fila en esa tabla
SQL_ARTICULOS = """
    SELECT a.id_articulo, a.nombre, a.descripcion, a.id_categoria,
           c.nombre AS categoria, a.ean, a.tipo, a.activo,
           co.codigo_qr, co.unidad_medida, co.stock_actual, co.stock_minimo, co.stock_reservado
    FROM articulos a
    LEFT JOIN categorias c ON c.id_categoria = a.id_categoria
    LEFT JOIN consumibles co ON co.id_articulo = a.id_articulo
    WHERE 1 = 1
"""

# datos que llegan al dar de alta un artículo
class ArticuloNuevo(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = None
    tipo: str  # 'consumible' o 'maquinaria'
     # estos campos solo se usan si es consumible
    codigo_qr: Optional[str] = None
    unidad_medida: str = "uds"
    stock_actual: int = 0
    stock_minimo: int = 0

# datos que llegan al editar un artículo (PUT = mando todos los campos)
class ArticuloEditar(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = None
    ean: Optional[str] = None
    activo: bool = True  # False = bloqueado por el admin
    stock_minimo: Optional[int] = None  # solo para consumibles
    
    
@router.get("/categorias")
def listar_categorias(usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_categoria, nombre FROM categorias ORDER BY nombre")
        return cur.fetchall()  # lista de diccionarios
    except Exception as e:
        print("Error al listar categorías:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.get("/articulos")
def listar_articulos(buscar: Optional[str] = None, tipo: Optional[str] = None,
                     usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()
        sql = SQL_ARTICULOS  # parto de la consulta base
        params = []  # aquí voy guardando los valores de los %s

        # el operario no ve el material bloqueado, el admin lo ve todo
        if usuario["rol"] != "administrador":
            sql += " AND a.activo = TRUE"

        # si viene texto de búsqueda filtro por nombre (ILIKE no distingue mayúsculas)
        if buscar:
            sql += " AND a.nombre ILIKE %s"
            params.append("%" + buscar + "%")

        # si viene el tipo filtro por consumible o maquinaria
        if tipo:
            sql += " AND a.tipo = %s"
            params.append(tipo)

        sql += " ORDER BY a.nombre"
        cur.execute(sql, params)
        return cur.fetchall()
    except Exception as e:
        print("Error al listar artículos:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.get("/articulos/{id_articulo}")
def ver_articulo(id_articulo: int, usuario=Depends(usuario_actual)):
    conn = conectar()
    try:
        cur = conn.cursor()
        sql = SQL_ARTICULOS + " AND a.id_articulo = %s"
        # igual que en el listado, el operario no ve el bloqueado
        if usuario["rol"] != "administrador":
            sql += " AND a.activo = TRUE"
        cur.execute(sql, (id_articulo,))
        articulo = cur.fetchone()

        if articulo is None:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")
        return articulo
    except HTTPException as e:
        raise e  # si no, el except de abajo se come el 404
    except Exception as e:
        print("Error al ver artículo:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.post("/articulos", status_code=201)
def crear_articulo(datos: ArticuloNuevo, usuario=Depends(solo_admin)):
    # primero compruebo los datos a mano
    if datos.tipo not in ("consumible", "maquinaria"):
        raise HTTPException(status_code=400, detail="El tipo tiene que ser 'consumible' o 'maquinaria'")
    if datos.tipo == "consumible":
        if not datos.codigo_qr:
            raise HTTPException(status_code=400, detail="Un consumible necesita codigo_qr")
        if datos.stock_actual < 0 or datos.stock_minimo < 0:
            raise HTTPException(status_code=400, detail="El stock no puede ser negativo")

    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que la categoría existe (si han mandado una)
        if datos.id_categoria is not None:
            cur.execute("SELECT 1 FROM categorias WHERE id_categoria = %s", (datos.id_categoria,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=400, detail="La categoría no existe")

        # compruebo que el QR no esté repetido
        if datos.tipo == "consumible":
            cur.execute("SELECT 1 FROM consumibles WHERE codigo_qr = %s", (datos.codigo_qr,))
            if cur.fetchone() is not None:
                raise HTTPException(status_code=400, detail="Ya existe un consumible con ese QR")

        # inserto en articulos y recupero el id nuevo con RETURNING
        cur.execute(
            """INSERT INTO articulos (nombre, descripcion, id_categoria, ean, tipo)
               VALUES (%s, %s, %s, %s, %s) RETURNING id_articulo""",
            (datos.nombre, datos.descripcion, datos.id_categoria, datos.ean, datos.tipo),
        )
        aux = cur.fetchone()
        nuevo_id = aux["id_articulo"]

        # si es consumible también hay que crear su fila en consumibles
        if datos.tipo == "consumible":
            cur.execute(
                """INSERT INTO consumibles (id_articulo, codigo_qr, unidad_medida, stock_actual, stock_minimo)
                   VALUES (%s, %s, %s, %s, %s)""",
                (nuevo_id, datos.codigo_qr, datos.unidad_medida, datos.stock_actual, datos.stock_minimo),
            )

        conn.commit()  # guardo los dos INSERT a la vez
        return {"mensaje": "Artículo creado", "id_articulo": nuevo_id}
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()  # si algo falla deshago todo
        print("Error al crear artículo:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()

# *A TENER EN CUENTA: las unidades de maquinaria (tabla maquinas) se crean en el siguiente paso, con POST /maquinas


@router.put("/articulos/{id_articulo}")
def editar_articulo(id_articulo: int, datos: ArticuloEditar, usuario=Depends(solo_admin)):
    conn = conectar()
    try:
        cur = conn.cursor()

        # compruebo que el artículo existe y de paso miro de qué tipo es
        cur.execute("SELECT tipo FROM articulos WHERE id_articulo = %s", (id_articulo,))
        articulo = cur.fetchone()
        if articulo is None:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")

        # compruebo la categoría igual que en el POST (copio y pego)
        if datos.id_categoria is not None:
            cur.execute("SELECT 1 FROM categorias WHERE id_categoria = %s", (datos.id_categoria,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=400, detail="La categoría no existe")

        # actualizo los datos generales
        cur.execute(
            """UPDATE articulos
               SET nombre = %s, descripcion = %s, id_categoria = %s, ean = %s, activo = %s
               WHERE id_articulo = %s""",
            (datos.nombre, datos.descripcion, datos.id_categoria, datos.ean, datos.activo, id_articulo),
        )

        # si es consumible y han mandado stock_minimo, lo actualizo también
        if articulo["tipo"] == "consumible" and datos.stock_minimo is not None:
            if datos.stock_minimo < 0:
                raise HTTPException(status_code=400, detail="El stock mínimo no puede ser negativo")
            cur.execute(
                "UPDATE consumibles SET stock_minimo = %s WHERE id_articulo = %s",
                (datos.stock_minimo, id_articulo),
            )

        conn.commit()
        return {"mensaje": "Artículo actualizado"}
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        print("Error al editar artículo:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()
