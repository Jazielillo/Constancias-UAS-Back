# models.py - SQLAlchemy Models
from sqlalchemy import Boolean, Column, Integer, String, Text, Date, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    genero = Column(String(20), nullable=True)
    grado_academico = Column(String(100), nullable=True)
    admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="usuario")

class Programa(Base):
    __tablename__ = "programas"
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="programa")

class Categoria(Base):
    __tablename__ = "categorias"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo_categoria = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="categoria")

class Periodo(Base):
    __tablename__ = "periodos"
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    semestre = Column(String(20), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String(20), default="programado")  # programado, activo, finalizado, borrador
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="periodo")

class Solicitud(Base):
    __tablename__ = "solicitudes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    programa_id = Column(BigInteger, ForeignKey("programas.id"), nullable=False)
    categoria_id = Column(BigInteger, ForeignKey("categorias.id"), nullable=False)
    periodo_id = Column(BigInteger, ForeignKey("periodos.id"), nullable=False)
    asignatura = Column(String(255), nullable=False)
    fecha_solicitud = Column(Date, nullable=False)
    estado = Column(String(20), default="pendiente")  # pendiente, aceptado, rechazado
    observaciones = Column(Text, nullable=True)
    fecha_procesado = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("User", back_populates="solicitudes")
    programa = relationship("Programa", back_populates="solicitudes")
    categoria = relationship("Categoria", back_populates="solicitudes")
    periodo = relationship("Periodo", back_populates="solicitudes")
