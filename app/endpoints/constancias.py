from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from schemas.schemas import ConstanciaIndividual, ConstanciaResponse, ConstanciaValidacion
from pdf_generator import PDFGenerator
from config.config import settings
import os
import uuid
from datetime import datetime

router = APIRouter()
pdf_generator = PDFGenerator()

@router.post("/constancia/individual", response_model=ConstanciaResponse)
async def generar_constancia_individual(constancia: ConstanciaIndividual):
    """Generar una constancia individual"""
    try:
        # Generar ID único para la constancia
        idqrcode = str(uuid.uuid4())
        
        # Generar QR code
        pdf_generator.generar_qrcode(idqrcode)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_pdf = f"{settings.CONSTANCIAS_DIR}/Constancia_{constancia.nombre}_{timestamp}.pdf"
        
        # Generar constancia
        pdf_generator.generar_constancia(
            idqrcode=idqrcode,
            pseudonimo=constancia.pseudonimo,
            grado=constancia.grado,
            nombre=constancia.nombre,
            area=constancia.area,
            programa=constancia.programa,
            semestre=constancia.semestre,
            ciclo_escolar=constancia.ciclo_escolar,
            fecha_emision=constancia.fecha_emision,
            archivo_pdf=archivo_pdf,
            idcategoria=constancia.idcategoria,
            asignatura=constancia.asignatura,
            email=constancia.email,
            curso=constancia.curso,
            instructor=constancia.instructor,
            periodo=constancia.periodo
        )
        
        return ConstanciaResponse(
            id=idqrcode,
            nombre=constancia.nombre,
            archivo_pdf=archivo_pdf,
            qr_code=f"{settings.QR_DIR}/{idqrcode}.png",
            url_validacion=f"{settings.VALIDATION_BASE_URL}{idqrcode}",
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar constancia: {str(e)}")

@router.get("/constancia/download/{filename}")
async def descargar_constancia(filename: str):
    """Descargar archivo de constancia"""
    file_path = f"{settings.CONSTANCIAS_DIR}/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )

@router.get("/qr/{qr_id}")
async def obtener_qr(qr_id: str):
    """Obtener código QR"""
    qr_path = f"{settings.QR_DIR}/{qr_id}.png"
    
    if not os.path.exists(qr_path):
        raise HTTPException(status_code=404, detail="QR no encontrado")
    
    return FileResponse(
        path=qr_path,
        filename=f"{qr_id}.png",
        media_type='image/png'
    )

@router.get("/categorias")
async def obtener_categorias():
    """Obtener lista de categorías de constancias disponibles"""
    categorias = {
        "1.1.1.2.1": "Curso de actualización disciplinar con evaluación",
        "1.1.1.2.2": "Curso de formación docente con evaluación",
        "1.2.2.4": "Publicación de antologías",
        "1.2.2.5": "Elaboración de apuntes",
        "1.2.2.8": "Elaboración de manual de prácticas",
        "1.2.3.3": "Programas de unidad de aprendizaje",
        "1.2.4.2": "Diseño e impartición de programa de cursos en modalidades no escolarizada y dual",
        "1.2.4.3": "Material pedagógico innovador con nuevas tecnologías",
        "1.4.1.10": "Cursos de regularización",
        "1.5.1.3": "Organización de eventos académicos",
        "1.5.1.8": "Elaboración de exámenes departamentales",
        "1.5.1.19": "Coordinación de academia"
    }
    
    return {"categorias": categorias}

@router.get("/validar/{qr_id}", response_model=ConstanciaValidacion)
async def validar_constancia(qr_id: str):
    """Validar constancia por ID del QR"""
    qr_path = f"{settings.QR_DIR}/{qr_id}.png"
    
    if os.path.exists(qr_path):
        return ConstanciaValidacion(
            valida=True,
            id=qr_id,
            url_validacion=f"{settings.VALIDATION_BASE_URL}{qr_id}"
        )
    else:
        return ConstanciaValidacion(
            valida=False,
            id=qr_id,
            mensaje="Constancia no encontrada"
        )

@router.delete("/constancia/{qr_id}")
async def eliminar_constancia(qr_id: str):
    """Eliminar constancia y su QR asociado"""
    qr_path = f"{settings.QR_DIR}/{qr_id}.png"
    constancia_encontrada = False
    
    # Buscar y eliminar PDF
    for filename in os.listdir(settings.CONSTANCIAS_DIR):
        if qr_id in filename:
            os.remove(f"{settings.CONSTANCIAS_DIR}/{filename}")
            constancia_encontrada = True
    
    # Eliminar QR
    if os.path.exists(qr_path):
        os.remove(qr_path)
        constancia_encontrada = True
    
    if constancia_encontrada:
        return {"mensaje": "Constancia eliminada exitosamente"}
    else:
        raise HTTPException(status_code=404, detail="Constancia no encontrada")