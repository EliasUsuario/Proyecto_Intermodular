
# rutas_articulos.py - catálogo maestro (artículos y categorías)
# Alumno: Elías Martínez

from typing import Optional
from fastapi import APIRouter
from conexion import conectar
from pydantic import BaseModel

router = APIRouter(tags=["Catálogo"])

# datos que llegan al dar de alta un artículo
class ArticuloNuevo(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = None
    tipo: str  # 'consumible' o 'maquinaria'

# datos que llegan al editar un artículo
class ArticuloEditar(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = None
    tipo: str  # 'consumible' o 'maquinaria'
    
@router.get("/")
def listar_articulos():
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_articulo, nombre, tipo, activo 
            FROM articulos 
            ORDER BY nombre;
        """)
        lista_articulos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return lista_articulos

    except Exception as e:
        return {"error": f"Error al obtener los artículos: {str(e)}"}
    
@router.get("/categorias")
def listar_categorias():
    pass

@router.get("/articulos")
def listar_articulos():
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_articulo, nombre, tipo, activo 
            FROM articulos 
            ORDER BY nombre;
        """)
        lista_articulos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return lista_articulos

    except Exception as e:
        return {"error": f"Error al obtener los artículos: {str(e)}"}   

@router.put("/articulos/{id_articulo}")
def editar_articulo(id_articulo: int, datos: ArticuloEditar):
    pass
