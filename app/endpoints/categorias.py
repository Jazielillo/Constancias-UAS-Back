from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Dict
from database.database import get_db
from models import models
from schemas.schemas import (
    Categoria, CategoriaCreate, CategoriaUpdate,
)
import jwt
from jwt.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter()



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

# ENDPOINTS PARA CATEGORÍAS

# ENDPOINTS DE LECTURA - Para usuarios autenticados
@router.get("/categorias", response_model=List[Categoria])
async def listar_categorias(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Listar todas las categorías - Requiere autenticación"""
    categorias = db.query(models.Categoria).offset(skip).limit(limit).all()
    return categorias

@router.get("/categorias/{categoria_id}", response_model=Categoria)
async def obtener_categoria(
    categoria_id: int, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Obtener una categoría por ID - Requiere autenticación"""
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

# ENDPOINTS DE ESCRITURA - Solo administradores
@router.post("/categorias", response_model=Categoria)
async def crear_categoria(
    categoria: CategoriaCreate, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Crear una nueva categoría - Solo administradores"""
    # Verificar si el código ya existe
    db_categoria = db.query(models.Categoria).filter(models.Categoria.codigo_categoria == categoria.codigo_categoria).first()
    if db_categoria:
        raise HTTPException(status_code=400, detail="El código de categoría ya existe")
    
    db_categoria = models.Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@router.put("/categorias/{categoria_id}", response_model=Categoria)
async def actualizar_categoria(
    categoria_id: int, 
    categoria: CategoriaUpdate, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Actualizar una categoría - Solo administradores"""
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    for field, value in categoria.dict(exclude_unset=True).items():
        setattr(db_categoria, field, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@router.delete("/categorias/{categoria_id}")
async def eliminar_categoria(
    categoria_id: int, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Eliminar una categoría - Solo administradores"""
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    db.delete(db_categoria)
    db.commit()
    return {"mensaje": "Categoría eliminada exitosamente"}

