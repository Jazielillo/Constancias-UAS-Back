from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from models import models
from schemas.schemas import (
    Categoria, CategoriaCreate, CategoriaUpdate,
)

router = APIRouter()


# ENDPOINTS PARA CATEGORÍAS
@router.get("/categorias", response_model=List[Categoria])
async def listar_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las categorías"""
    categorias = db.query(models.Categoria).offset(skip).limit(limit).all()
    return categorias

@router.post("/categorias", response_model=Categoria)
async def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    """Crear una nueva categoría"""
    # Verificar si el código ya existe
    db_categoria = db.query(models.Categoria).filter(models.Categoria.codigo_categoria == categoria.codigo_categoria).first()
    if db_categoria:
        raise HTTPException(status_code=400, detail="El código de categoría ya existe")
    
    db_categoria = models.Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@router.get("/categorias/{categoria_id}", response_model=Categoria)
async def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)):
    """Obtener una categoría por ID"""
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@router.put("/categorias/{categoria_id}", response_model=Categoria)
async def actualizar_categoria(categoria_id: int, categoria: CategoriaUpdate, db: Session = Depends(get_db)):
    """Actualizar una categoría"""
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    for field, value in categoria.dict(exclude_unset=True).items():
        setattr(db_categoria, field, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@router.delete("/categorias/{categoria_id}")
async def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    """Eliminar una categoría"""
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    db.delete(db_categoria)
    db.commit()
    return {"mensaje": "Categoría eliminada exitosamente"}