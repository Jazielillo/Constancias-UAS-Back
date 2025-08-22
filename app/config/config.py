# config.py
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

class Settings:
    # Configuración de la aplicación
    APP_NAME = "API de Constancias UAS"
    VERSION = "1.0.0"
    
    # Configuración de directorios
    QR_DIR = "qrs"
    CONSTANCIAS_DIR = "constancias"
    UPLOADS_DIR = "uploads"
    ASSETS_DIR = "../assets"
    
    # Configuración de archivos de assets
    HEADER_IMAGE = f"{ASSETS_DIR}/cabecera.png"
    FOOTER_IMAGE = f"{ASSETS_DIR}/pie.png"
    SIGNATURE_IMAGE = f"{ASSETS_DIR}/firma.png"
    
    # Configuración de la universidad
    UNIVERSITY_NAME = "UNIVERSIDAD AUTÓNOMA DE SINALOA"
    FACULTY_NAME = "Facultad de Ingeniería Mochis"
    DIRECTOR_NAME = "DR. RODY ABRAHAM SOTO ROJO"
    DIRECTOR_TITLE = "DIRECTOR"
    
    # URL base para validación
    VALIDATION_BASE_URL = "http://localhost:8080/validacion/"
    
    # Configuración de constancias
    COMMISSION_TEXT = """COMISIÓN DE EVALUACIÓN DEL PROGRAMA DE ESTÍMULOS<br />
AL DESEMPEÑO DEL PERSONAL DOCENTE 2025-2026<br />
UNIVERSIDAD AUTÓNOMA DE SINALOA"""
    
    REMITENTE_TEXT = "El suscrito C. Dr. Rody Abraham Soto Rojo, Director de la Facultad de Ingeniería Mochis, dependiente de la Universidad Autónoma de Sinaloa, hace constar que"

settings = Settings()