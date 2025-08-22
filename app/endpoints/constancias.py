# routes/constancias.py - Versión con IDs compatibles
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from sqlalchemy.orm import joinedload
from fastapi import BackgroundTasks
from pdf_generator import PDFGenerator
from config.config import settings
from database.database import get_db
from models.models import DatosFijos, Solicitud, ConstanciaGenerada
from sqlalchemy import Boolean
import os
import secrets
import string
from datetime import datetime

router = APIRouter()
pdf_generator = PDFGenerator()

def generar_id_compatible(longitud=20):
    """Generar ID compatible con el sistema original"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def formatear_fecha(fecha_str: str) -> str:
    """Convertir fecha de dd/mm/yyyy a formato textual completo"""
    # ... tu función existente de formateo de fecha ...
    try:
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
        
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
                return str(num)
        
        def año_a_texto(año):
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
            return str(año)
        
        dia = fecha_obj.day
        mes = fecha_obj.month
        año = fecha_obj.year
        
        dia_texto = numero_a_texto(dia)
        mes_texto = meses[mes]
        año_texto = año_a_texto(año)
        
        dia_palabra = "día" if dia == 1 else "días"
        
        return f"{dia_texto} {dia_palabra} del mes de {mes_texto} del año {año_texto}"
        
    except ValueError:
        return fecha_str

class ConstanciaRequest(BaseModel):
    pseudonimo: str
    grado: str
    nombre: str
    texto_asunto: str
    texto_consta: str
    fecha_emision: str
    
    @validator('grado', 'nombre', pre=True)
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v

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
        
        # CAMBIO IMPORTANTE: Generar ID compatible con el sistema original
        idqrcode = generar_id_compatible(20)  # Genera algo como: vyBjmTqw4EwapcC6FuWg
        
        # Verificar que el ID no exista ya en la BD (por si acaso)
        existing = db.query(ConstanciaGenerada).filter(ConstanciaGenerada.qr_id == idqrcode).first()
        while existing:
            idqrcode = generar_id_compatible(20)
            existing = db.query(ConstanciaGenerada).filter(ConstanciaGenerada.qr_id == idqrcode).first()
        
        # Generar QR code
        pdf_generator.generar_qrcode(idqrcode)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_pdf = f"{settings.CONSTANCIAS_DIR}/Constancia_{constancia.nombre.upper()}_{timestamp}.pdf"
        
        # Formatear la fecha de emisión
        fecha_formateada = formatear_fecha(constancia.fecha_emision)
        
        # Formatear el asunto
        asunto_formateado = f"ASUNTO: {constancia.texto_asunto}"
        
        # Generar constancia con datos fijos y variables
        pdf_generator.generar_constancia_simplificada(
            idqrcode=idqrcode,
            archivo_pdf=archivo_pdf,
            texto_aqc=datos_fijos.texto_aqc,
            texto_remitente=datos_fijos.texto_remitente,
            texto_apeticion=datos_fijos.texto_apeticion,
            texto_atte=datos_fijos.texto_atte,
            texto_sursum=datos_fijos.texto_sursum,
            texto_nombrefirma=datos_fijos.texto_nombrefirma,
            texto_cargo=datos_fijos.texto_cargo,
            texto_msgdigital=datos_fijos.texto_msgdigital,
            texto_ccp=datos_fijos.texto_ccp,
            pseudonimo=constancia.pseudonimo,
            grado=constancia.grado.upper(),
            nombre=constancia.nombre.upper(),
            texto_asunto=asunto_formateado,
            texto_consta=constancia.texto_consta,
            fecha_emision=fecha_formateada,
        )
        
        # Guardar la constancia en la base de datos
        nueva_constancia = ConstanciaGenerada(
            qr_id=idqrcode,
            nombre=constancia.nombre.upper(),
            grado=constancia.grado.upper(),
            pseudonimo=constancia.pseudonimo,
            texto_asunto=asunto_formateado,
            texto_consta=constancia.texto_consta,
            fecha_emision=fecha_formateada,
            archivo_pdf=archivo_pdf,
            es_valida=True
        )
        
        db.add(nueva_constancia)
        db.commit()
        db.refresh(nueva_constancia)
        
        return ConstanciaResponse(
            id=idqrcode,
            nombre=constancia.nombre.upper(),
            archivo_pdf=archivo_pdf,
            qr_code=f"{settings.QR_DIR}/{idqrcode}.png",
            url_validacion=f"{settings.VALIDATION_BASE_URL}{idqrcode}",
            status="success"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar constancia: {str(e)}")

@router.get("/solicitudes/{solicitud_id}/constancia")
async def obtener_constancia_solicitud(
    solicitud_id: int, 
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
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
        
        if solicitud.estado.lower() != 'aceptado':
            raise HTTPException(status_code=400, detail="La constancia solo está disponible para solicitudes aceptadas")
        
        # Obtener datos fijos de la base de datos
        datos_fijos = db.query(DatosFijos).first()
        if not datos_fijos:
            raise HTTPException(status_code=500, detail="No se encontraron datos fijos en la base de datos")
        
        # CAMBIO IMPORTANTE: Usar ID compatible en lugar del formato largo
        idqrcode = generar_id_compatible(20)
        
        # Verificar que el ID no exista ya
        existing = db.query(ConstanciaGenerada).filter(ConstanciaGenerada.qr_id == idqrcode).first()
        while existing:
            idqrcode = generar_id_compatible(20)
            existing = db.query(ConstanciaGenerada).filter(ConstanciaGenerada.qr_id == idqrcode).first()
        
        # Generar QR code
        pdf_generator.generar_qrcode(idqrcode)
        
        # Generar nombre de archivo temporal
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_pdf = f"{settings.CONSTANCIAS_DIR}/Constancia_Solicitud_{solicitud_id}_{timestamp}.pdf"
        qr_path = f"{settings.QR_DIR}/{idqrcode}.png"
        
        # Formatear la fecha de emisión (usar fecha actual)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        fecha_formateada = formatear_fecha(fecha_actual)
        
        # Formatear el asunto usando el asunto de la categoría
        asunto_formateado = f"ASUNTO: {solicitud.categoria.asunto}"
        
        # Generar texto de constancia basado en la descripción de la solicitud
        texto_consta = solicitud.descripcion or f"Constancia para {solicitud.categoria.nombre} - {solicitud.edicion.nombre} - {solicitud.periodo}"
        
        # Determinar pseudónimo basado en género
        if solicitud.usuario.genero and solicitud.usuario.genero.lower() == 'masculino':
            pseudonimo = "el"
        elif solicitud.usuario.genero and solicitud.usuario.genero.lower() == 'femenino':
            pseudonimo = "la"
        else:
            pseudonimo = "el/la"
        
        # Usar el grado académico de la solicitud o del usuario
        grado = (solicitud.grado_academico or solicitud.usuario.grado_academico or "").upper()
        
        # Guardar en BD antes de generar PDF
        nueva_constancia = ConstanciaGenerada(
            qr_id=idqrcode,
            nombre=solicitud.usuario.nombre.upper(),
            grado=grado,
            pseudonimo=pseudonimo,
            texto_asunto=asunto_formateado,
            texto_consta=texto_consta,
            fecha_emision=fecha_formateada,
            archivo_pdf=archivo_pdf,
            es_valida=True
        )
        
        db.add(nueva_constancia)
        db.commit()
        db.refresh(nueva_constancia)
        
        # Generar constancia
        pdf_generator.generar_constancia_simplificada(
            idqrcode=idqrcode,
            archivo_pdf=archivo_pdf,
            texto_aqc=datos_fijos.texto_aqc,
            texto_remitente=datos_fijos.texto_remitente,
            texto_apeticion=datos_fijos.texto_apeticion,
            texto_atte=datos_fijos.texto_atte,
            texto_sursum=datos_fijos.texto_sursum,
            texto_nombrefirma=datos_fijos.texto_nombrefirma,
            texto_cargo=datos_fijos.texto_cargo,
            texto_msgdigital=datos_fijos.texto_msgdigital,
            texto_ccp=datos_fijos.texto_ccp,
            pseudonimo=pseudonimo,
            grado=grado,
            nombre=solicitud.usuario.nombre.upper(),
            texto_asunto=asunto_formateado,
            texto_consta=texto_consta,
            fecha_emision=fecha_formateada,
        )
        
        # Verificar que el archivo se haya generado
        if not os.path.exists(archivo_pdf):
            raise HTTPException(status_code=500, detail="Error al generar el PDF")

        # Función para eliminar archivos temporales
        def eliminar_archivos_temporales():
            try:
                if os.path.exists(archivo_pdf):
                    os.remove(archivo_pdf)
                if os.path.exists(qr_path):
                    os.remove(qr_path)
            except Exception as e:
                print(f"Error al eliminar archivos temporales: {str(e)}")

        # Agregar tarea en segundo plano para eliminar los archivos
        background_tasks.add_task(eliminar_archivos_temporales)
        
        # Retornar el archivo PDF
        return FileResponse(
            path=archivo_pdf,
            filename=f"Constancia_Solicitud_{solicitud_id}.pdf",
            media_type='application/pdf',
            background=background_tasks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Limpiar archivos si hubo error en la generación
        if 'archivo_pdf' in locals() and os.path.exists(archivo_pdf):
            os.remove(archivo_pdf)
        if 'qr_path' in locals() and os.path.exists(qr_path):
            os.remove(qr_path)
        
        # Limpiar BD si hubo error
        db.rollback()
        
        raise HTTPException(status_code=500, detail=f"Error al generar constancia: {str(e)}")

# Resto de tus endpoints existentes...
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
async def validar_constancia(qr_id: str, db: Session = Depends(get_db)):
    """Validar constancia por ID del QR"""
    
    # Buscar en la base de datos
    constancia = db.query(ConstanciaGenerada).filter(
        ConstanciaGenerada.qr_id == qr_id,
        ConstanciaGenerada.es_valida == True
    ).first()
    
    if constancia:
        return {
            "valida": True,
            "id": qr_id,
            "nombre": constancia.nombre,
            "grado": constancia.grado,
            "texto_asunto": constancia.texto_asunto,
            "texto_consta": constancia.texto_consta,
            "fecha_emision": constancia.fecha_emision,
            "fecha_creacion": constancia.fecha_creacion.strftime("%d/%m/%Y %H:%M:%S"),
            "url_validacion": f"{settings.VALIDATION_BASE_URL}{qr_id}"
        }
    else:
        return {
            "valida": False,
            "id": qr_id,
            "mensaje": "Constancia no encontrada o inválida"
        }

@router.delete("/constancia/{qr_id}")
async def eliminar_constancia(qr_id: str, db: Session = Depends(get_db)):
    """Eliminar constancia y su QR asociado"""
    
    # Buscar constancia en BD
    constancia = db.query(ConstanciaGenerada).filter(
        ConstanciaGenerada.qr_id == qr_id
    ).first()
    
    if not constancia:
        raise HTTPException(status_code=404, detail="Constancia no encontrada")
    
    # Marcar como inválida en lugar de eliminar (mejor práctica)
    constancia.es_valida = False
    db.commit()
    
    # Opcional: eliminar archivos físicos
    qr_path = f"{settings.QR_DIR}/{qr_id}.png"
    if os.path.exists(qr_path):
        os.remove(qr_path)
    
    if os.path.exists(constancia.archivo_pdf):
        os.remove(constancia.archivo_pdf)
    
    return {"mensaje": "Constancia eliminada exitosamente"}


@router.get("/validar/{qr_id}")
async def validar_constancia(qr_id: str, db: Session = Depends(get_db)):
    """Validar constancia por ID del QR - Si existe en la tabla, es válida"""
    
    # Buscar en la base de datos - Si existe el registro, es válida
    constancia = db.query(ConstanciaGenerada).filter(
        ConstanciaGenerada.qr_id == qr_id
    ).first()
    
    if constancia:
        return {
            "valida": True,
            "id": qr_id,
            "nombre": constancia.nombre,
            "grado": constancia.grado,
            "pseudonimo": constancia.pseudonimo,
            "texto_asunto": constancia.texto_asunto,
            "texto_consta": constancia.texto_consta,
            "fecha_emision": constancia.fecha_emision,
            "fecha_creacion": constancia.fecha_creacion.strftime("%d/%m/%Y %H:%M:%S") if constancia.fecha_creacion else "",
            "url_validacion": f"{settings.VALIDATION_BASE_URL}{qr_id}"
        }
    else:
        return {
            "valida": False,
            "id": qr_id,
            "mensaje": "Constancia no encontrada o código inválido"
        }