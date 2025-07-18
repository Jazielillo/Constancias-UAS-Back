from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import pandas as pd
import os
import uuid
from datetime import datetime
import tempfile
import shutil

# Importar las funciones del código original
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
import qrcode
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear directorios necesarios
os.makedirs("qrs", exist_ok=True)
os.makedirs("constancias", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="API de Constancias UAS",
    description="API para generar constancias académicas de la Universidad Autónoma de Sinaloa",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
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

# Funciones del código original
def generar_qrcode(idqrcode: str) -> str:
    """Generar código QR para la constancia"""
    datos = f"https://fim.uas.edu.mx/constancias/validacion.php?code={idqrcode}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(datos)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    nombre_archivo_qr = f"qrs/{idqrcode}.png"
    img.save(nombre_archivo_qr)
    return nombre_archivo_qr

def encabezado_pie(canvas, doc):
    """Función para añadir encabezado y pie de página"""
    ruta_encabezado = "./assets/cabecera.png"
    ruta_pie = "./assets/pie.png"
    
    # Verificar si las imágenes existen
    if not os.path.exists(ruta_encabezado) or not os.path.exists(ruta_pie):
        return
    
    ancho_pagina, alto_pagina = letter
    
    # Encabezado
    try:
        imagen_encabezado = Image(ruta_encabezado, width=ancho_pagina-60, height=80)
        imagen_encabezado.wrapOn(canvas, ancho_pagina, alto_pagina)
        imagen_encabezado.drawOn(canvas, 30, alto_pagina - 100)
    except:
        pass
    
    # Pie de página
    try:
        imagen_pie = Image(ruta_pie, width=ancho_pagina-60, height=30)
        imagen_pie.wrapOn(canvas, ancho_pagina, alto_pagina)
        imagen_pie.drawOn(canvas, 30, 15)
    except:
        pass

def generar_constancia(idqrcode: str, pseudonimo: str, grado: str, nombre: str, area: str, 
                      programa: str, semestre: str, ciclo_escolar: str, fecha_emision: str, 
                      archivo_pdf: str, idcategoria: str, asignatura: str, email: str,
                      curso: Optional[str] = None, instructor: Optional[str] = None, 
                      periodo: Optional[str] = None) -> str:
    """Generar PDF de constancia"""
    
    doc = BaseDocTemplate(archivo_pdf, pagesize=letter, topMargin=130)
    ruta_qrcode = f"qrs/{idqrcode}.png"
    
    # Verificar si existe el QR code
    if os.path.exists(ruta_qrcode):
        imagen_qrcode = Image(ruta_qrcode)
        imagen_qrcode._restrictSize(0.7 * 72, 0.7 * 72)
    else:
        imagen_qrcode = None
    
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='test', frames=frame, onPage=encabezado_pie)
    doc.addPageTemplates([template])
    
    story = []
    estilos = getSampleStyleSheet()
    
    # Definir estilos
    estilo_justificado = estilos["Normal"]
    estilo_justificado.alignment = TA_JUSTIFY
    estilo_justificado.fontName = 'Helvetica'
    estilo_justificado.fontSize = 12
    
    estiloNegrita = ParagraphStyle(
        'EstiloNegrita',
        fontName='Helvetica-Bold',
        fontSize=12,
        alignment=TA_LEFT,
    )
    
    estiloDerecha = ParagraphStyle(
        'EstiloDerecha',
        fontName='Helvetica',
        fontSize=12,
        alignment=TA_RIGHT,
    )
    
    estiloNegritaCentrado = ParagraphStyle(
        'EstiloNegritaCentrado',
        fontName='Helvetica-Bold',
        fontSize=12,
        alignment=TA_CENTER,
    )
    
    estiloCentrado = ParagraphStyle(
        'EstiloCentrado',
        fontName='Helvetica',
        fontSize=10,
        alignment=TA_CENTER,
    )
    
    # Imagen de firma
    ruta_firma = "./assets/firma.png"
    if os.path.exists(ruta_firma):
        firma = Image(ruta_firma)
        ancho_pagina, alto_pagina = letter
        ancho_imagen, alto_imagen = firma.imageWidth, firma.imageHeight
        proporcion = ancho_imagen / alto_imagen
        ancho_imagen_deseado = 1.5 * inch
        alto_imagen_deseado = ancho_imagen_deseado / proporcion
        
        firma.drawHeight = alto_imagen_deseado
        firma.drawWidth = ancho_imagen_deseado
        firma.hAlign = 'CENTER'
    else:
        firma = None
    
    # Textos de la constancia
    texto_aqc = "COMISIÓN DE EVALUACIÓN DEL PROGRAMA DE ESTÍMULOS<br />AL DESEMPEÑO DEL PERSONAL DOCENTE 2025-2026<br />UNIVERSIDAD AUTÓNOMA DE SINALOA"
    texto_remitente = f"El suscrito C. Dr. Rody Abraham Soto Rojo, Director de la Facultad de Ingeniería Mochis, dependiente de la Universidad Autónoma de Sinaloa, hace constar que {pseudonimo} "
    texto_persona = f"{grado} {nombre}"
    
    # Lógica para diferentes tipos de constancias
    match idcategoria:
        case '1.1.1.2.1':
            texto_asunto = "ASUNTO: \nConstancia de curso de actualización<br/>disciplinar con evaluación"
            texto_consta = f"Participó y acreditó el curso de actualización disciplinar <b>{curso}</b> de acuerdo con los criterios para la formulación y aprobación de planes y programas de estudio; impartido por {instructor}, {periodo}, con una duración de 30 horas."
        case '1.1.1.2.2':
            texto_asunto = "ASUNTO: \nConstancia de curso de formación<br/>docente con evaluación"
            texto_consta = f"Participó y acreditó el curso de formación docente <b>{curso}</b> de acuerdo con los criterios para la formulación y aprobación de planes y programas de estudio; impartido por {instructor}, {periodo}, con una duración de 30 horas."
        case '1.2.2.4':
            texto_asunto = "ASUNTO: \nConstancia de publicación de antologías"
            texto_consta = f"Diseñó y elaboró antología para facilitar el aprendizaje de la asignatura <b>{asignatura}</b> del programa de <b>{programa}</b> que se impartió en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.2.2.5':
            texto_asunto = "ASUNTO: \nConstancia de elaboración de apuntes"
            texto_consta = f"Diseñó y elaboró apuntes para facilitar el aprendizaje de la asignatura <b>{asignatura}</b> del programa de <b>{programa}</b> que se impartió en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.2.2.8':
            texto_asunto = "ASUNTO: \nConstancia de elaboración de<br/>manual de prácticas"
            texto_consta = f"Diseñó y elaboró el manual de prácticas de laboratorio para facilitar el aprendizaje de la asignatura <b>{asignatura}</b> del programa de <b>{programa}</b> que se impartió en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.2.3.3':
            texto_asunto = "ASUNTO: \nConstancia de programas de<br/>unidad de aprendizaje"
            texto_consta = f"Participó de manera oportuna en la elaboración y actualización de programas de unidad de aprendizaje de los programas de estudio de la asignatura <b>{asignatura}</b> del programa de <b>{programa}</b> que se impartió en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.2.4.2':
            texto_asunto = "ASUNTO: \nConstancia diseño e impartición de programa<br/>de cursos en modalidades no escolarizada y dual"
            texto_consta = f"Diseñó e impartió el curso <b>{curso}</b> en modalidad no escolarizada, con lineamientos de diseño institucional, el cual se impartió en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.2.4.3':
            texto_asunto = "ASUNTO: \nConstancia Material pedagógico<br/>innovador con nuevas tecnologías"
            texto_consta = f"Diseñó y elaboró material pedagógico innovador utilizando las nuevas tecnologías de la asignatura <b>{asignatura}</b> del programa de <b>{programa}</b> que se impartió en el <b>{semestre}</b> semestre del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.4.1.10':
            texto_asunto = "ASUNTO: \nConstancia de cursos de regularización"
            texto_consta = f"Participó de manera oportuna en la impartición de cursos de regularización académica para exámenes extraordinarios dirigidos a estudiantes no remunerado en la asignatura <b>{asignatura}</b> del programa de <b>{programa}</b> que se impartió en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.5.1.3':
            texto_asunto = "ASUNTO: \nConstancia de organización de eventos académicos"
            texto_consta = f"Participó colegiadamente en el diseño y elaboración de exámenes departamentales del área de <b>{area}</b> del programa de <b>{programa}</b>, en asignaturas del semestre <b>{semestre}</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.5.1.8':
            texto_asunto = "ASUNTO: \nConstancia de elaboración de<br/>exámenes departamentales"
            texto_consta = f"Participó colegiadamente en el diseño y elaboración de exámenes departamentales del área de <b>{area}</b> del programa de <b>{programa}</b>, en asignaturas del <b>semestre {semestre}</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case '1.5.1.19':
            texto_asunto = "ASUNTO: \nCoordinación de academia<br/>"
            texto_consta = f"Fungió como Coordinador de Academia en el área <b>{area}</b> del programa de <b>{programa}</b> en el <b>{semestre} semestre</b> del ciclo escolar <b>{ciclo_escolar}</b>, según consta en los archivos de esta Unidad Académica."
        case _:
            texto_asunto = "ASUNTO: \nInformación incorrecta."
            texto_consta = f"Información incorrecta"
    
    texto_apeticion = f"A petición de la parte interesada se extiende la presente, para los fines que juzgue convenientes, a los {fecha_emision}, en la ciudad de Los Mochis, Sinaloa."
    texto_atte = "A T E N T A M E N T E"
    texto_sursum = "\"SURSUM VERSUS\""
    texto_nombrefirma = f"DR. RODY ABRAHAM SOTO ROJO"
    texto_cargo = "DIRECTOR"
    texto_msgdigital = "Firmado digitalmente"
    texto_ccp = "C.c.p. archivo."
    
    # Construir el documento
    story.append(Paragraph(texto_asunto, estiloDerecha))
    story.append(Spacer(1, 25))
    story.append(Paragraph(texto_aqc, estiloNegrita))
    story.append(Spacer(1, 25))
    story.append(Paragraph(texto_remitente, estilo_justificado))
    story.append(Spacer(1, 25))
    story.append(Paragraph(texto_persona, estiloNegritaCentrado))
    story.append(Spacer(1, 25))
    story.append(Paragraph(texto_consta, estilo_justificado))
    story.append(Spacer(1, 25))
    story.append(Paragraph(texto_apeticion, estilo_justificado))
    story.append(Spacer(1, 40))
    story.append(Paragraph(texto_atte, estiloNegritaCentrado))
    story.append(Paragraph(texto_sursum, estiloNegritaCentrado))
    story.append(Spacer(1, 5))
    
    if firma:
        story.append(firma)
    
    story.append(Spacer(1, -15))
    story.append(Paragraph(texto_nombrefirma, estiloNegritaCentrado))
    story.append(Paragraph(texto_cargo, estiloNegritaCentrado))
    story.append(Spacer(1, 20))
    
    if imagen_qrcode:
        story.append(imagen_qrcode)
    
    story.append(Paragraph(texto_msgdigital, estiloCentrado))
    story.append(Spacer(1, 14))
    story.append(Paragraph(texto_ccp, estilo_justificado))
    
    doc.build(story)
    return archivo_pdf

# Endpoints de la API

@app.get("/")
async def root():
    return {"message": "API de Constancias UAS - Facultad de Ingeniería Mochis"}

@app.post("/constancia/individual", response_model=ConstanciaResponse)
async def generar_constancia_individual(constancia: ConstanciaIndividual):
    """Generar una constancia individual"""
    try:
        # Generar ID único para la constancia
        idqrcode = str(uuid.uuid4())
        
        # Generar QR code
        generar_qrcode(idqrcode)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_pdf = f"constancias/Constancia_{constancia.nombre}_{timestamp}.pdf"
        
        # Generar constancia
        generar_constancia(
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
            qr_code=f"qrs/{idqrcode}.png",
            url_validacion=f"https://fim.uas.edu.mx/constancias/validacion.php?code={idqrcode}",
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar constancia: {str(e)}")


@app.get("/constancia/download/{filename}")
async def descargar_constancia(filename: str):
    """Descargar archivo de constancia"""
    file_path = f"constancias/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )

@app.get("/qr/{qr_id}")
async def obtener_qr(qr_id: str):
    """Obtener código QR"""
    qr_path = f"qrs/{qr_id}.png"
    
    if not os.path.exists(qr_path):
        raise HTTPException(status_code=404, detail="QR no encontrado")
    
    return FileResponse(
        path=qr_path,
        filename=f"{qr_id}.png",
        media_type='image/png'
    )



@app.get("/categorias")
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



@app.get("/validar/{qr_id}")
async def validar_constancia(qr_id: str):
    """Validar constancia por ID del QR"""
    qr_path = f"qrs/{qr_id}.png"
    
    if os.path.exists(qr_path):
        return {
            "valida": True,
            "id": qr_id,
            "url_validacion": f"https://fim.uas.edu.mx/constancias/validacion.php?code={qr_id}"
        }
    else:
        return {
            "valida": False,
            "id": qr_id,
            "mensaje": "Constancia no encontrada"
        }



@app.delete("/constancia/{qr_id}")
async def eliminar_constancia(qr_id: str):
    """Eliminar constancia y su QR asociado"""
    qr_path = f"qrs/{qr_id}.png"
    constancia_encontrada = False
    
    # Buscar y eliminar PDF
    for filename in os.listdir("constancias"):
        if qr_id in filename:
            os.remove(f"constancias/{filename}")
            constancia_encontrada = True
    
    # Eliminar QR
    if os.path.exists(qr_path):
        os.remove(qr_path)
        constancia_encontrada = True
    
    if constancia_encontrada:
        return {"mensaje": "Constancia eliminada exitosamente"}
    else:
        raise HTTPException(status_code=404, detail="Constancia no encontrada")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)