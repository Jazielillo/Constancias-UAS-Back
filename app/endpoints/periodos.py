from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from models import models
from schemas.schemas import (
    Periodo, PeriodoCreate, PeriodoUpdate
)

router = APIRouter()


# ENDPOINTS PARA PERÍODOS
@router.get("/periodos", response_model=List[Periodo])
async def listar_periodos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todos los períodos"""
    periodos = db.query(models.Periodo).offset(skip).limit(limit).all()
    return periodos

@router.post("/periodos", response_model=Periodo)
async def crear_periodo(periodo: PeriodoCreate, db: Session = Depends(get_db)):
    """Crear un nuevo período"""
    db_periodo = models.Periodo(**periodo.dict())
    db.add(db_periodo)
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

@router.get("/periodos/{periodo_id}", response_model=Periodo)
async def obtener_periodo(periodo_id: int, db: Session = Depends(get_db)):
    """Obtener un período por ID"""
    periodo = db.query(models.Periodo).filter(models.Periodo.id == periodo_id).first()
    if periodo is None:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    return periodo

@router.put("/periodos/{periodo_id}", response_model=Periodo)
async def actualizar_periodo(periodo_id: int, periodo: PeriodoUpdate, db: Session = Depends(get_db)):
    """Actualizar un período"""
    db_periodo = db.query(models.Periodo).filter(models.Periodo.id == periodo_id).first()
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    for field, value in periodo.dict(exclude_unset=True).items():
        setattr(db_periodo, field, value)
    
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

@router.delete("/periodos/{periodo_id}")
async def eliminar_periodo(periodo_id: int, db: Session = Depends(get_db)):
    """Eliminar un período"""
    db_periodo = db.query(models.Periodo).filter(models.Periodo.id == periodo_id).first()
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    db.delete(db_periodo)
    db.commit()
    return {"mensaje": "Período eliminado exitosamente"}