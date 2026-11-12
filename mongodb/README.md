# Módulo MongoDB — Music DNA (ListenBrainz)

Este módulo gestiona el almacenamiento de los documentos originales de ListenBrainz en formato semiestructurado (JSON) utilizando **MongoDB**.

Cumple con los requisitos del Proyecto Grupal II:
- Almacenamiento no estructurado / semiestructurado.
- Operaciones CRUD directas en Python (Crear, Consultar, Actualizar, Eliminar).
- Script de carga por lotes para ingesta masiva (usado en el pipeline de Airflow).
- Consultas analíticas y agregaciones avanzadas.
- Opcionalmente: API REST desarrollada con FastAPI y Pydantic con documentación interactiva Swagger.

---

## 1. Despliegue de la Base de Datos

Puedes iniciar MongoDB con Docker Compose de manera aislada:

```bash
docker compose -f mongodb/docker-compose.yml up -d
```

O utilizando el Compose general en la raíz del repositorio:

```bash
docker compose up -d mongodb
```

La base de datos quedará accesible en `mongodb://localhost:27017/` (base `listenbrainz_db`, colección `listens`).

---

## 2. Operaciones CRUD (Para Exposición y Video)

Se cuenta con un script interactivo en consola para demostrar las 4 operaciones básicas exigidas en la rúbrica sin requerir dependencias HTTP:

```bash
# Ejecutar demo completa
python -m mongodb.crud

# Ejecutar con pausa interactiva [Enter] para el video demostrativo:
python -m mongodb.crud --pause
```

El script ejecuta y valida:
1. **CREATE:** Inserción de un nuevo documento JSON con metadatos de canción, artista y timestamp.
2. **READ:** Consulta por ID único (`_id`) y consulta por usuario.
3. **UPDATE:** Actualización atómica de campos (`$set`) como título o álbum.
4. **DELETE:** Eliminación del documento y comprobación de ausencia.

---

## 3. Carga Masiva de Datos

Para cargar datos desde el dump oficial procesado (`data/processed/listens_full.jsonl`):

```bash
# Cargar 50,000 registros (mínimo de la rúbrica)
python -m mongodb.load_listens --limit 50000

# Cargar con tamaño de lote personalizado
python -m mongodb.load_listens --limit 100000 --batch-size 2500
```

Esta función también puede ser invocada programáticamente desde el DAG de Airflow:
```python
from mongodb.load_listens import load_to_mongodb

load_to_mongodb("data/processed/listens_full.jsonl", limit=50000)
```

---

## 4. Consultas y Agregaciones

Para ejecutar agregaciones analíticas (top artistas, top tracks, promedio de duración, escuchas por día):

```bash
python -m mongodb.queries
```

---

## 5. API REST con FastAPI (Opcional)

Si deseas utilizar la API REST desarrollada con FastAPI:

```bash
python -m mongodb.api_server
```

Abre en tu navegador [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para probar los endpoints interactivos mediante Swagger UI.

Para probar el CRUD vía HTTP:
```bash
python -m mongodb.demo_api_crud
```

---

## 6. Pruebas Unitarias

Para ejecutar la suite de pruebas automatizadas:

```bash
pytest mongodb/tests
```
