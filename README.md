# API de Constancias UAS - Facultad de Ingeniería Mochis

API REST desarrollada con FastAPI para generar constancias académicas de la Universidad Autónoma de Sinaloa, Facultad de Ingeniería Mochis.

## Características

- ✅ Generación de constancias individuales
- ✅ Procesamiento masivo desde archivos Excel
- ✅ Generación automática de códigos QR
- ✅ Validación de constancias
- ✅ Descarga de archivos PDF y códigos QR
- ✅ Múltiples categorías de constancias
- ✅ Documentación automática con Swagger

## Instalación

### Requisitos previos

- Python 3.11 o superior
- pip

### Instalación local

1. Clona el repositorio:

```bash
git clone <url-del-repositorio>
cd constancias-api
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Coloca los archivos necesarios en el directorio raíz:

   - `cabecera.png` - Imagen del encabezado
   - `pie.png` - Imagen del pie de página
   - `firma.png` - Imagen de la firma

4. Ejecuta la aplicación:

```bash
python main.py
```

O usando uvicorn directamente:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Uso de la API

### Documentación interactiva

Una vez que la API esté ejecutándose, puedes acceder a la documentación interactiva en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints principales

#### 1. Generar constancia individual

```http
POST /constancia/individual
Content-Type: application/json

{
  "pseudonimo": "la parte interesada",
  "grado": "Ing.",
  "nombre": "Juan Pérez García",
  "area": "Sistemas Computacionales",
  "programa": "Ingeniería en Sistemas Computacionales",
  "semestre": "8vo",
  "ciclo_escolar": "2024-2025",
  "fecha_emision": "15 de julio de 2025",
  "idcategoria": "1.2.2.4",
  "asignatura": "Programación Web",
  "email": "juan.perez@uas.edu.mx"
}
```

#### 2. Generar constancias masivamente

```http
POST /constancia/masivo
Content-Type: multipart/form-data

file: [archivo Excel con las constancias]
```

#### 3. Obtener categorías disponibles

```http
GET /categorias
```

#### 4. Validar constancia

```http
GET /validar/{qr_id}
```

#### 5. Descargar constancia

```http
GET /constancia/download/{filename}
```

#### 6. Descargar código QR

```http
GET /qr/{qr_id}
```

#### 7. Eliminar constancia

```http
DELETE /constancia/{qr_id}
```

## Formato del archivo Excel

Para el procesamiento masivo, el archivo Excel debe contener las siguientes columnas:

| Columna      | Descripción            | Obligatorio |
| ------------ | ---------------------- | ----------- |
| Pseudonimo   | Pseudónimo del docente | ✅          |
| Grado        | Grado académico        | ✅          |
| Nombre       | Nombre completo        | ✅          |
| Area         | Área académica         | ✅          |
| Programa     | Programa académico     | ✅          |
| Semestre     | Semestre               | ✅          |
| CicloEscolar | Ciclo escolar          | ✅          |
| FechaEmision | Fecha de emisión       | ✅          |
| idCategoria  | ID de categoría        | ✅          |
| Asignatura   | Asignatura             | ✅          |
| email        | Email del docente      | ✅          |
| Curso        | Nombre del curso       | ❌          |
| Instructor   | Instructor del curso   | ❌          |
| Periodo      | Período del curso      | ❌          |

## Categorías de constancias

| Código    | Descripción                                                                      |
| --------- | -------------------------------------------------------------------------------- |
| 1.1.1.2.1 | Curso de actualización disciplinar con evaluación                                |
| 1.1.1.2.2 | Curso de formación docente con evaluación                                        |
| 1.2.2.4   | Publicación de antologías                                                        |
| 1.2.2.5   | Elaboración de apuntes                                                           |
| 1.2.2.8   | Elaboración de manual de prácticas                                               |
| 1.2.3.3   | Programas de unidad de aprendizaje                                               |
| 1.2.4.2   | Diseño e impartición de programa de cursos en modalidades no escolarizada y dual |
| 1.2.4.3   | Material pedagógico innovador con nuevas tecnologías                             |
| 1.4.1.10  | Cursos de regularización                                                         |
| 1.5.1.3   | Organización de eventos académicos                                               |
| 1.5.1.8   | Elaboración de exámenes departamentales                                          |
| 1.5.1.19  | Coordinación de academia                                                         |

## Estructura de directorios

```
constancias-api/
├── main.py                 # Código principal de la API
├── requirements.txt        # Dependencias de Python
├── Dockerfile             # Configuración de Docker
├── docker-compose.yml     # Configuración de Docker Compose
├── example_usage.py       # Ejemplos de uso
├── README.md              # Este archivo
├── cabecera.png           # Imagen del encabezado
├── pie.png                # Imagen del pie de página
├── firma.png              # Imagen de la firma
├── qrs/                   # Directorio para códigos QR generados
├── constancias/           # Directorio para PDFs generados
└── uploads/               # Directorio para archivos temporales
```

## Ejemplo de uso con Python

```python
import requests

# Generar constancia individual
data = {
    "pseudonimo": "la parte interesada",
    "grado": "Dr.",
    "nombre": "María López García",
    "area": "Ciencias Computacionales",
    "programa": "Ingeniería en Sistemas",
    "semestre": "7mo",
    "ciclo_escolar": "2024-2025",
    "fecha_emision": "15 de julio de 2025",
    "idcategoria": "1.2.2.4",
    "asignatura": "Inteligencia Artificial",
    "email": "maria.lopez@uas.edu.mx"
}

response = requests.post("http://localhost:8000/constancia/individual", json=data)
print(response.json())
```

## Consideraciones de seguridad

- Asegúrate de configurar correctamente las variables de entorno
- En producción, usa HTTPS
- Considera implementar autenticación y autorización
- Valida y sanitiza todas las entradas de usuario
- Limita el tamaño de los archivos de carga

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Contacto

Para soporte técnico o consultas:

- Email: soporte@fim.uas.edu.mx
- Facultad de Ingeniería Mochis - Universidad Autónoma de Sinaloa
