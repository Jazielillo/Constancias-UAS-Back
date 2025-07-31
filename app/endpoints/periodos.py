from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Dict
from database.database import get_db
from models import models
from schemas.schemas import (
    Periodo, PeriodoCreate, PeriodoUpdate,
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


# ENDPOINTS PARA PERÍODOS

# ENDPOINTS DE LECTURA - Para usuarios autenticados
@router.get("/periodos", response_model=List[Periodo])
async def listar_periodos(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Listar todos los períodos - Requiere autenticación"""
    periodos = db.query(models.Periodo).offset(skip).limit(limit).all()
    
    # Actualizar estados de todos los períodos en tiempo real
    for periodo in periodos:
        estado_actual = calcular_estado_periodo(periodo.fecha_inicio, periodo.fecha_fin)
        if periodo.estado != estado_actual:
            periodo.estado = estado_actual
            db.commit()
    
    return periodos

@router.get("/periodos/{periodo_id}", response_model=Periodo)
async def obtener_periodo(
    periodo_id: int, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Obtener un período por ID - Requiere autenticación"""
    periodo = db.query(models.Periodo).filter(models.Periodo.id == periodo_id).first()
    if periodo is None:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    return periodo

# Función para calcular el estado basado en las fechas
def calcular_estado_periodo(fecha_inicio: str, fecha_fin: str) -> str:
    """
    Calcula el estado del período basado en las fechas y la fecha actual.
    """
    from datetime import datetime, date
    
    # Convertir strings a objetos date
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    if isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    
    hoy = date.today()
    
    if hoy < fecha_inicio:
        return "programado"
    elif fecha_inicio <= hoy <= fecha_fin:
        return "activo"
    else:
        return "finalizado"

# ENDPOINTS DE ESCRITURA - Solo administradores
@router.post("/periodos", response_model=Periodo)
async def crear_periodo(
    periodo: PeriodoCreate, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Crear un nuevo período - Solo administradores"""
    # Extraer el año de la edición del nombre (formato: "Edición YYYY")
    try:
        edicion_anio = periodo.nombre.split(" ")[1]  # Extrae "2025" de "Edición 2025"
        
        # Verificar si ya existe una edición para ese año
        db_edicion_existente = db.query(models.Periodo).filter(
            models.Periodo.nombre == f"Edición {edicion_anio}"
        ).first()
        if db_edicion_existente:
            raise HTTPException(status_code=400, detail=f"Ya existe una edición para el año {edicion_anio}")
            
    except (IndexError, ValueError):
        # Si el formato del nombre no es el esperado, continuar con validación normal
        db_periodo_existente = db.query(models.Periodo).filter(
            models.Periodo.nombre == periodo.nombre,
            models.Periodo.semestre == periodo.semestre
        ).first()
        if db_periodo_existente:
            raise HTTPException(status_code=400, detail="Ya existe un período con ese nombre y semestre")
    
    # Calcular el estado automáticamente basado en las fechas
    estado_calculado = calcular_estado_periodo(periodo.fecha_inicio, periodo.fecha_fin)
    
    # Crear el período con el estado calculado
    periodo_data = periodo.dict()
    periodo_data["estado"] = estado_calculado
    
    db_periodo = models.Periodo(**periodo_data)
    db.add(db_periodo)
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

@router.put("/periodos/{periodo_id}", response_model=Periodo)
async def actualizar_periodo(
    periodo_id: int, 
    periodo: PeriodoUpdate, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Actualizar un período - Solo administradores"""
    db_periodo = db.query(models.Periodo).filter(models.Periodo.id == periodo_id).first()
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Si se están actualizando las fechas, recalcular el estado
    fecha_inicio = periodo.fecha_inicio if periodo.fecha_inicio else db_periodo.fecha_inicio
    fecha_fin = periodo.fecha_fin if periodo.fecha_fin else db_periodo.fecha_fin
    
    # Calcular el estado automáticamente si se proporcionan fechas
    if periodo.fecha_inicio or periodo.fecha_fin:
        estado_calculado = calcular_estado_periodo(fecha_inicio, fecha_fin)
        periodo.estado = estado_calculado
    
    # Verificar edición duplicada si se cambia el nombre
    if periodo.nombre and periodo.nombre != db_periodo.nombre:
        try:
            edicion_anio = periodo.nombre.split(" ")[1]
            db_edicion_existente = db.query(models.Periodo).filter(
                models.Periodo.nombre == f"Edición {edicion_anio}",
                models.Periodo.id != periodo_id  # Excluir el período actual
            ).first()
            if db_edicion_existente:
                raise HTTPException(status_code=400, detail=f"Ya existe una edición para el año {edicion_anio}")
        except (IndexError, ValueError):
            pass
    
    for field, value in periodo.dict(exclude_unset=True).items():
        setattr(db_periodo, field, value)
    
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

@router.delete("/periodos/{periodo_id}")
async def eliminar_periodo(
    periodo_id: int, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Eliminar un período - Solo administradores"""
    db_periodo = db.query(models.Periodo).filter(models.Periodo.id == periodo_id).first()
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Opcional: Verificar si el período tiene solicitudes asociadas antes de eliminar
    solicitudes_asociadas = db.query(models.Solicitud).filter(models.Solicitud.periodo_id == periodo_id).first()
    if solicitudes_asociadas:
        raise HTTPException(status_code=400, detail="No se puede eliminar el período porque tiene solicitudes asociadas")
    
    db.delete(db_periodo)
    db.commit()
    return {"mensaje": "Período eliminado exitosamente"}