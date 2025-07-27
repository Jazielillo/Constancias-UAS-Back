

# # Enums para estados
# class EstadoSolicitud(str, Enum):
#     PENDIENTE = "pendiente"
#     ACEPTADO = "aceptado"
#     RECHAZADO = "rechazado"

# class EstadoPeriodo(str, Enum):
#     PROGRAMADO = "programado"
#     ACTIVO = "activo"
#     FINALIZADO = "finalizado"
#     BORRADOR = "borrador"

# class Genero(str, Enum):
#     MASCULINO = "masculino"
#     FEMENINO = "femenino"
#     OTRO = "otro"


# schemas/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# Esquemas para Constancias
class ConstanciaIndividual(BaseModel):
    pseudonimo: str
    grado: str
    nombre: str
    area: str
    programa: str
    semestre: str
    ciclo_escolar: str
    fecha_emision: str
    idcategoria: str
    asignatura: str
    email: EmailStr
    curso: Optional[str] = None
    instructor: Optional[str] = None
    periodo: Optional[str] = None

class ConstanciaResponse(BaseModel):
    id: str
    nombre: str
    archivo_pdf: str
    qr_code: str
    url_validacion: str
    status: str

class ConstanciaValidacion(BaseModel):
    valida: bool
    id: str
    url_validacion: Optional[str] = None
    mensaje: Optional[str] = None

# Esquemas para Usuario
class UserBase(BaseModel):
    nombre: str
    email: EmailStr
    genero: Optional[str] = None
    grado_academico: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    genero: Optional[str] = None
    grado_academico: Optional[str] = None
    admin: Optional[bool] = None

class User(UserBase):
    id: int
    admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas para Programa
class ProgramaBase(BaseModel):
    nombre: str
    codigo: str

class ProgramaCreate(ProgramaBase):
    pass

class ProgramaUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None

class Programa(ProgramaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas para Categoría
class CategoriaBase(BaseModel):
    codigo_categoria: str
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    codigo_categoria: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class Categoria(CategoriaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas para Período
class PeriodoBase(BaseModel):
    nombre: str
    semestre: str
    fecha_inicio: date
    fecha_fin: date
    estado: str = "programado"

class PeriodoCreate(PeriodoBase):
    pass

class PeriodoUpdate(BaseModel):
    nombre: Optional[str] = None
    semestre: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = None

class Periodo(PeriodoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas para Solicitud
class SolicitudBase(BaseModel):
    programa_id: int
    categoria_id: int
    periodo_id: int
    asignatura: str
    fecha_solicitud: date
    observaciones: Optional[str] = None

class SolicitudCreate(SolicitudBase):
    user_id: int

class SolicitudUpdate(BaseModel):
    programa_id: Optional[int] = None
    categoria_id: Optional[int] = None
    periodo_id: Optional[int] = None
    asignatura: Optional[str] = None
    fecha_solicitud: Optional[date] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_procesado: Optional[datetime] = None

class Solicitud(SolicitudBase):
    id: int
    user_id: int
    estado: str
    fecha_procesado: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relaciones
    usuario: Optional[User] = None
    programa: Optional[Programa] = None
    categoria: Optional[Categoria] = None
    periodo: Optional[Periodo] = None
    
    class Config:
        from_attributes = True