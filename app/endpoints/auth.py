from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from database.database import get_db
from models import models  # Importar modelos SQLAlchemy
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import Header
from pydantic import BaseModel, constr
from schemas.schemas import (
    CredentialRequest, User, UserCreate, UserUpdate  # Estos son esquemas Pydantic
)

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
if not SECRET_KEY:
    print("SECRET_KEY no encontrada en las variables de entorno.")

router = APIRouter()

def create_access_token(data: Dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/prueba")
async def prueba():
    return {"message": "¡Esta es una prueba desde FastAPI SALUDEEEN!"}

@router.post("/verify-credential")
async def verify_credential(request: CredentialRequest, db: Session = Depends(get_db)):
    try:
        # Usar request.credential en lugar de credential directamente
        decoded = jwt.decode(request.credential, options={"verify_signature": False})
        
        # El resto del código permanece igual...
        google_sub = decoded.get("sub")
        email = decoded.get("email")
        given_name = decoded.get("given_name", "")
        family_name = decoded.get("family_name", "")
        
        # Crear nombre completo
        nombre_completo = f"{family_name} {given_name}".strip()
        
        if not google_sub or not email:
            raise HTTPException(status_code=400, detail="Invalid credential: missing required fields")
        
        # Buscar usuario existente por sub (usando el modelo SQLAlchemy)
        existing_user = db.query(models.User).filter(models.User.sub == google_sub).first()
        
        if existing_user:
            # Usuario ya existe, usar datos existentes
            user_id = existing_user.id
            is_admin = existing_user.admin
            genero = existing_user.genero
        else:
            # Crear nuevo usuario (usando el modelo SQLAlchemy)
            new_user = models.User(
                sub=google_sub,
                nombre=nombre_completo,
                email=email,
                genero=None,  # Será None por defecto
                grado_academico=None,
                admin=False  # Por defecto False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            user_id = new_user.id
            is_admin = new_user.admin
            genero = new_user.genero
        
        # Crear tokens JWT
        token_data = {
            "user_id": user_id,
            "admin": is_admin,
            "sub": google_sub
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user_id,
            "admin": is_admin,
            "genero": genero
        }
        
    except InvalidTokenError as e:
        raise HTTPException(status_code=400, detail=f"Invalid credential: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    



# Endpoint adicional para refresh token
@router.post("/refresh-token")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        # Decodificar el refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Verificar que el usuario aún existe (usando el modelo SQLAlchemy)
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Crear nuevo access token
        token_data = {
            "user_id": user.id,
            "admin": user.admin,
            "sub": user.sub
        }
        
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    


# Modelo Pydantic para la request del género
class UpdateGenderRequest(BaseModel):
    genero: constr(pattern=r'^(Masculino|Femenino)$')  

# Función auxiliar para extraer y validar el token
# Endpoint para actualizar género
@router.put("/update-gender")
async def update_gender(
    request: UpdateGenderRequest,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
):
    """
    Actualiza el género del usuario autenticado.
    
    Headers requeridos:
    - Authorization: Bearer <access_token>
    
    Body:
    - genero: "Masculino" o "Femenino"
    """
    try:
        # Verificar que el header Authorization existe
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extraer el token (formato: "Bearer <token>")
        try:
            scheme, token = authorization.split(' ', 1)  # Usar split con límite
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
        
        # Actualizar el género
        user.genero = request.genero
        
        # Guardar cambios
        db.commit()
        db.refresh(user)
        
        return {
            "message": "Género actualizado exitosamente",
            "user_id": user.id,
            "genero": user.genero,
            "updated_at": user.updated_at
        }
        
    except HTTPException:
        raise  # Re-lanzar HTTPExceptions
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
