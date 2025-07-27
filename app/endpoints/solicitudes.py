from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from models import models
from schemas.schemas import (
    Solicitud, SolicitudCreate, SolicitudUpdate
)

router = APIRouter()


# ENDPOINTS PARA SOLICITUDES
@router.get("/solicitudes", response_model=List[Solicitud])
async def listar_solicitudes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las solicitudes"""
    solicitudes = db.query(models.Solicitud).offset(skip).limit(limit).all()
    return solicitudes

@router.post("/solicitudes", response_model=Solicitud)
async def crear_solicitud(solicitud: SolicitudCreate, db: Session = Depends(get_db)):
    """Crear una nueva solicitud"""
    db_solicitud = models.Solicitud(**solicitud.dict())
    db.add(db_solicitud)
    db.commit()
    db.refresh(db_solicitud)
    return db_solicitud

@router.get("/solicitudes/{solicitud_id}", response_model=Solicitud)
async def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    """Obtener una solicitud por ID"""
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud

@router.put("/solicitudes/{solicitud_id}", response_model=Solicitud)
async def actualizar_solicitud(solicitud_id: int, solicitud: SolicitudUpdate, db: Session = Depends(get_db)):
    """Actualizar una solicitud"""
    db_solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if db_solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    for field, value in solicitud.dict(exclude_unset=True).items():
        setattr(db_solicitud, field, value)
    
    db.commit()
    db.refresh(db_solicitud)
    return db_solicitud

@router.delete("/solicitudes/{solicitud_id}")
async def eliminar_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    """Eliminar una solicitud"""
    db_solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if db_solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    db.delete(db_solicitud)
    db.commit()
    return {"mensaje": "Solicitud eliminada exitosamente"}