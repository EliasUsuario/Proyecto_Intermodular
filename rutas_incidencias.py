# rutas_incidencias.py - incidencias de maquinaria (solo administrador)
# Alumno: Elías Martínez

#   GET /incidencias                =   listar incidencias, con ?resuelta=true/false
#   PUT /incidencias/{id}/resolver  =   marcarla como resuelta y dejar la máquina disponible
# (las incidencias se crean al devolver una máquina, en rutas_maquinas.py)


from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from conexion import conectar
from seguridad import solo_admin

router = APIRouter(tags=["Incidencias"])


@router.get("/incidencias")
def listar_incidencias(resuelta: Optional[bool] = None, usuario=Depends(solo_admin)):
    conn = conectar()
    try:
        cur = conn.cursor()

        # saco la incidencia con los datos de la máquina y de quien la tenía
        # *A TENER EN CUENTA: "reportada_por" es el titular del préstamo; si la devuelve un admin en su nombre sale el nombre del titular, no el del admin
        sql = """
            SELECT i.id_incidencia, i.descripcion, i.fecha_reporte, i.resuelta, i.fecha_resolucion,
                   m.id_maquina, m.codigo_qr, m.numero_serie, m.estado,
                   a.nombre AS maquina, u.nombre AS reportada_por, adm.nombre AS resuelta_por
            FROM incidencias i
            JOIN prestamos p ON p.id_prestamo = i.id_prestamo
            JOIN maquinas m ON m.id_maquina = p.id_maquina
            JOIN articulos a ON a.id_articulo = m.id_articulo
            JOIN usuarios u ON u.id_usuario = p.id_usuario
            LEFT JOIN usuarios adm ON adm.id_usuario = i.id_admin_resuelve
            WHERE 1 = 1
        """
        params = []

        # si piden solo las resueltas o solo las pendientes, filtro
        if resuelta is not None:
            sql += " AND i.resuelta = %s"
            params.append(resuelta)

        # primero las pendientes y dentro de cada grupo las más recientes
        sql += " ORDER BY i.resuelta ASC, i.fecha_reporte DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    except Exception as e:
        print("Error al listar incidencias:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()


@router.put("/incidencias/{id_incidencia}/resolver")
def resolver_incidencia(id_incidencia: int, usuario=Depends(solo_admin)):
    conn = conectar()
    try:
        cur = conn.cursor()

        # marco la incidencia como resuelta (solo si no lo estaba ya)
        cur.execute(
            """UPDATE incidencias
               SET resuelta = TRUE, fecha_resolucion = NOW(), id_admin_resuelve = %s
               WHERE id_incidencia = %s AND resuelta = FALSE
               RETURNING id_prestamo""",
            (usuario["id_usuario"], id_incidencia),
        )
        fila = cur.fetchone()

        if fila is None:
            # no ha actualizado nada: o no existe o ya estaba resuelta
            cur.execute("SELECT 1 FROM incidencias WHERE id_incidencia = %s", (id_incidencia,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Incidencia no encontrada")
            raise HTTPException(status_code=400, detail="La incidencia ya estaba resuelta")

        # saco la máquina a través del préstamo y la dejo disponible
        # (solo si sigue en mantenimiento, por si el admin la ha cambiado antes)
        cur.execute("SELECT id_maquina FROM prestamos WHERE id_prestamo = %s", (fila["id_prestamo"],))
        prestamo = cur.fetchone()
        cur.execute(
            "UPDATE maquinas SET estado = 'disponible' WHERE id_maquina = %s AND estado = 'en_mantenimiento'",
            (prestamo["id_maquina"],),
        )

        conn.commit()
        return {"mensaje": "Incidencia resuelta, máquina disponible"}
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        print("Error al resolver incidencia:", e)
        raise HTTPException(status_code=500, detail="Error en el servidor")
    finally:
        conn.close()
