"""
Estilos visuales y tema para el Dashboard Analítico.
Diseño académico minimalista, con paleta sobria de tonos claros y sin elementos distractores.
"""

CUSTOM_CSS = """
<style>
    /* Tipografía y espaciado general */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
    }

    /* Fondo principal */
    .stApp {
        background-color: #f8fafc;
    }

    /* Ocultar elementos decorativos por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Encabezado principal */
    .main-header {
        background-color: #ffffff;
        padding: 24px 32px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
    }

    .main-header h1 {
        color: #0f172a;
        font-size: 26px;
        font-weight: 700;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }

    .main-header p {
        color: #64748b;
        font-size: 14px;
        margin: 0;
    }

    /* Tarjetas de métricas (KPI Cards) */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 18px 20px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    .metric-card .title {
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }

    .metric-card .value {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }

    .metric-card .subtitle {
        font-size: 12px;
        color: #475569;
    }

    /* Contenedor de sección */
    .content-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 20px;
    }

    .content-box h3 {
        font-size: 18px;
        font-weight: 600;
        color: #0f172a;
        margin-top: 0;
        margin-bottom: 12px;
    }

    /* Tablas estilizadas */
    .dataframe {
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #e2e8f0;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 6px 6px 0 0;
        color: #64748b;
        font-weight: 500;
        font-size: 14px;
        background-color: transparent;
    }

    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #1e3a8a !important;
        background-color: #ffffff !important;
    }

    /* Badges de estado */
    .status-badge-ok {
        display: inline-block;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        color: #065f46;
        background-color: #d1fae5;
        border-radius: 4px;
    }

    .status-badge-off {
        display: inline-block;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        color: #991b1b;
        background-color: #fee2e2;
        border-radius: 4px;
    }
</style>
"""
