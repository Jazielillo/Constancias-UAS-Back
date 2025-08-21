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
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        try:
            scheme, token = authorization.split(' ', 1)
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Access token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
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
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def get_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Verifica que el usuario actual sea administrador."""
    if not current_user.get("admin", False):
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador para esta operación")
    return current_user

def calcular_estado_periodo(fecha_inicio: str, fecha_fin: str) -> str:
    """Calcula el estado del período basado en las fechas y la fecha actual."""
    from datetime import datetime, date
    
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

# ✅ ENDPOINT ACTUALIZADO
@router.get("/periodos/edicion-actual")
async def obtener_edicion_actual(db: Session = Depends(get_db)):
    """Obtener la edición que está actualmente en curso Y ACTIVA"""
    try:
        from datetime import date
        
        hoy = date.today()
        print(f"[DEBUG] Fecha actual: {hoy}")
        
        # Solo buscar ediciones activas
        edicion_actual = db.query(models.Edicion).filter(
            models.Edicion.fecha_inicio <= hoy,
            models.Edicion.fecha_fin >= hoy,
            models.Edicion.activa == True
        ).first()
        
        print(f"[DEBUG] Edición encontrada: {edicion_actual}")
        
        if edicion_actual is None:
            # Si no hay edición activa en curso, buscar la más reciente activa
            edicion_actual = db.query(models.Edicion).filter(
                models.Edicion.activa == True
            ).order_by(
                models.Edicion.fecha_inicio.desc()
            ).first()
            
            if edicion_actual is None:
                raise HTTPException(
                    status_code=404, 
                    detail="No hay ninguna edición activa disponible en el sistema"
                )
        
        try:
            estado_actual = calcular_estado_periodo(edicion_actual.fecha_inicio, edicion_actual.fecha_fin)
            if edicion_actual.estado != estado_actual:
                edicion_actual.estado = estado_actual
                db.commit()
                db.refresh(edicion_actual)
        except Exception as e:
            print(f"[WARNING] Error al calcular estado: {e}")
        
        return {
            "id": edicion_actual.id,
            "nombre": edicion_actual.nombre,
            "periodo1": edicion_actual.periodo1,
            "periodo2": edicion_actual.periodo2,
            "estado": edicion_actual.estado,
            "fecha_inicio": str(edicion_actual.fecha_inicio) if edicion_actual.fecha_inicio else None,
            "fecha_fin": str(edicion_actual.fecha_fin) if edicion_actual.fecha_fin else None,
            "activa": edicion_actual.activa
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

# ✅ ENDPOINT ACTUALIZADO
@router.get("/periodos", response_model=List[Periodo])
async def listar_periodos(
    skip: int = 0, 
    limit: int = 100, 
    incluir_inactivas: bool = True,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Listar ediciones - Requiere autenticación"""
    query = db.query(models.Edicion)
    
    if not incluir_inactivas:
        query = query.filter(models.Edicion.activa == True)
    
    ediciones = query.offset(skip).limit(limit).all()
    
    # Actualizar estados
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

# ✅ ENDPOINT ACTUALIZADO
@router.post("/periodos", response_model=Periodo)
async def crear_periodo(
    periodo: PeriodoCreate, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Crear una nueva edición - Solo administradores"""
    try:
        edicion_anio = periodo.nombre.split(" ")[1]
        
        # Solo verificar ediciones activas del mismo año
        db_edicion_existente = db.query(models.Edicion).filter(
            models.Edicion.nombre == f"Edición {edicion_anio}",
            models.Edicion.activa == True
        ).first()
        if db_edicion_existente:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe una edición activa para el año {edicion_anio}. Debe desactivar la edición existente primero."
            )
            
    except (IndexError, ValueError):
        db_edicion_existente = db.query(models.Edicion).filter(
            models.Edicion.nombre == periodo.nombre,
            models.Edicion.periodo1 == periodo.periodo1,
            models.Edicion.periodo2 == periodo.periodo2,
            models.Edicion.activa == True
        ).first()
        if db_edicion_existente:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe una edición activa con ese nombre y períodos"
            )
    
    estado_calculado = calcular_estado_periodo(periodo.fecha_inicio, periodo.fecha_fin)
    
    periodo_data = periodo.dict()
    periodo_data["estado"] = estado_calculado
    
    db_edicion = models.Edicion(**periodo_data)
    db.add(db_edicion)
    db.commit()
    db.refresh(db_edicion)
    return db_edicion

# ✅ ENDPOINT ACTUALIZADO
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
    
    # Recalcular estado si cambian las fechas
    fecha_inicio = periodo.fecha_inicio if periodo.fecha_inicio else db_edicion.fecha_inicio
    fecha_fin = periodo.fecha_fin if periodo.fecha_fin else db_edicion.fecha_fin
    
    if periodo.fecha_inicio or periodo.fecha_fin:
        estado_calculado = calcular_estado_periodo(fecha_inicio, fecha_fin)
        periodo.estado = estado_calculado
    
    # Validar al activar una edición
    if periodo.activa == True and not db_edicion.activa:
        try:
            nombre_actual = periodo.nombre if periodo.nombre else db_edicion.nombre
            edicion_anio = nombre_actual.split(" ")[1]
            
            db_edicion_activa_existente = db.query(models.Edicion).filter(
                models.Edicion.nombre == f"Edición {edicion_anio}",
                models.Edicion.activa == True,
                models.Edicion.id != periodo_id
            ).first()
            
            if db_edicion_activa_existente:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ya existe una edición activa para el año {edicion_anio}. Debe desactivar la edición existente primero."
                )
        except (IndexError, ValueError):
            pass
    
    # Verificar nombre duplicado solo entre activas
    if periodo.nombre and periodo.nombre != db_edicion.nombre:
        try:
            edicion_anio = periodo.nombre.split(" ")[1]
            db_edicion_existente = db.query(models.Edicion).filter(
                models.Edicion.nombre == f"Edición {edicion_anio}",
                models.Edicion.activa == True,
                models.Edicion.id != periodo_id
            ).first()
            if db_edicion_existente:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ya existe una edición activa para el año {edicion_anio}"
                )
        except (IndexError, ValueError):
            pass
    
    for field, value in periodo.dict(exclude_unset=True).items():
        setattr(db_edicion, field, value)
    
    db.commit()
    db.refresh(db_edicion)
    return db_edicion

# ✅ NUEVO ENDPOINT: Toggle activa/inactiva
@router.patch("/periodos/{periodo_id}/toggle-activa")
async def toggle_edicion_activa(
    periodo_id: int,
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Activar/Desactivar una edición - Solo administradores"""
    db_edicion = db.query(models.Edicion).filter(models.Edicion.id == periodo_id).first()
    if db_edicion is None:
        raise HTTPException(status_code=404, detail="Edición no encontrada")
    
    # Si se está intentando activar
    if not db_edicion.activa:
        try:
            edicion_anio = db_edicion.nombre.split(" ")[1]
            db_edicion_activa_existente = db.query(models.Edicion).filter(
                models.Edicion.nombre == f"Edición {edicion_anio}",
                models.Edicion.activa == True,
                models.Edicion.id != periodo_id
            ).first()
            
            if db_edicion_activa_existente:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ya existe una edición activa para el año {edicion_anio}. Debe desactivar la edición existente primero."
                )
        except (IndexError, ValueError):
            pass
    
    # Cambiar el estado
    db_edicion.activa = not db_edicion.activa
    db.commit()
    db.refresh(db_edicion)
    
    accion = "activada" if db_edicion.activa else "desactivada"
    return {"mensaje": f"Edición {accion} exitosamente", "edicion": db_edicion}

# ✅ ENDPOINT MODIFICADO: Ya no elimina, solo desactiva
@router.delete("/periodos/{periodo_id}")
async def eliminar_periodo(
    periodo_id: int, 
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(get_admin_user)
):
    """Desactivar una edición (eliminación lógica) - Solo administradores"""
    db_edicion = db.query(models.Edicion).filter(models.Edicion.id == periodo_id).first()
    if db_edicion is None:
        raise HTTPException(status_code=404, detail="Edición no encontrada")
    
    # Verificar si hay solicitudes asociadas
    solicitudes_asociadas = db.query(models.Solicitud).filter(
        (models.Solicitud.periodo == db_edicion.periodo1) |
        (models.Solicitud.periodo == db_edicion.periodo2)
    ).first()
    
    if solicitudes_asociadas:
        # Si hay solicitudes, solo desactivar
        db_edicion.activa = False
        db.commit()
        db.refresh(db_edicion)
        return {"mensaje": "Edición desactivada exitosamente (tiene solicitudes asociadas)"}
    else:
        # Si no hay solicitudes, permitir eliminación física
        db.delete(db_edicion)
        db.commit()
        return {"mensaje": "Edición eliminada exitosamente"}