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


class CredentialRequest(BaseModel):
    credential: str

    
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
    asunto: str
    descripcion: Optional[str] = None
    activo: bool = True

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    codigo_categoria: Optional[str] = None
    nombre: Optional[str] = None
    asunto: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class Categoria(CategoriaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas para Período (ahora Ediciones)
class PeriodoBase(BaseModel):
    nombre: str
    periodo1: str  # Cambio: era semestre
    periodo2: str  # Nuevo campo
    fecha_inicio: date
    fecha_fin: date
    estado: str = "programado"

class PeriodoCreate(PeriodoBase):
    pass

class PeriodoUpdate(BaseModel):
    nombre: Optional[str] = None
    periodo1: Optional[str] = None  # Cambio: era semestre
    periodo2: Optional[str] = None  # Nuevo campo
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
    periodo: str  # Cambio: era periodo_id (int), ahora es periodo (str)
    asignatura: str
    fecha_solicitud: date
    observaciones: Optional[str] = None

class SolicitudCreate(SolicitudBase):
    user_id: int

class SolicitudUpdate(BaseModel):
    programa_id: Optional[int] = None
    categoria_id: Optional[int] = None
    periodo: Optional[str] = None  # Cambio: era periodo_id
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
    
    # Relaciones actualizadas
    usuario: Optional[User] = None
    programa: Optional[Programa] = None
    categoria: Optional[Categoria] = None
    # Ya no hay relación con periodo (era objeto Periodo, ahora es string)
    
    class Config:
        from_attributes = True


class EdicionBase(BaseModel):
    nombre: str
    periodo1: str
    periodo2: str
    fecha_inicio: date
    fecha_fin: date
    estado: str = "programado"

class EdicionCreate(EdicionBase):
    pass

class EdicionUpdate(BaseModel):
    nombre: Optional[str] = None
    periodo1: Optional[str] = None
    periodo2: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = None

class Edicion(EdicionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas para Solicitud
class SolicitudBase(BaseModel):
    categoria_id: int
    edicion_id: int
    periodo: str
    descripcion: Optional[str] = None
    fecha_solicitud: date

class SolicitudCreate(SolicitudBase):
    user_id: int
    # Campos adicionales para procesar la plantilla
    datos_formulario: Optional[dict] = None

class SolicitudUpdate(BaseModel):
    categoria_id: Optional[int] = None
    edicion_id: Optional[int] = None
    periodo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_solicitud: Optional[date] = None
    estado: Optional[str] = None

class Solicitud(SolicitudBase):
    id: int
    user_id: int
    estado: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relaciones
    usuario: Optional[User] = None
    categoria: Optional[Categoria] = None
    edicion: Optional[Edicion] = None
    
    class Config:
        from_attributes = True

# Esquema específico para el formulario de solicitud
class SolicitudFormulario(BaseModel):
    categoria_id: int
    edicion_id: int
    periodo: str
    datos_dinamicos: dict  # Aquí van los valores para reemplazar en la plantilla

# Esquema para obtener campos dinámicos de una categoría
class CamposDinamicos(BaseModel):
    categoria_id: int
    campos: List[str]  # Lista de campos extraídos de la descripción
    plantilla: str     # La descripción original con los marcadores











##DATOS FIJOS
class DatosFijosBase(BaseModel):
    texto_aqc: Optional[str] = None
    texto_remitente: Optional[str] = None
    texto_apeticion: Optional[str] = None
    texto_atte: Optional[str] = None
    texto_sursum: Optional[str] = None
    texto_nombrefirma: Optional[str] = None
    texto_cargo: Optional[str] = None
    texto_msgdigital: Optional[str] = None
    texto_ccp: Optional[str] = None

class DatosFijosUpdate(DatosFijosBase):
    pass

class DatosFijos(DatosFijosBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


##DATOS FIJOS