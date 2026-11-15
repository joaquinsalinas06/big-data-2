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

    /* Encabezado principal */
    .main-header {
        background-color: #ffffff;
        padding: 20px 28px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }

    .main-header h1 {
        color: #0f172a !important;
        font-size: 24px;
        font-weight: 700;
        margin: 0 0 6px 0;
    }

    .main-header p {
        color: #475569 !important;
        font-size: 14px;
        margin: 0;
    }

    /* Caja de diagnóstico de motor */
    .motor-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }

    .motor-box .label {
        font-weight: 600;
        font-size: 13px;
        color: #0f172a !important;
        margin-bottom: 4px;
    }

    .motor-box .caption {
        font-size: 11px;
        color: #64748b !important;
        margin-top: 4px;
    }

    /* Tarjetas de métricas (KPI Cards) */
    .metric-card {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 16px 18px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    .metric-card .title {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 6px !important;
    }

    .metric-card .value {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin-bottom: 4px !important;
    }

    .metric-card .subtitle {
        font-size: 11px !important;
        color: #64748b !important;
    }

    /* Contenedor de sección */
    .content-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .content-box h3 {
        font-size: 17px;
        font-weight: 600;
        color: #0f172a !important;
        margin-top: 0;
        margin-bottom: 10px;
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #cbd5e1;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 6px 6px 0 0;
        color: #475569 !important;
        font-weight: 500;
        font-size: 13px;
        background-color: transparent;
    }

    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #1e3a8a !important;
        background-color: #ffffff !important;
    }

    /* Badges de estado */
    .status-badge-ok {
        display: inline-block;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        color: #065f46 !important;
        background-color: #d1fae5 !important;
        border: 1px solid #a7f3d0;
        border-radius: 4px;
    }

    .status-badge-off {
        display: inline-block;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        color: #991b1b !important;
        background-color: #fee2e2 !important;
        border: 1px solid #fecaca;
        border-radius: 4px;
    }

    /* Tablas limpias */
    table {
        color: #0f172a !important;
    }

    th {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    td {
        color: #1e293b !important;
    }
</style>
"""
