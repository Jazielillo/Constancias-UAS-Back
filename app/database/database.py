from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la base de datos SIN comillas en .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear engine (sin connect_args porque no es SQLite)
engine = create_engine(DATABASE_URL)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos ORM
Base = declarative_base()

# Dependency para obtener la sesión de base de datos (FastAPI lo usará con Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
