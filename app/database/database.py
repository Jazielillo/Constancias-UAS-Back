from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Tu URL de conexión de Neon
SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_no19BxDCKMAr@ep-restless-field-af8c9iq1-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Crea el engine de SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Crea una sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para heredar tus modelos
Base = declarative_base()
