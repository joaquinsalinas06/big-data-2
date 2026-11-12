# MongoDB — Modelo Documental y Operaciones CRUD

Guía técnica del almacenamiento de datos semiestructurados (JSON) de ListenBrainz en **MongoDB** (`listenbrainz_db.listens`).

---

## 1. Modelo de Datos e Índices

Cada registro de escucha se almacena en la colección `listens` como un documento JSON con la siguiente estructura:

```json
{
  "_id": "67324f1e...",
  "user_name": "usuario_ejemplo",
  "timestamp": 1793318246,
  "track_metadata": {
    "track_name": "Song title",
    "artist_name": "Artist name",
    "release_name": "Album name",
    "additional_info": {}
  }
}
```

### Índices Compuestos Creados:
Para garantizar consultas óptimas en MongoDB, se configuran los siguientes índices:
1. `[("timestamp", -1), ("_id", -1)]`: Paginación cronológica y feeds de actividad.
2. `[("user_name", 1), ("timestamp", -1), ("_id", -1)]`: Historial de escuchas por usuario.
3. `[("track_metadata.artist_name", 1), ("timestamp", -1), ("_id", -1)]`: Búsqueda y agregación por artista.

---

## 2. Operaciones CRUD en Python (Directas)

Para la sustentación y video, se cuenta con el script interactivo directo:

```bash
python -m databases.mongodb.crud --pause
```

Operaciones implementadas:
* **CREATE (`insert_listen`):** Inserción del documento con metadatos validados.
* **READ (`get_listen` / `get_user_listens`):** Búsqueda por `_id` único o por usuario con orden descendente.
* **UPDATE (`update_listen`):** Actualización atómica con `$set` (modificación de título o álbum).
* **DELETE (`delete_listen`):** Eliminación por `_id` comprobando la confirmación de borrado.

---

## 3. API REST con FastAPI y Swagger (Opcional)

Adicionalmente, se incluye una capa de API REST en [`databases/mongodb/app/`](../databases/mongodb/app/):

```bash
python -m databases.mongodb.tools.api_server
```

Abre en el navegador: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Recorrido de una solicitud en la API:
1. `databases/mongodb/app/routes/listens.py` recibe el método HTTP, la ruta y los parámetros.
2. `databases/mongodb/app/models.py` valida los campos con Pydantic. Si son incorrectos, responde 422 antes de escribir en MongoDB.
3. `databases/mongodb/app/services/listen_service.py` interpreta el identificador, prepara filtros y determina la operación.
4. `databases/mongodb/app/repositories/listen_repository.py` ejecuta la operación PyMongo sobre `listenbrainz_db.listens`.
5. La respuesta validada devuelve el identificador como una cadena JSON.
