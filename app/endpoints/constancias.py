from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from pdf_generator import PDFGenerator
from config.config import settings
from database.database import get_db
from models.models import DatosFijos
import os
import uuid
from datetime import datetime

router = APIRouter()
pdf_generator = PDFGenerator()

def formatear_fecha(fecha_str: str) -> str:
    """Convertir fecha de dd/mm/yyyy a formato textual completo"""
    try:
        # Parsear la fecha
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
        
        # Diccionarios para conversión
        meses = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        unidades = {
            0: "", 1: "un", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
            6: "seis", 7: "siete", 8: "ocho", 9: "nueve"
        }
        
        decenas = {
            10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce",
            15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho",
            19: "diecinueve", 20: "veinte", 30: "treinta"
        }
        
        def numero_a_texto(num):
            """Convertir número a texto"""
            if num == 0:
                return "cero"
            elif 1 <= num <= 9:
                return unidades[num]
            elif 10 <= num <= 20:
                return decenas[num]
            elif 21 <= num <= 29:
                return f"veinti{unidades[num - 20]}"
            elif num == 30:
                return "treinta"
            elif 31 <= num <= 31:
                return f"treinta y {unidades[num - 30]}"
            else:
                return str(num)  # Fallback para números mayores
        
        def año_a_texto(año):
            """Convertir año a texto"""
            if año >= 2000 and año <= 2099:
                decena = año - 2000
                if decena == 0:
                    return "dos mil"
                elif 1 <= decena <= 9:
                    return f"dos mil {unidades[decena]}"
                elif decena == 10:
                    return "dos mil diez"
                elif 11 <= decena <= 19:
                    return f"dos mil {decenas[decena]}"
                elif decena == 20:
                    return "dos mil veinte"
                elif 21 <= decena <= 29:
                    return f"dos mil veinti{unidades[decena - 20]}"
                elif decena == 30:
                    return "dos mil treinta"
                elif 31 <= decena <= 39:
                    return f"dos mil treinta y {unidades[decena - 30]}"
                elif decena == 40:
                    return "dos mil cuarenta"
                elif 41 <= decena <= 49:
                    return f"dos mil cuarenta y {unidades[decena - 40]}"
                elif decena == 50:
                    return "dos mil cincuenta"
                elif 51 <= decena <= 59:
                    return f"dos mil cincuenta y {unidades[decena - 50]}"
                elif decena == 60:
                    return "dos mil sesenta"
                elif 61 <= decena <= 69:
                    return f"dos mil sesenta y {unidades[decena - 60]}"
                elif decena == 70:
                    return "dos mil setenta"
                elif 71 <= decena <= 79:
                    return f"dos mil setenta y {unidades[decena - 70]}"
                elif decena == 80:
                    return "dos mil ochenta"
                elif 81 <= decena <= 89:
                    return f"dos mil ochenta y {unidades[decena - 80]}"
                elif decena == 90:
                    return "dos mil noventa"
                elif 91 <= decena <= 99:
                    return f"dos mil noventa y {unidades[decena - 90]}"
            return str(año)  # Fallback
        
        dia = fecha_obj.day
        mes = fecha_obj.month
        año = fecha_obj.year
        
        dia_texto = numero_a_texto(dia)
        mes_texto = meses[mes]
        año_texto = año_a_texto(año)
        
        # Determinar si es "día" o "días"
        dia_palabra = "día" if dia == 1 else "días"
        
        return f"{dia_texto} {dia_palabra} del mes de {mes_texto} del año {año_texto}"
        
    except ValueError:
        # Si hay error en el formato, devolver la fecha original
        return fecha_str

class ConstanciaRequest(BaseModel):
    pseudonimo: str
    grado: str
    nombre: str
    texto_asunto: str
    texto_consta: str
    fecha_emision: str  # Formato: dd/mm/yyyy

class ConstanciaResponse(BaseModel):
    id: str
    nombre: str
    archivo_pdf: str
    qr_code: str
    url_validacion: str
    status: str

@router.post("/constancia/individual", response_model=ConstanciaResponse)
async def generar_constancia_individual(constancia: ConstanciaRequest, db: Session = Depends(get_db)):
    """Generar una constancia individual con datos simplificados"""
    try:
        # Obtener datos fijos de la base de datos
        datos_fijos = db.query(DatosFijos).first()
        if not datos_fijos:
            raise HTTPException(status_code=500, detail="No se encontraron datos fijos en la base de datos")
        
        # Generar ID único para la constancia
        idqrcode = str(uuid.uuid4())
        
        # Generar QR code
        pdf_generator.generar_qrcode(idqrcode)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_pdf = f"{settings.CONSTANCIAS_DIR}/Constancia_{constancia.nombre}_{timestamp}.pdf"
        
        # Formatear la fecha de emisión
        fecha_formateada = formatear_fecha(constancia.fecha_emision)
        
        # Formatear el asunto
        asunto_formateado = f"ASUNTO: {constancia.texto_asunto}"
        
        # Generar constancia con datos fijos y variables
        pdf_generator.generar_constancia_simplificada(
            # Datos del QR y archivo
            idqrcode=idqrcode,
            archivo_pdf=archivo_pdf,
            
            # Datos fijos de la DB
            texto_aqc=datos_fijos.texto_aqc,
            texto_remitente=datos_fijos.texto_remitente,
            texto_apeticion=datos_fijos.texto_apeticion,
            texto_atte=datos_fijos.texto_atte,
            texto_sursum=datos_fijos.texto_sursum,
            texto_nombrefirma=datos_fijos.texto_nombrefirma,
            texto_cargo=datos_fijos.texto_cargo,
            texto_msgdigital=datos_fijos.texto_msgdigital,
            texto_ccp=datos_fijos.texto_ccp,
            
            # Datos variables del request
            pseudonimo=constancia.pseudonimo,
            grado=constancia.grado,
            nombre=constancia.nombre,
            texto_asunto=asunto_formateado,
            texto_consta=constancia.texto_consta,
            fecha_emision=fecha_formateada,
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

@router.get("/validar/{qr_id}")
async def validar_constancia(qr_id: str):
    """Validar constancia por ID del QR"""
    qr_path = f"{settings.QR_DIR}/{qr_id}.png"
    
    if os.path.exists(qr_path):
        return {
            "valida": True,
            "id": qr_id,
            "url_validacion": f"{settings.VALIDATION_BASE_URL}{qr_id}"
        }
    else:
        return {
            "valida": False,
            "id": qr_id,
            "mensaje": "Constancia no encontrada"
        }

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
    
# Agregar este endpoint a tu archivo de rutas de solicitudes

@router.get("/solicitudes/{solicitud_id}/constancia")
async def obtener_constancia_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    """Obtener PDF de constancia para una solicitud específica"""
    try:
        # Buscar la solicitud con sus relaciones
        solicitud = db.query(Solicitud).options(
            joinedload(Solicitud.usuario),
            joinedload(Solicitud.categoria),
            joinedload(Solicitud.edicion)
        ).filter(Solicitud.id == solicitud_id).first()
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        # Verificar que la solicitud esté aceptada
        if solicitud.estado.lower() != 'aceptado':
            raise HTTPException(status_code=400, detail="La constancia solo está disponible para solicitudes aceptadas")
        
        # Obtener datos fijos de la base de datos
        datos_fijos = db.query(DatosFijos).first()
        if not datos_fijos:
            raise HTTPException(status_code=500, detail="No se encontraron datos fijos en la base de datos")
        
        # Generar ID único para la constancia si no existe
        idqrcode = f"solicitud_{solicitud_id}_{uuid.uuid4()}"
        
        # Generar QR code
        pdf_generator.generar_qrcode(idqrcode)
        
        # Generar nombre de archivo temporal
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_pdf = f"{settings.CONSTANCIAS_DIR}/Constancia_Solicitud_{solicitud_id}_{timestamp}.pdf"
        
        # Formatear la fecha de emisión (usar fecha actual)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        fecha_formateada = formatear_fecha(fecha_actual)
        
        # Formatear el asunto usando el asunto de la categoría
        asunto_formateado = f"ASUNTO: {solicitud.categoria.asunto}"
        
        # Generar texto de constancia basado en la descripción de la solicitud
        texto_consta = solicitud.descripcion or f"Constancia para {solicitud.categoria.nombre} - {solicitud.edicion.nombre} - {solicitud.periodo}"
        
        # Determinar pseudónimo basado en género
        pseudonimo = "C." if solicitud.usuario.genero and solicitud.usuario.genero.lower() == 'masculino' else "C."
        
        # Usar el grado académico de la solicitud o del usuario
        grado = solicitud.grado_academico or solicitud.usuario.grado_academico or ""
        
        # Generar constancia con datos fijos y variables
        pdf_generator.generar_constancia_simplificada(
            # Datos del QR y archivo
            idqrcode=idqrcode,
            archivo_pdf=archivo_pdf,
            
            # Datos fijos de la DB
            texto_aqc=datos_fijos.texto_aqc,
            texto_remitente=datos_fijos.texto_remitente,
            texto_apeticion=datos_fijos.texto_apeticion,
            texto_atte=datos_fijos.texto_atte,
            texto_sursum=datos_fijos.texto_sursum,
            texto_nombrefirma=datos_fijos.texto_nombrefirma,
            texto_cargo=datos_fijos.texto_cargo,
            texto_msgdigital=datos_fijos.texto_msgdigital,
            texto_ccp=datos_fijos.texto_ccp,
            
            # Datos variables de la solicitud
            pseudonimo=pseudonimo,
            grado=grado,
            nombre=solicitud.usuario.nombre,
            texto_asunto=asunto_formateado,
            texto_consta=texto_consta,
            fecha_emision=fecha_formateada,
        )
        
        # Verificar que el archivo se haya generado
        if not os.path.exists(archivo_pdf):
            raise HTTPException(status_code=500, detail="Error al generar el PDF")
        
        # Retornar el archivo PDF
        return FileResponse(
            path=archivo_pdf,
            filename=f"Constancia_Solicitud_{solicitud_id}.pdf",
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar constancia: {str(e)}")
