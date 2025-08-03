from sqlalchemy import Boolean, Column, Integer, String, Text, Date, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    sub = Column(String(255), unique=True, index=True, nullable=False)  # Google sub ID
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    genero = Column(String(20), nullable=True, default=None)  # Nullable por defecto
    grado_academico = Column(String(100), nullable=True)
    admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="usuario")

    
# class Programa(Base):
#     __tablename__ = "programas"
    
#     id = Column(BigInteger, primary_key=True, index=True)
#     nombre = Column(String(255), nullable=False)
#     codigo = Column(String(50), unique=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
#     # Relaciones
#     solicitudes = relationship("Solicitud", back_populates="programa")

class Categoria(Base):
    __tablename__ = "categorias"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo_categoria = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    asunto = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="categoria")

class Edicion(Base):
    __tablename__ = "ediciones"
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    periodo1 = Column(String(20), nullable=False)  
    periodo2 = Column(String(20), nullable=False)  
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String(20), default="programado")  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Agregar esta relación
    solicitudes = relationship("Solicitud", back_populates="edicion")
    

class Solicitud(Base):
    __tablename__ = "solicitudes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    grado_academico = Column(String(100), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    categoria_id = Column(BigInteger, ForeignKey("categorias.id"), nullable=False)
    edicion_id = Column(BigInteger, ForeignKey("ediciones.id"), nullable=False)
    periodo = Column(String(20), nullable=False)
    descripcion = Column(Text, nullable=True) 
    fecha_solicitud = Column(Date, nullable=False)
    estado = Column(String(20), default="pendiente")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("User", back_populates="solicitudes")
    categoria = relationship("Categoria", back_populates="solicitudes")
    edicion = relationship("Edicion", back_populates="solicitudes")  # Esta línea ya la tienes


class DatosFijos(Base):
    __tablename__ = "datos_fijos"
    
    id = Column(BigInteger, primary_key=True, index=True)
    texto_aqc = Column(Text, nullable=True)
    texto_remitente = Column(Text, nullable=True)
    texto_apeticion = Column(Text, nullable=True)
    texto_atte = Column(Text, nullable=True)
    texto_sursum = Column(Text, nullable=True)
    texto_nombrefirma = Column(String(255), nullable=True)
    texto_cargo = Column(String(255), nullable=True)
    texto_msgdigital = Column(Text, nullable=True)
    texto_ccp = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConstanciaGenerada(Base):
    __tablename__ = "constancias_generadas"
    
    id = Column(Integer, primary_key=True, index=True)
    qr_id = Column(String(255), unique=True, index=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    grado = Column(String(100))
    pseudonimo = Column(String(10))
    texto_asunto = Column(Text)
    texto_consta = Column(Text)
    fecha_emision = Column(String(100))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    archivo_pdf = Column(String(500))
    es_valida = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ConstanciaGenerada(qr_id='{self.qr_id}', nombre='{self.nombre}')>"