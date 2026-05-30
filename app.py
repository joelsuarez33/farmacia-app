import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Guía Farmacia",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS mobile-first ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding: 1rem 1rem 2rem; max-width: 480px; }
    h1 { font-size: 1.3rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 1rem !important; }
    .stButton > button {
        width: 100%; border-radius: 12px;
        padding: 0.6rem 1rem; font-size: 0.95rem;
    }
    .drug-card {
        border: 0.5px solid #e0e0e0; border-radius: 12px;
        padding: 14px; margin-bottom: 10px;
        background: var(--background-color);
    }
    .badge {
        display: inline-block; border-radius: 20px;
        padding: 2px 10px; font-size: 0.78rem;
        margin: 2px; background: #f0f0f0; color: #333;
    }
    .badge-alert {
        background: #fff0f0; color: #c0392b;
        border: 0.5px solid #f5c6c6;
    }
    .badge-forma {
        background: #f0f4ff; color: #2c5282;
        border: 0.5px solid #c3d4f5;
    }
    .badge-nota {
        background: #fffbe6; color: #7d6608;
        border: 0.5px solid #f5e5a0;
    }
    .warning-box {
        background: #fff8e1; border-left: 4px solid #f59e0b;
        border-radius: 8px; padding: 10px 14px;
        margin-bottom: 14px; font-size: 0.88rem; color: #7d6608;
    }
    .cat-btn {
        border: 0.5px solid #e0e0e0; border-radius: 12px;
        padding: 12px; text-align: left; cursor: pointer;
        background: var(--background-color); margin-bottom: 8px;
    }
    div[data-testid="stExpander"] {
        border: 0.5px solid #e0e0e0 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Constantes ───────────────────────────────────────────────────────────────
SHEET_ID = "1dtmAAWwYBm55a_BtPqBqO_MXEA9cdSK6phZdADOTcy0"
SHEET_NAME = "Hoja1"  # ajustar si el nombre de la pestaña es distinto

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

CATEGORY_ICONS = {
    "analgesicos": "💊", "antiinflamatorios": "💊",
    "antigripales": "🤧", "resfrio": "🤧",
    "tos": "😮‍💨",
    "digestivos": "🫃", "antiacidos": "🫃",
    "alergia": "🌿",
    "antibioticos": "⚠️",
    "vitaminas": "🌟", "suplementos": "🌟",
    "dermocos": "🧴", "cremas": "🧴",
}

CATEGORY_WARNINGS = {
    "antibioticos": "⚠️ Regla general: no dispensar sin receta médica vigente. Explicar siempre completar el tratamiento completo.",
    "antigripales": "⚠️ Muchos antigripales contienen paracetamol. Advertir al paciente para evitar duplicar dosis con otros analgésicos.",
}

REQUIRED_COLS = {"Clasificacion", "Droga", "Definición", "Dosis"}

# ── Conexión a Google Sheets ─────────────────────────────────────────────────
@st.cache_resource
def get_gspread_client():
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=3600)
def load_vademecum() -> pd.DataFrame:
    client = get_gspread_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(SHEET_NAME)
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    # Normalizar nombres de columna (strip espacios)
    df.columns = df.columns.str.strip()

    # Validar columnas requeridas presentes en el sheet
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        st.error(f"Faltan columnas en el Sheet: {missing}")
        st.stop()

    # Filtrar filas con las 4 columnas requeridas completas
    for col in REQUIRED_COLS:
        df = df[df[col].astype(str).str.strip() != ""]

    # Normalizar clasificación: lowercase, strip
    df["Clasificacion"] = df["Clasificacion"].str.strip().str.lower()

    return df.reset_index(drop=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
def get_icon(cat: str) -> str:
    cat_lower = cat.lower()
    for key, icon in CATEGORY_ICONS.items():
        if key in cat_lower:
            return icon
    return "🔹"

def get_warning(cat: str) -> str | None:
    cat_lower = cat.lower()
    for key, msg in CATEGORY_WARNINGS.items():
        if key in cat_lower:
            return msg
    return None

def render_badges(text: str, css_class: str = "badge") -> str:
    if not text or str(text).strip() == "":
        return ""
    items = [i.strip() for i in str(text).split(",") if i.strip()]
    return " ".join(f'<span class="{css_class}">{i}</span>' for i in items)

def render_drug_card(row: pd.Series):
    droga = row.get("Droga", "")
    definicion = row.get("Definición", "")
    dosis = row.get("Dosis", "")
    usos = row.get("Usos", "")
    marcas = row.get("Marcas", "")
    forma = row.get("Forma Farmaceutica", row.get("Forma Farmacéutica", ""))
    notas = row.get("Notas", "")
    alertas = row.get("Alertas", "")

    with st.expander(f"**{droga}** — {definicion}"):
        if dosis:
            st.markdown(f"**Dosis disponibles:** {dosis}")
        if usos:
            st.markdown(f"**Usos:** {usos}")
        if marcas:
            st.markdown("**Marcas comerciales:**")
            st.markdown(render_badges(marcas, "badge"), unsafe_allow_html=True)
        if forma:
            st.markdown("**Forma farmacéutica:**")
            st.markdown(render_badges(forma, "badge badge-forma"), unsafe_allow_html=True)
        if notas:
            st.markdown("**Notas:**")
            st.markdown(render_badges(notas, "badge badge-nota"), unsafe_allow_html=True)
        if alertas:
            st.markdown("**⚠️ Alertas:**")
            st.markdown(
                f'<div style="background:#fff0f0;border-radius:8px;padding:8px 12px;'
                f'font-size:0.88rem;color:#c0392b;margin-top:4px">{alertas}</div>',
                unsafe_allow_html=True
            )

# ── UI principal ─────────────────────────────────────────────────────────────
st.title("💊 Guía de Mostrador")

tab1, tab2 = st.tabs(["Vademécum", "Obras Sociales"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — VADEMÉCUM
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    with st.spinner("Cargando datos..."):
        df = load_vademecum()

    # Buscador
    query = st.text_input("🔍 Buscar droga, marca o indicación...", key="search")

    if query.strip():
        # Búsqueda cross-column
        q = query.strip().lower()
        mask = (
            df["Droga"].str.lower().str.contains(q, na=False) |
            df.get("Marcas", pd.Series(dtype=str)).str.lower().str.contains(q, na=False) |
            df.get("Usos", pd.Series(dtype=str)).str.lower().str.contains(q, na=False) |
            df.get("Definición", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        )
        results = df[mask]
        st.markdown(f"**{len(results)} resultado(s) para '{query}'**")
        if results.empty:
            st.info("Sin resultados. Probá con otro término.")
        else:
            for _, row in results.iterrows():
                render_drug_card(row)

    else:
        # Vista por categoría
        categories = df["Clasificacion"].unique().tolist()

        # Estado de categoría seleccionada
        if "selected_cat" not in st.session_state:
            st.session_state.selected_cat = None

        if st.session_state.selected_cat is None:
            # Grilla de categorías
            cols = st.columns(2)
            for i, cat in enumerate(categories):
                count = len(df[df["Clasificacion"] == cat])
                icon = get_icon(cat)
                with cols[i % 2]:
                    if st.button(
                        f"{icon} {cat.title()}\n{count} producto(s)",
                        key=f"cat_{cat}",
                        use_container_width=True
                    ):
                        st.session_state.selected_cat = cat
                        st.rerun()
        else:
            cat = st.session_state.selected_cat
            icon = get_icon(cat)

            col1, col2 = st.columns([1, 6])
            with col1:
                if st.button("←", key="back"):
                    st.session_state.selected_cat = None
                    st.rerun()
            with col2:
                st.markdown(f"### {icon} {cat.title()}")

            # Warning si aplica
            warn = get_warning(cat)
            if warn:
                st.markdown(
                    f'<div class="warning-box">{warn}</div>',
                    unsafe_allow_html=True
                )

            # Lista de drogas de la categoría
            cat_df = df[df["Clasificacion"] == cat]
            for _, row in cat_df.iterrows():
                render_drug_card(row)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — OBRAS SOCIALES (Fase 1: PDF estático)
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📋 Guía de Obras Sociales")
    st.info(
        "Próximamente: resúmenes por obra social y descarga de procedimientos. "
        "Por ahora podés descargar la guía general."
    )

    import os
    pdf_path = "assets/guia_OS_general.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📥 Descargar guía general de Obras Sociales",
                data=f,
                file_name="guia_OS_general.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    else:
        st.warning("Guía general de OS no disponible aún. Próximamente.")
