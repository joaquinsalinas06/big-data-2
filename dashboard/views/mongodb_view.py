"""
Vista de Almacenamiento Documental y Consultas en MongoDB.
Incluye buscador dinámico, visor de documentos BSON/JSON y consola de operaciones CRUD.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from dashboard.services import get_mongodb_listens, is_port_open, get_mongo_client, get_mongo_collection


def render_mongodb_view():
    st.markdown("### Almacenamiento Documental: MongoDB")
    st.caption("Base de datos: 'listenbrainz_db' | Colección: 'listens' | Esquema semiestructurado BSON")

    subtab_query, subtab_crud = st.tabs(["Consultas y Exploración", "Operaciones CRUD (Demostración)"])

    with subtab_query:
        st.markdown("#### Búsqueda Interactiva de Documentos")
        col_search, col_limit = st.columns([3, 1])
        with col_search:
            search_query = st.text_input(
                "Filtro por artista, canción o usuario:",
                placeholder="Ejemplo: Radiohead, Linkin Park, BTS, Astrid",
                key="mongo_search_input"
            )
        with col_limit:
            limit = st.selectbox("Límite de resultados:", [10, 25, 50], index=0, key="mongo_limit_select")

        # Visualización de la sintaxis PyMongo ejecutada
        if search_query:
            query_code = (
                f'db.listens.find({{\n'
                f'    "$or": [\n'
                f'        {{"track_metadata.artist_name": {{"$regex": "{search_query}", "$options": "i"}}}},\n'
                f'        {{"track_metadata.track_name": {{"$regex": "{search_query}", "$options": "i"}}}},\n'
                f'        {{"user_name": {{"$regex": "{search_query}", "$options": "i"}}}}\n'
                f'    ]\n'
                f'}}).sort([("timestamp", -1)]).limit({limit})'
            )
        else:
            query_code = f'db.listens.find().sort([("timestamp", -1)]).limit({limit})'

        with st.expander("Ver consulta PyMongo equivalente", expanded=False):
            st.code(query_code, language="python")

        if not is_port_open("127.0.0.1", 27017):
            st.error("No se pudo conectar a MongoDB en localhost:27017.")
            st.info("Para explorar documentos en vivo, inicie el contenedor con: `docker compose up -d mongodb`")
        else:
            records = get_mongodb_listens(query_text=search_query, limit=limit)

            if not records:
                st.info("La colección 'listens' en MongoDB está vacía o ningún registro coincide con el criterio. (Para cargar datos ejecute: `python -m databases.mongodb.loader --limit 1000`).")
            else:
                table_data = []
                for r in records:
                    ts = r.get("timestamp", 0)
                    formatted_date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    metadata = r.get("track_metadata", {})
                    table_data.append({
                        "ID Documento": str(r.get("_id"))[:12] + "...",
                        "Usuario": r.get("user_name"),
                        "Fecha UTC": formatted_date,
                        "Artista": metadata.get("artist_name", "Desconocido"),
                        "Canción": metadata.get("track_name", "Desconocido"),
                        "Álbum": metadata.get("release_name") or "Sin especificar",
                    })

                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown("#### Inspección de Documento BSON Crudo")
                selected_idx = st.selectbox(
                    "Seleccione un registro para visualizar su JSON completo:",
                    range(len(records)),
                    format_func=lambda i: f"{table_data[i]['Artista']} — {table_data[i]['Canción']} ({table_data[i]['Usuario']})",
                    key="mongo_json_select"
                )
                st.json(records[selected_idx])

    with subtab_crud:
        st.markdown("#### Demostración de Operaciones CRUD en MongoDB")
        st.markdown("Prueba de las 4 operaciones básicas exigidas en la Sección 4 del enunciado (`databases/mongodb/crud.py`):")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""
            **1. CREATE**
            ```python
            db.listens.insert_one({
                "user_name": "demo_utec",
                "timestamp": 1793289600,
                "track_metadata": {
                    "artist_name": "Radiohead",
                    "track_name": "Creep"
                }
            })
            ```
            """)
        with c2:
            st.markdown("""
            **2. READ**
            ```python
            doc = db.listens.find_one({
                "_id": inserted_id
            })
            ```
            """)
        with c3:
            st.markdown("""
            **3. UPDATE**
            ```python
            db.listens.update_one(
                {"_id": inserted_id},
                {"$set": {
                    "track_metadata.release_name": "Pablo Honey (Remastered)"
                }}
            )
            ```
            """)
        with c4:
            st.markdown("""
            **4. DELETE**
            ```python
            db.listens.delete_one({
                "_id": inserted_id
            })
            ```
            """)

        btn_run_crud = st.button("Ejecutar Flujo CRUD en MongoDB", key="btn_mongo_crud")
        if btn_run_crud:
            if not is_port_open("127.0.0.1", 27017):
                st.error("MongoDB no se encuentra en línea en localhost:27017. Inicie el contenedor con: `docker compose up -d mongodb`")
            else:
                try:
                    import time
                    from databases.mongodb.crud import insert_listen, get_listen, update_listen, delete_listen
                    with get_mongo_client() as client:
                        col = get_mongo_collection(client)
                        now_ts = int(time.time())
                        # 1. Create
                        ins_id = insert_listen(col, "demo_utec_live", now_ts, "Creep", "Radiohead", release_name="Pablo Honey", is_demo=True)
                        st.markdown(f"**1. CREATE:** Documento insertado con `_id: {ins_id}`")
                        # 2. Read
                        doc = get_listen(col, ins_id)
                        meta = doc.get("track_metadata", {})
                        st.markdown(f"**2. READ:** Recuperado documento con artista `{meta.get('artist_name')}` y canción `{meta.get('track_name')}`")
                        # 3. Update
                        update_listen(col, ins_id, {"track_metadata.release_name": "Pablo Honey (Remastered)"})
                        st.markdown("**3. UPDATE:** Campo `release_name` modificado a 'Pablo Honey (Remastered)'")
                        # 4. Delete
                        delete_listen(col, ins_id)
                        st.markdown("**4. DELETE:** Documento eliminado. Verificación: None.")
                        st.success("Flujo CRUD ejecutado exitosamente sobre MongoDB local (localhost:27017).")
                except Exception as e:
                    st.error(f"Error al ejecutar operaciones CRUD en MongoDB: {e}")
