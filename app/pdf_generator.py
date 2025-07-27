# pdf_generator.py
import os
import uuid
import qrcode
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
from config.config import settings

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configurar estilos personalizados"""
        self.estilo_justificado = self.styles["Normal"]
        self.estilo_justificado.alignment = TA_JUSTIFY
        self.estilo_justificado.fontName = 'Helvetica'
        self.estilo_justificado.fontSize = 12
        
        self.estiloNegrita = ParagraphStyle(
            'EstiloNegrita',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_LEFT,
        )
        
        self.estiloDerecha = ParagraphStyle(
            'EstiloDerecha',
            fontName='Helvetica',
            fontSize=12,
            alignment=TA_RIGHT,
        )
        
        self.estiloNegritaCentrado = ParagraphStyle(
            'EstiloNegritaCentrado',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER,
        )
        
        self.estiloCentrado = ParagraphStyle(
            'EstiloCentrado',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
        )
    
    def generar_qrcode(self, idqrcode: str) -> str:
        """Generar código QR para la constancia"""
        datos = f"{settings.VALIDATION_BASE_URL}{idqrcode}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(datos)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        nombre_archivo_qr = f"{settings.QR_DIR}/{idqrcode}.png"
        img.save(nombre_archivo_qr)
        return nombre_archivo_qr
    
    def _encabezado_pie(self, canvas, doc):
        """Función para añadir encabezado y pie de página"""
        # Verificar si las imágenes existen
        if not os.path.exists(settings.HEADER_IMAGE) or not os.path.exists(settings.FOOTER_IMAGE):
            return
        
        ancho_pagina, alto_pagina = letter
        
        # Encabezado
        try:
            imagen_encabezado = Image(settings.HEADER_IMAGE, width=ancho_pagina-60, height=80)
            imagen_encabezado.wrapOn(canvas, ancho_pagina, alto_pagina)
            imagen_encabezado.drawOn(canvas, 30, alto_pagina - 100)
        except:
            pass
        
        # Pie de página
        try:
            imagen_pie = Image(settings.FOOTER_IMAGE, width=ancho_pagina-60, height=30)
            imagen_pie.wrapOn(canvas, ancho_pagina, alto_pagina)
            imagen_pie.drawOn(canvas, 30, 15)
        except:
            pass
    
    def _get_constancia_content(self, idcategoria: str, **kwargs) -> tuple[str, str]:
        """Obtener contenido específico según la categoría"""
        content_map = {
            '1.1.1.2.1': (
                "ASUNTO: \nConstancia de curso de actualización<br/>disciplinar con evaluación",
                f"Participó y acreditó el curso de actualización disciplinar <b>{kwargs.get('curso', '')}</b> de acuerdo con los criterios para la formulación y aprobación de planes y programas de estudio; impartido por {kwargs.get('instructor', '')}, {kwargs.get('periodo', '')}, con una duración de 30 horas."
            ),
            '1.1.1.2.2': (
                "ASUNTO: \nConstancia de curso de formación<br/>docente con evaluación",
                f"Participó y acreditó el curso de formación docente <b>{kwargs.get('curso', '')}</b> de acuerdo con los criterios para la formulación y aprobación de planes y programas de estudio; impartido por {kwargs.get('instructor', '')}, {kwargs.get('periodo', '')}, con una duración de 30 horas."
            ),
            '1.2.2.4': (
                "ASUNTO: \nConstancia de publicación de antologías",
                f"Diseñó y elaboró antología para facilitar el aprendizaje de la asignatura <b>{kwargs.get('asignatura', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> que se impartió en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.2.2.5': (
                "ASUNTO: \nConstancia de elaboración de apuntes",
                f"Diseñó y elaboró apuntes para facilitar el aprendizaje de la asignatura <b>{kwargs.get('asignatura', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> que se impartió en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.2.2.8': (
                "ASUNTO: \nConstancia de elaboración de<br/>manual de prácticas",
                f"Diseñó y elaboró el manual de prácticas de laboratorio para facilitar el aprendizaje de la asignatura <b>{kwargs.get('asignatura', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> que se impartió en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.2.3.3': (
                "ASUNTO: \nConstancia de programas de<br/>unidad de aprendizaje",
                f"Participó de manera oportuna en la elaboración y actualización de programas de unidad de aprendizaje de los programas de estudio de la asignatura <b>{kwargs.get('asignatura', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> que se impartió en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.2.4.2': (
                "ASUNTO: \nConstancia diseño e impartición de programa<br/>de cursos en modalidades no escolarizada y dual",
                f"Diseñó e impartió el curso <b>{kwargs.get('curso', '')}</b> en modalidad no escolarizada, con lineamientos de diseño institucional, el cual se impartió en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.2.4.3': (
                "ASUNTO: \nConstancia Material pedagógico<br/>innovador con nuevas tecnologías",
                f"Diseñó y elaboró material pedagógico innovador utilizando las nuevas tecnologías de la asignatura <b>{kwargs.get('asignatura', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> que se impartió en el <b>{kwargs.get('semestre', '')}</b> semestre del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.4.1.10': (
                "ASUNTO: \nConstancia de cursos de regularización",
                f"Participó de manera oportuna en la impartición de cursos de regularización académica para exámenes extraordinarios dirigidos a estudiantes no remunerado en la asignatura <b>{kwargs.get('asignatura', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> que se impartió en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.5.1.3': (
                "ASUNTO: \nConstancia de organización de eventos académicos",
                f"Participó colegiadamente en el diseño y elaboración de exámenes departamentales del área de <b>{kwargs.get('area', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b>, en asignaturas del semestre <b>{kwargs.get('semestre', '')}</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.5.1.8': (
                "ASUNTO: \nConstancia de elaboración de<br/>exámenes departamentales",
                f"Participó colegiadamente en el diseño y elaboración de exámenes departamentales del área de <b>{kwargs.get('area', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b>, en asignaturas del <b>semestre {kwargs.get('semestre', '')}</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            ),
            '1.5.1.19': (
                "ASUNTO: \nCoordinación de academia<br/>",
                f"Fungió como Coordinador de Academia en el área <b>{kwargs.get('area', '')}</b> del programa de <b>{kwargs.get('programa', '')}</b> en el <b>{kwargs.get('semestre', '')} semestre</b> del ciclo escolar <b>{kwargs.get('ciclo_escolar', '')}</b>, según consta en los archivos de esta Unidad Académica."
            )
        }
        
        return content_map.get(idcategoria, (
            "ASUNTO: \nInformación incorrecta.",
            "Información incorrecta"
        ))
    
    def generar_constancia(self, idqrcode: str, pseudonimo: str, grado: str, nombre: str, 
                          area: str, programa: str, semestre: str, ciclo_escolar: str, 
                          fecha_emision: str, archivo_pdf: str, idcategoria: str, 
                          asignatura: str, email: str, curso: Optional[str] = None, 
                          instructor: Optional[str] = None, periodo: Optional[str] = None) -> str:
        """Generar PDF de constancia"""
        
        doc = BaseDocTemplate(archivo_pdf, pagesize=letter, topMargin=130)
        ruta_qrcode = f"{settings.QR_DIR}/{idqrcode}.png"
        
        # Verificar si existe el QR code
        if os.path.exists(ruta_qrcode):
            imagen_qrcode = Image(ruta_qrcode)
            imagen_qrcode._restrictSize(0.7 * 72, 0.7 * 72)
        else:
            imagen_qrcode = None
        
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='test', frames=frame, onPage=self._encabezado_pie)
        doc.addPageTemplates([template])
        
        story = []
        
        # Imagen de firma
        if os.path.exists(settings.SIGNATURE_IMAGE):
            firma = Image(settings.SIGNATURE_IMAGE)
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
        
        # Obtener contenido específico de la categoría
        texto_asunto, texto_consta = self._get_constancia_content(
            idcategoria, 
            curso=curso, 
            instructor=instructor, 
            periodo=periodo,
            asignatura=asignatura,
            programa=programa,
            semestre=semestre,
            ciclo_escolar=ciclo_escolar,
            area=area
        )
        
        # Textos estáticos
        texto_remitente = f"{settings.REMITENTE_TEXT} {pseudonimo} "
        texto_persona = f"{grado} {nombre}"
        texto_apeticion = f"A petición de la parte interesada se extiende la presente, para los fines que juzgue convenientes, a los {fecha_emision}, en la ciudad de Los Mochis, Sinaloa."
        
        # Construir el documento
        story.append(Paragraph(texto_asunto, self.estiloDerecha))
        story.append(Spacer(1, 25))
        story.append(Paragraph(settings.COMMISSION_TEXT, self.estiloNegrita))
        story.append(Spacer(1, 25))
        story.append(Paragraph(texto_remitente, self.estilo_justificado))
        story.append(Spacer(1, 25))
        story.append(Paragraph(texto_persona, self.estiloNegritaCentrado))
        story.append(Spacer(1, 25))
        story.append(Paragraph(texto_consta, self.estilo_justificado))
        story.append(Spacer(1, 25))
        story.append(Paragraph(texto_apeticion, self.estilo_justificado))
        story.append(Spacer(1, 40))
        story.append(Paragraph("A T E N T A M E N T E", self.estiloNegritaCentrado))
        story.append(Paragraph("\"SURSUM VERSUS\"", self.estiloNegritaCentrado))
        story.append(Spacer(1, 5))
        
        if firma:
            story.append(firma)
        
        story.append(Spacer(1, -15))
        story.append(Paragraph(settings.DIRECTOR_NAME, self.estiloNegritaCentrado))
        story.append(Paragraph(settings.DIRECTOR_TITLE, self.estiloNegritaCentrado))
        story.append(Spacer(1, 20))
        
        if imagen_qrcode:
            story.append(imagen_qrcode)
        
        story.append(Paragraph("Firmado digitalmente", self.estiloCentrado))
        story.append(Spacer(1, 14))
        story.append(Paragraph("C.c.p. archivo.", self.estilo_justificado))
        
        doc.build(story)
        return archivo_pdf