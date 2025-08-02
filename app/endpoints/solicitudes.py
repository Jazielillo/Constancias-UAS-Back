from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import re
from datetime import date
from database.database import get_db
from models import models
from schemas.schemas import (
    Solicitud, SolicitudCreate, SolicitudUpdate, SolicitudFormulario,
    CamposDinamicos, Categoria
)

router = APIRouter()

def extraer_campos_de_plantilla(descripcion: str) -> List[str]:
    """
    Extrae los campos dinámicos de una descripción con formato {campo}
    Ejemplo: "Constancia para {grado} {nombre}" -> ["grado", "nombre"]
    """
    if not descripcion:
        return []
    
    # Buscar todos los patrones {campo}
    patron = r'\{([^}]+)\}'
    campos = re.findall(patron, descripcion)
    return campos

def reemplazar_campos_en_plantilla(plantilla: str, datos: dict) -> str:
    """
    Reemplaza los campos {campo} en la plantilla con los valores del diccionario
    """
    if not plantilla:
        return ""
    
    descripcion_final = plantilla
    for campo, valor in datos.items():
        descripcion_final = descripcion_final.replace(f"{{{campo}}}", str(valor))
    
    return descripcion_final

# # ENDPOINTS PARA USUARIOS
# @router.get("/usuarios/{user_id}")
# async def obtener_usuario(user_id: int, db: Session = Depends(get_db)):
#     """Obtener datos del usuario logueado"""
#     usuario = db.query(models.User).filter(models.User.id == user_id).first()
#     if usuario is None:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
#     return {
#         "id": usuario.id,
#         "nombre": usuario.nombre,
#         "email": usuario.email,
#         "genero": usuario.genero,
#         "grado_academico": usuario.grado_academico
#     }

# # ENDPOINTS PARA CATEGORÍAS (necesarios para obtener las plantillas)
# @router.get("/categorias", response_model=List[Categoria])
# async def listar_categorias(db: Session = Depends(get_db)):
#     """Listar todas las categorías activas"""
#     categorias = db.query(models.Categoria).filter(models.Categoria.activo == True).all()
#     return categorias

# @router.get("/categorias/{categoria_id}/campos-dinamicos", response_model=CamposDinamicos)
# async def obtener_campos_dinamicos(categoria_id: int, db: Session = Depends(get_db)):
#     """
#     Obtiene los campos dinámicos de una categoría basados en su descripción
#     """
#     categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
#     if categoria is None:
#         raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
#     campos = extraer_campos_de_plantilla(categoria.descripcion)
    
#     return CamposDinamicos(
#         categoria_id=categoria_id,
#         campos=campos,
#         plantilla=categoria.descripcion or ""
#     )

# # ENDPOINTS PARA EDICIONES
# @router.get("/ediciones", response_model=List[dict])
# async def listar_ediciones(db: Session = Depends(get_db)):
#     """Listar todas las ediciones activas"""
#     ediciones = db.query(models.Edicion).filter(models.Edicion.estado.in_(["programado", "activo"])).all()
    
#     # Formatear la respuesta para incluir los períodos
#     resultado = []
#     for edicion in ediciones:
#         resultado.append({
#             "id": edicion.id,
#             "nombre": edicion.nombre,
#             "periodos": [edicion.periodo1, edicion.periodo2],
#             "fecha_inicio": edicion.fecha_inicio,
#             "fecha_fin": edicion.fecha_fin,
#             "estado": edicion.estado
#         })
    
#     return resultado

# ENDPOINTS PARA SOLICITUDES
@router.get("/usuarios/{user_id}")
async def obtener_usuario(user_id: int, db: Session = Depends(get_db)):
    """Obtener datos del usuario logueado"""
    usuario = db.query(models.User).filter(models.User.id == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "genero": usuario.genero,
        "grado_academico": usuario.grado_academico
    }


# @router.get("/solicitudes", response_model=List[Solicitud])
# async def listar_solicitudes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """Listar todas las solicitudes"""
#     solicitudes = db.query(models.Solicitud).offset(skip).limit(limit).all()
#     return solicitudes

def formatear_grado_academico(grado: str) -> str:
    """
    Formatea el grado académico:
    - Primera letra mayúscula, resto minúsculas
    - Agrega punto al final si no lo tiene
    """
    if not grado:
        return grado
    
    # Limpiar espacios extra
    grado = grado.strip()
    
    # Convertir primera letra a mayúscula y resto a minúsculas
    grado_formateado = grado.capitalize()
    
    # Agregar punto al final si no lo tiene
    if not grado_formateado.endswith('.'):
        grado_formateado += '.'
    
    return grado_formateado

@router.get("/solicitudes")
async def listar_solicitudes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las solicitudes con datos relacionados"""
    solicitudes = db.query(models.Solicitud)\
        .join(models.User)\
        .join(models.Categoria)\
        .join(models.Edicion)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Formatear la respuesta para incluir los datos relacionados
    resultado = []
    for solicitud in solicitudes:
        resultado.append({
            "id": solicitud.id,
            "user_id": solicitud.user_id,
            "categoria_id": solicitud.categoria_id,
            "edicion_id": solicitud.edicion_id,
            "periodo": solicitud.periodo,
            "grado_academico": solicitud.grado_academico,
            "descripcion": solicitud.descripcion,
            "fecha_solicitud": solicitud.fecha_solicitud,
            "estado": solicitud.estado,
            "created_at": solicitud.created_at,
            "updated_at": solicitud.updated_at,
            # Datos relacionados
            "usuario": {
                "nombre": solicitud.usuario.nombre,
                "email": solicitud.usuario.email,
                "genero": solicitud.usuario.genero,
                "grado_academico": solicitud.usuario.grado_academico
            },
            "categoria": {
                "codigo_categoria": solicitud.categoria.codigo_categoria,
                "nombre": solicitud.categoria.nombre
            },
            "edicion": {
                "nombre": solicitud.edicion.nombre
            }
        })
    
    return resultado

@router.post("/solicitudes/formulario")
async def crear_solicitud_desde_formulario(solicitud_form: SolicitudFormulario, db: Session = Depends(get_db)):
    """
    Crear una nueva solicitud procesando la plantilla de la categoría
    """
    # Obtener la categoría para acceder a la plantilla
    categoria = db.query(models.Categoria).filter(models.Categoria.id == solicitud_form.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar que la edición existe
    edicion = db.query(models.Edicion).filter(models.Edicion.id == solicitud_form.edicion_id).first()
    if edicion is None:
        raise HTTPException(status_code=404, detail="Edición no encontrada")
    
    # Verificar que el período es válido para la edición
    if solicitud_form.periodo not in [edicion.periodo1, edicion.periodo2]:
        raise HTTPException(status_code=400, detail="Período no válido para la edición seleccionada")
    
    # Procesar la plantilla
    descripcion_final = reemplazar_campos_en_plantilla(
        categoria.descripcion or "", 
        solicitud_form.datos_dinamicos
    )
    
    # Crear la solicitud
    db_solicitud = models.Solicitud(
        user_id=solicitud_form.datos_dinamicos.get("user_id"),
        categoria_id=solicitud_form.categoria_id,
        edicion_id=solicitud_form.edicion_id,
        periodo=solicitud_form.periodo,
        grado_academico=formatear_grado_academico(solicitud_form.datos_dinamicos.get("grado", "")),
        descripcion=descripcion_final,
        fecha_solicitud=date.today(),
        estado="pendiente"
    )
    
    db.add(db_solicitud)
    db.commit()
    db.refresh(db_solicitud)
    
    return {
        "mensaje": "Solicitud creada exitosamente",
        "solicitud_id": db_solicitud.id,
        "descripcion_generada": descripcion_final
    }

@router.post("/solicitudes", response_model=Solicitud)
async def crear_solicitud(solicitud: SolicitudCreate, db: Session = Depends(get_db)):
    """Crear una nueva solicitud (método tradicional)"""
    solicitud_data = solicitud.dict()
    
    # Si viene con datos_formulario, procesar la plantilla
    if solicitud_data.get("datos_formulario"):
        categoria = db.query(models.Categoria).filter(
            models.Categoria.id == solicitud_data["categoria_id"]
        ).first()
        
        if categoria and categoria.descripcion:
            descripcion_final = reemplazar_campos_en_plantilla(
                categoria.descripcion,
                solicitud_data["datos_formulario"]
            )
            solicitud_data["descripcion"] = descripcion_final
        
        # Remover datos_formulario antes de crear el modelo
        del solicitud_data["datos_formulario"]
    
    db_solicitud = models.Solicitud(**solicitud_data)
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

@router.get("/usuarios/{user_id}/solicitudes")
async def listar_solicitudes_usuario(user_id: int, db: Session = Depends(get_db)):
    """Listar solicitudes de un usuario específico con datos relacionados"""
    solicitudes = db.query(models.Solicitud)\
        .join(models.User)\
        .join(models.Categoria)\
        .join(models.Edicion)\
        .filter(models.Solicitud.user_id == user_id)\
        .order_by(models.Solicitud.created_at.desc())\
        .all()
    
    # Formatear la respuesta (SIN incluir descripción)
    resultado = []
    for solicitud in solicitudes:
        resultado.append({
            "id": solicitud.id,
            "fecha_solicitud": solicitud.fecha_solicitud,
            "estado": solicitud.estado,
            "grado_academico": solicitud.grado_academico,
            "periodo": solicitud.periodo,
            "created_at": solicitud.created_at,
            # Datos relacionados
            "categoria": {
                "codigo_categoria": solicitud.categoria.codigo_categoria,
                "nombre": solicitud.categoria.nombre
            },
            "edicion": {
                "nombre": solicitud.edicion.nombre
            }
            # Nota: NO incluimos descripción ni datos completos del usuario
        })
    
    return resultado


