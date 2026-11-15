"""
Estilos visuales y tema para el Dashboard Analítico.
Diseño académico minimalista, con paleta sobria de tonos claros, compatible con modo oscuro/claro del navegador.
"""

CUSTOM_CSS = """
<style>
    /* Forzar fondo claro y tipografía legible en todo el dashboard */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* Tipografía y color explícito para todos los textos y encabezados */
    html, body, [class*="css"], [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span, label {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #0f172a !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: #475569 !important;
    }

    /* Ocultar elementos decorativos por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Barra superior compacta */
    .dashboard-header {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        padding: 4px 0 14px 0;
        margin-bottom: 8px;
        border-bottom: 1px solid #e2e8f0;
    }

    .dashboard-header h2 {
        margin: 0;
        font-size: 22px;
        color: #0f172a !important;
        font-weight: 700;
    }

    .dashboard-header .header-sub {
        font-size: 13px;
        color: #64748b;
    }

    /* Tarjetas de estado en sidebar */
    .sidebar-db-status {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 12px;
    }

    .sidebar-db-status .db-name {
        font-weight: 600;
        color: #0f172a;
    }

    .sidebar-db-status .db-detail {
        color: #64748b;
        font-size: 11px;
    }

    /* Tarjetas de métricas (KPI Cards) */
    .metric-card {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 14px 16px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }

    .metric-card .title {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 4px !important;
    }

    .metric-card .value {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin-bottom: 4px !important;
        line-height: 1.2 !important;
    }

    .metric-card .subtitle {
        font-size: 12px !important;
        color: #64748b !important;
    }

    /* Cajas de contenido general */
    .content-box {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
        margin-bottom: 16px !important;
    }

    .content-box h3 {
        margin-top: 0 !important;
        color: #0f172a !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    .content-box p {
        color: #334155 !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        margin-bottom: 6px !important;
    }

    /* Badges de estado */
    .status-badge-ok {
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }

    .status-badge-off {
        background-color: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        display: inline-block;
    }

    /* Pestañas estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 18px;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        padding: 8px 14px;
        background-color: transparent;
        border-radius: 6px 6px 0 0;
    }

    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important;
        border-bottom: 2px solid #1e3a8a !important;
        background-color: #ffffff;
    }

    /* Tablas de Streamlit */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 6px;
    }

    /* Consola de código */
    .stCodeBlock {
        border-radius: 6px;
        border: 1px solid #cbd5e1;
    }
</style>
"""
