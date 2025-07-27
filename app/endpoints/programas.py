from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from models import models
from schemas.schemas import (
    Programa, ProgramaCreate, ProgramaUpdate,
)

router = APIRouter()

# ENDPOINTS PARA PROGRAMAS
@router.get("/programas", response_model=List[Programa])
async def listar_programas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todos los programas"""
    programas = db.query(models.Programa).offset(skip).limit(limit).all()
    return programas

@router.post("/programas", response_model=Programa)
async def crear_programa(programa: ProgramaCreate, db: Session = Depends(get_db)):
    """Crear un nuevo programa"""
    # Verificar si el código ya existe
    db_programa = db.query(models.Programa).filter(models.Programa.codigo == programa.codigo).first()
    if db_programa:
        raise HTTPException(status_code=400, detail="El código del programa ya existe")
    
    db_programa = models.Programa(**programa.dict())
    db.add(db_programa)
    db.commit()
    db.refresh(db_programa)
    return db_programa

@router.get("/programas/{programa_id}", response_model=Programa)
async def obtener_programa(programa_id: int, db: Session = Depends(get_db)):
    """Obtener un programa por ID"""
    programa = db.query(models.Programa).filter(models.Programa.id == programa_id).first()
    if programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    return programa

@router.put("/programas/{programa_id}", response_model=Programa)
async def actualizar_programa(programa_id: int, programa: ProgramaUpdate, db: Session = Depends(get_db)):
    """Actualizar un programa"""
    db_programa = db.query(models.Programa).filter(models.Programa.id == programa_id).first()
    if db_programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    
    for field, value in programa.dict(exclude_unset=True).items():
        setattr(db_programa, field, value)
    
    db.commit()
    db.refresh(db_programa)
    return db_programa

@router.delete("/programas/{programa_id}")
async def eliminar_programa(programa_id: int, db: Session = Depends(get_db)):
    """Eliminar un programa"""
    db_programa = db.query(models.Programa).filter(models.Programa.id == programa_id).first()
    if db_programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    
    db.delete(db_programa)
    db.commit()
    return {"mensaje": "Programa eliminado exitosamente"}