from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Dict
from database.database import get_db
from models import models
from schemas.schemas import (
    Periodo, PeriodoCreate, PeriodoUpdate,  # Mantenemos los nombres de schemas
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


# ENDPOINTS PARA PERÍODOS (ahora usando la tabla Ediciones)

@router.get("/periodos/edicion-actual")
async def obtener_edicion_actual(db: Session = Depends(get_db)):
    """
    Obtener la edición que está actualmente en curso (dentro del rango de fechas)
    - Endpoint público, no requiere autenticación
    """
    try:
        from datetime import date
        
        hoy = date.today()
        print(f"[DEBUG] Fecha actual: {hoy}")
        
        # Buscar la edición que esté dentro del rango de fechas actual
        edicion_actual = db.query(models.Edicion).filter(
            models.Edicion.fecha_inicio <= hoy,
            models.Edicion.fecha_fin >= hoy
        ).first()
        
        print(f"[DEBUG] Edición encontrada: {edicion_actual}")
        
        if edicion_actual is None:
            # Si no hay edición activa, buscar la más reciente
            edicion_actual = db.query(models.Edicion).order_by(
                models.Edicion.fecha_inicio.desc()
            ).first()
            
            if edicion_actual is None:
                raise HTTPException(
                    status_code=404, 
                    detail="No hay ninguna edición disponible en el sistema"
                )
        
        # Calcular el estado si es necesario
        try:
            estado_actual = calcular_estado_periodo(edicion_actual.fecha_inicio, edicion_actual.fecha_fin)
            if edicion_actual.estado != estado_actual:
                edicion_actual.estado = estado_actual
                db.commit()
                db.refresh(edicion_actual)
        except Exception as e:
            print(f"[WARNING] Error al calcular estado: {e}")
            # Continuar con el estado actual en la BD
        
        # IMPORTANTE: Convertir fechas a string para evitar problemas de serialización
        return {
            "id": edicion_actual.id,
            "nombre": edicion_actual.nombre,
            "periodo1": edicion_actual.periodo1,
            "periodo2": edicion_actual.periodo2,
            "estado": edicion_actual.estado,
            "fecha_inicio": str(edicion_actual.fecha_inicio) if edicion_actual.fecha_inicio else None,
            "fecha_fin": str(edicion_actual.fecha_fin) if edicion_actual.fecha_fin else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error en obtener_edicion_actual: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
    

# ENDPOINTS DE LECTURA - Para usuarios autenticados
@router.get("/periodos", response_model=List[Periodo])
async def listar_periodos(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Listar todas las ediciones - Requiere autenticación"""
    ediciones = db.query(models.Edicion).offset(skip).limit(limit).all()
    
    # Actualizar estados de todas las ediciones en tiempo real
    for edicion in ediciones:
        estado_actual = calcular_estado_periodo(edicion.fecha_inicio, edicion.fecha_fin)
        if edicion.estado != estado_actual:
            edicion.estado = estado_actual
            db.commit()
    
    return ediciones

@router.get("/periodos/{periodo_id}", response_model=Periodo)
async def obtener_periodo(
    periodo_id: int, 
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Obtener una edición por ID - Requiere autenticación"""
    edicion = db.query(models.Edicion).filter(models.Edicion.id == periodo_id).first()
    if edicion is None:
        raise HTTPException(status_code=404, detail="Edición no encontrada")
    return edicion

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
    """Crear una nueva edición - Solo administradores"""
    # Extraer el año de la edición del nombre (formato: "Edición YYYY")
    try:
        edicion_anio = periodo.nombre.split(" ")[1]  # Extrae "2025" de "Edición 2025"
        
        # Verificar si ya existe una edición para ese año
        db_edicion_existente = db.query(models.Edicion).filter(
            models.Edicion.nombre == f"Edición {edicion_anio}"
        ).first()
        if db_edicion_existente:
            raise HTTPException(status_code=400, detail=f"Ya existe una edición para el año {edicion_anio}")
            
    except (IndexError, ValueError):
        # Si el formato del nombre no es el esperado, verificar duplicados por nombre y periodo1/periodo2
        db_edicion_existente = db.query(models.Edicion).filter(
            models.Edicion.nombre == periodo.nombre,
            models.Edicion.periodo1 == periodo.periodo1,
            models.Edicion.periodo2 == periodo.periodo2
        ).first()
        if db_edicion_existente:
            raise HTTPException(status_code=400, detail="Ya existe una edición con ese nombre y períodos")
    
    # Calcular el estado automáticamente basado en las fechas
    estado_calculado = calcular_estado_periodo(periodo.fecha_inicio, periodo.fecha_fin)
    
    # Crear la edición con el estado calculado
    periodo_data = periodo.dict()
    periodo_data["estado"] = estado_calculado
    
    db_edicion = models.Edicion(**periodo_data)
    db.add(db_edicion)
    db.commit()
    db.refresh(db_edicion)
    return db_edicion

@router.put("/periodos/{periodo_id}", response_model=Periodo)
async def actualizar_periodo(
    periodo_id: int, 
    periodo: PeriodoUpdate, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Actualizar una edición - Solo administradores"""
    db_edicion = db.query(models.Edicion).filter(models.Edicion.id == periodo_id).first()
    if db_edicion is None:
        raise HTTPException(status_code=404, detail="Edición no encontrada")
    
    # Si se están actualizando las fechas, recalcular el estado
    fecha_inicio = periodo.fecha_inicio if periodo.fecha_inicio else db_edicion.fecha_inicio
    fecha_fin = periodo.fecha_fin if periodo.fecha_fin else db_edicion.fecha_fin
    
    # Calcular el estado automáticamente si se proporcionan fechas
    if periodo.fecha_inicio or periodo.fecha_fin:
        estado_calculado = calcular_estado_periodo(fecha_inicio, fecha_fin)
        periodo.estado = estado_calculado
    
    # Verificar edición duplicada si se cambia el nombre
    if periodo.nombre and periodo.nombre != db_edicion.nombre:
        try:
            edicion_anio = periodo.nombre.split(" ")[1]
            db_edicion_existente = db.query(models.Edicion).filter(
                models.Edicion.nombre == f"Edición {edicion_anio}",
                models.Edicion.id != periodo_id  # Excluir la edición actual
            ).first()
            if db_edicion_existente:
                raise HTTPException(status_code=400, detail=f"Ya existe una edición para el año {edicion_anio}")
        except (IndexError, ValueError):
            pass
    
    for field, value in periodo.dict(exclude_unset=True).items():
        setattr(db_edicion, field, value)
    
    db.commit()
    db.refresh(db_edicion)
    return db_edicion

@router.delete("/periodos/{periodo_id}")
async def eliminar_periodo(
    periodo_id: int, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Eliminar una edición - Solo administradores"""
    db_edicion = db.query(models.Edicion).filter(models.Edicion.id == periodo_id).first()
    if db_edicion is None:
        raise HTTPException(status_code=404, detail="Edición no encontrada")
    
    # Verificar si hay solicitudes asociadas que usen los períodos de esta edición
    # Como ahora el período es un string, necesitamos verificar contra periodo1 y periodo2
    solicitudes_asociadas = db.query(models.Solicitud).filter(
        (models.Solicitud.periodo == db_edicion.periodo1) |
        (models.Solicitud.periodo == db_edicion.periodo2)
    ).first()
    
    if solicitudes_asociadas:
        raise HTTPException(status_code=400, detail="No se puede eliminar la edición porque tiene solicitudes asociadas")
    
    db.delete(db_edicion)
    db.commit()
    return {"mensaje": "Edición eliminada exitosamente"}