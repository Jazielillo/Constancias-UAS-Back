# schemas.py - Pydantic Schemas
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Enums para estados
class EstadoSolicitud(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"

class EstadoPeriodo(str, Enum):
    PROGRAMADO = "programado"
    ACTIVO = "activo"
    FINALIZADO = "finalizado"
    BORRADOR = "borrador"

class Genero(str, Enum):
    MASCULINO = "masculino"
    FEMENINO = "femenino"
    OTRO = "otro"

# User Schemas
class UserBase(BaseModel):
    nombre: str
    email: EmailStr
    genero: Optional[Genero] = None
    grado_academico: Optional[str] = None
    admin: bool = False

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    genero: Optional[Genero] = None
    grado_academico: Optional[str] = None
    admin: Optional[bool] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Programa Schemas
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

# Categoria Schemas
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

# Periodo Schemas
class PeriodoBase(BaseModel):
    nombre: str
    semestre: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoPeriodo = EstadoPeriodo.PROGRAMADO

    @validator('fecha_fin')
    def validate_fecha_fin(cls, v, values):
        if 'fecha_inicio' in values and v <= values['fecha_inicio']:
            raise ValueError('La fecha fin debe ser posterior a la fecha inicio')
        return v

class PeriodoCreate(PeriodoBase):
    pass

class PeriodoUpdate(BaseModel):
    nombre: Optional[str] = None
    semestre: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[EstadoPeriodo] = None

class Periodo(PeriodoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Solicitud Schemas
class SolicitudBase(BaseModel):
    user_id: int
    programa_id: int
    categoria_id: int
    periodo_id: int
    asignatura: str
    fecha_solicitud: date
    observaciones: Optional[str] = None

class SolicitudCreate(SolicitudBase):
    pass

class SolicitudUpdate(BaseModel):
    programa_id: Optional[int] = None
    categoria_id: Optional[int] = None
    periodo_id: Optional[int] = None
    asignatura: Optional[str] = None
    fecha_solicitud: Optional[date] = None
    estado: Optional[EstadoSolicitud] = None
    observaciones: Optional[str] = None

class SolicitudAdmin(BaseModel):
    estado: EstadoSolicitud
    observaciones: Optional[str] = None

class Solicitud(SolicitudBase):
    id: int
    estado: EstadoSolicitud
    fecha_procesado: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Schemas con relaciones para respuestas completas
class SolicitudWithRelations(Solicitud):
    usuario: User
    programa: Programa
    categoria: Categoria
    periodo: Periodo

class UserWithSolicitudes(User):
    solicitudes: List[Solicitud] = []

class ProgramaWithSolicitudes(Programa):
    solicitudes: List[Solicitud] = []

class CategoriaWithSolicitudes(Categoria):
    solicitudes: List[Solicitud] = []

class PeriodoWithSolicitudes(Periodo):
    solicitudes: List[Solicitud] = []

# Schemas para respuestas de listas con paginación
class PaginatedResponse(BaseModel):
    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int

class SolicitudesPaginated(BaseModel):
    items: List[SolicitudWithRelations]
    total: int
    page: int
    size: int
    pages: int

class UsersPaginated(BaseModel):
    items: List[User]
    total: int
    page: int
    size: int
    pages: int

# Schemas para filtros
class SolicitudFilters(BaseModel):
    user_id: Optional[int] = None
    programa_id: Optional[int] = None
    categoria_id: Optional[int] = None
    periodo_id: Optional[int] = None
    estado: Optional[EstadoSolicitud] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None

class PeriodoFilters(BaseModel):
    estado: Optional[EstadoPeriodo] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None

# Schemas para estadísticas
class EstadisticasSolicitudes(BaseModel):
    total_solicitudes: int
    pendientes: int
    aceptadas: int
    rechazadas: int
    por_programa: dict
    por_categoria: dict
    por_periodo: dict

# Schema para respuestas de API
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[BaseModel] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None