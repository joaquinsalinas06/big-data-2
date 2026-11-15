"""
Vista de Exploración Documental en MongoDB.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from dashboard.services import get_mongodb_listens


def render_mongodb_view():
    st.markdown("### Almacenamiento Documental: MongoDB")
    st.caption("Colección 'listens' en base de datos 'listenbrainz_db'")

    col_search, col_limit = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("Buscar por artista, canción o usuario:", placeholder="Ej: Radiohead, Astrid, FE!N")
    with col_limit:
        limit = st.selectbox("Límite de registros:", [10, 25, 50], index=0)

    records = get_mongodb_listens(query_text=search_query, limit=limit)

    if not records:
        st.info("No se encontraron registros que coincidan con el criterio de búsqueda.")
        return

    # Preparar tabla formateada
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

    # Inspección del documento crudo JSON
    st.markdown("#### Inspección de Documento JSON Semiestructurado")
    selected_idx = st.selectbox("Seleccione un registro para inspeccionar su estructura cruda:", range(len(records)), format_func=lambda i: f"{table_data[i]['Artista']} - {table_data[i]['Canción']} ({table_data[i]['Usuario']})")
    
    st.json(records[selected_idx])

    # Ficha técnica de MongoDB
    with st.expander("Detalles Técnicos del Modelo en MongoDB"):
        st.markdown("""
        * **Naturaleza del dato:** Documental semiestructurado en formato BSON/JSON.
        * **Índices Compuestos Creados:**
          * `[("timestamp", -1), ("_id", -1)]`: Paginación eficiente de feeds cronológicos.
          * `[("user_name", 1), ("timestamp", -1), ("_id", -1)]`: Historial de usuario por fecha.
          * `[("track_metadata.artist_name", 1), ("timestamp", -1), ("_id", -1)]`: Agrupación por artista.
        * **Operaciones CRUD:** Soportadas de forma nativa vía PyMongo y expuestas adicionalmente mediante FastAPI en `databases/mongodb/app`.
        """)
