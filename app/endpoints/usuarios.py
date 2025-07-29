from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from models import models
from schemas.schemas import (
    User, UserCreate, UserUpdate
)

router = APIRouter()

@router.get("/prueba")
async def prueba():
    return {"message": "¡Esta es una prueba desde FastAPI SALUDEEEN!"}

# ENDPOINTS PARA USUARIOS
@router.get("/usuarios", response_model=List[User])
async def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todos los usuarios"""
    usuarios = db.query(models.User).offset(skip).limit(limit).all()
    return usuarios

@router.post("/usuarios", response_model=User)
async def crear_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario"""
    # Verificar si el email ya existe
    db_usuario = db.query(models.User).filter(models.User.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    db_usuario = models.User(**usuario.dict())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.get("/usuarios/{usuario_id}", response_model=User)
async def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener un usuario por ID"""
    usuario = db.query(models.User).filter(models.User.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/usuarios/{usuario_id}", response_model=User)
async def actualizar_usuario(usuario_id: int, usuario: UserUpdate, db: Session = Depends(get_db)):
    """Actualizar un usuario"""
    db_usuario = db.query(models.User).filter(models.User.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    for field, value in usuario.dict(exclude_unset=True).items():
        setattr(db_usuario, field, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.delete("/usuarios/{usuario_id}")
async def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Eliminar un usuario"""
    db_usuario = db.query(models.User).filter(models.User.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(db_usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado exitosamente"}