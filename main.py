# Alumno: Elías Martínez | 2º DAM

# main.py - arranque de la API de GestorMaterial
# Para arrancarla:  uvicorn main:app --reload --host 0.0.0.0
# La documentación automática sale en http://localhost:8000/docs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import rutas_articulos # fichero con el catálogo
import rutas_conexion # fichero con el login
import rutas_consumibles

# Se crea la aplicación
app = FastAPI(title="GestorMaterial API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# añado las rutas de cada fichero a la app
app.include_router(rutas_articulos.router)
app.include_router(rutas_conexion.router)
app.include_router(rutas_consumibles.router)

#* A TENER EN CUENTA: según vaya haciendo cosas nuevas hay que añadir aquí su router

@app.get("/")
def inicio():
    # ruta de prueba para ver que el servidor está funcionando
    return {"mensaje": "API de GestorMaterial funcionando correctamente"}