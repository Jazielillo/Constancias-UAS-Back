# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Importar configuración y modelos
from models import models
from database.database import engine
from config.config import settings
from pdf_generator import PDFGenerator
from endpoints.categorias import router as categorias_router
from endpoints.constancias import router as constancias_router
from endpoints.periodos import router as periodos_router
from endpoints.programas import router as programas_router
from endpoints.solicitudes import router as solicitudes_router
from endpoints.usuarios import router as usuarios_router


# Crear directorios necesarios
os.makedirs("qrs", exist_ok=True)
os.makedirs("constancias", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="API de Constancias UAS",
    description="API para generar constancias académicas de la Universidad Autónoma de Sinaloa",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Incluir routers
app.include_router(categorias_router, prefix="/api/v1", tags=["categorias"])
app.include_router(constancias_router, prefix="/api/v1", tags=["constancias"])
app.include_router(periodos_router, prefix="/api/v1", tags=["periodos"])
app.include_router(programas_router, prefix="/api/v1", tags=["programas"])
app.include_router(solicitudes_router, prefix="/api/v1", tags=["solicitudes"])
app.include_router(usuarios_router, prefix="/api/v1", tags=["usuarios"])

@app.get("/")
async def root():
    return {"message": "API de Constancias UAS - Facultad de Ingeniería Mochis"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)