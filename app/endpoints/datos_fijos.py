from fastapi import APIRouter, HTTPException, Depends, Header, File, UploadFile
from sqlalchemy.orm import Session
from typing import Dict, Optional
from database.database import get_db
from models import models
from schemas.schemas import (
    DatosFijos, DatosFijosUpdate
)
import jwt
from jwt.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv
import shutil
from pathlib import Path

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter()

# Configuración de rutas de archivos
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

# Función auxiliar para extraer y validar el access token
async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Extrae y valida el access token del header Authorization.
    Retorna los datos del usuario autenticado.
    """
    try:
        # Verificar que el header Authorization existe
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extraer el token (formato: "Bearer <token>")
        try:
            scheme, token = authorization.split(' ', 1)
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        # Decodificar el token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verificar que es un access token
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Access token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        # Buscar el usuario en la base de datos
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user.id,
            "admin": user.admin,
            "sub": user.sub,
            "email": user.email,
            "nombre": user.nombre
        }
        
    except HTTPException:
        raise  # Re-lanzar HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# FUNCIÓN PARA VERIFICAR PERMISOS DE ADMINISTRADOR
async def get_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Verifica que el usuario actual sea administrador.
    Basado en el campo 'admin' del access_token decodificado.
    """
    if not current_user.get("admin", False):
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador para esta operación")
    return current_user

# Función auxiliar para validar archivos PNG
def validar_archivo_png(file: UploadFile) -> None:
    """
    Valida que el archivo sea PNG
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se ha proporcionado un archivo")
    
    if not file.filename.lower().endswith('.png'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PNG")
    
    if not file.content_type or not file.content_type.startswith('image/png'):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen PNG válida")

# ENDPOINTS PARA DATOS FIJOS

@router.get("/datos-fijos", response_model=Optional[DatosFijos])
async def obtener_datos_fijos(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtener los datos fijos - Requiere autenticación
    Todos los usuarios autenticados pueden ver los datos
    """
    # Obtener el primer (y único) registro de datos fijos
    datos_fijos = db.query(models.DatosFijos).first()
    
    # Si no existe, crear uno vacío
    if not datos_fijos:
        datos_fijos = models.DatosFijos()
        db.add(datos_fijos)
        db.commit()
        db.refresh(datos_fijos)
    
    return datos_fijos

@router.put("/datos-fijos", response_model=DatosFijos)
async def actualizar_datos_fijos(
    datos_fijos_update: DatosFijosUpdate,
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """
    Actualizar los datos fijos - Solo administradores
    """
    # Obtener el registro existente o crear uno nuevo
    datos_fijos = db.query(models.DatosFijos).first()
    
    if not datos_fijos:
        # Si no existe, crear uno nuevo
        datos_fijos = models.DatosFijos()
        db.add(datos_fijos)
    
    # Actualizar solo los campos que se proporcionaron
    for field, value in datos_fijos_update.dict(exclude_unset=True).items():
        setattr(datos_fijos, field, value)
    
    db.commit()
    db.refresh(datos_fijos)
    
    return datos_fijos

@router.post("/datos-fijos/inicializar", response_model=DatosFijos)
async def inicializar_datos_fijos(
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """
    Inicializar/Reinicializar datos fijos con valores por defecto - Solo administradores
    Este endpoint borra los datos existentes y los reemplaza con valores por defecto
    """
    # Eliminar todos los registros existentes de datos fijos
    db.query(models.DatosFijos).delete()
    db.commit()
    
    # Crear nuevos datos fijos con valores por defecto predefinidos
    datos_fijos = models.DatosFijos(
        texto_aqc="COMISIÓN DE EVALUACIÓN DEL PROGRAMA DE ESTÍMULOS AL DESEMPEÑO DEL PERSONAL DOCENTE 2025-2026 UNIVERSIDAD AUTÓNOMA DE SINALOA",
        texto_remitente="El suscrito C. Dr. Rody Abraham Soto Rojo, Director de la Facultad de Ingeniería Mochis, dependiente de la Universidad Autónoma de Sinaloa, hace constar que",
        texto_apeticion="A petición de la parte interesada se extiende la presente, para los fines que juzgue convenientes, a los tres días del mes de abril del año dos mil veinticinco, en la ciudad de Los Mochis, Sinaloa.",
        texto_atte="A T E N T A M E N T E",
        texto_sursum="SURSUM VERSUS",
        texto_nombrefirma="DR. RODY ABRAHAM SOTO ROJO",
        texto_cargo="DIRECTOR",
        texto_msgdigital="Firmado digitalmente",
        texto_ccp="C.C.P. Archivo"
    )
    
    db.add(datos_fijos)
    db.commit()
    db.refresh(datos_fijos)
    
    return datos_fijos

# ENDPOINTS PARA SUBIR IMÁGENES

@router.post("/datos-fijos/subir-cabecera")
async def subir_cabecera(
    file: UploadFile = File(...),
    admin_user: Dict = Depends(get_admin_user)
):
    """
    Subir y reemplazar la imagen de cabecera - Solo administradores
    El archivo debe ser formato PNG
    """
    try:
        # Validar que sea PNG
        validar_archivo_png(file)
        
        # Ruta del archivo de destino
        cabecera_path = ASSETS_DIR / "cabecera.png"
        
        # Guardar el archivo, reemplazando si existe
        with open(cabecera_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Cabecera subida exitosamente",
            "filename": "cabecera.png",
            "path": str(cabecera_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir cabecera: {str(e)}")
    finally:
        file.file.close()

@router.post("/datos-fijos/subir-pie-pagina")
async def subir_pie_pagina(
    file: UploadFile = File(...),
    admin_user: Dict = Depends(get_admin_user)
):
    """
    Subir y reemplazar la imagen de pie de página - Solo administradores
    El archivo debe ser formato PNG
    """
    try:
        # Validar que sea PNG
        validar_archivo_png(file)
        
        # Ruta del archivo de destino
        pie_path = ASSETS_DIR / "pie.png"
        
        # Guardar el archivo, reemplazando si existe
        with open(pie_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Pie de página subido exitosamente",
            "filename": "pie.png",
            "path": str(pie_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir pie de página: {str(e)}")
    finally:
        file.file.close()

@router.post("/datos-fijos/subir-firma")
async def subir_firma(
    file: UploadFile = File(...),
    admin_user: Dict = Depends(get_admin_user)
):
    """
    Subir y reemplazar la imagen de firma digital - Solo administradores
    El archivo debe ser formato PNG
    """
    try:
        # Validar que sea PNG
        validar_archivo_png(file)
        
        # Ruta del archivo de destino
        firma_path = ASSETS_DIR / "firma.png"
        
        # Guardar el archivo, reemplazando si existe
        with open(firma_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Firma digital subida exitosamente",
            "filename": "firma.png",
            "path": str(firma_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir firma: {str(e)}")
    finally:
        file.file.close()