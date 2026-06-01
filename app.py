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

tab1, tab2 = st.tabs(["Vademécum", "Manual de dispensa"])

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
# TAB 2 — Manual de dispensa
# ════════════════════════════════════════════════════════════════════════════
 
# ── Datos hardcodeados del manual operativo ──────────────────────────────────
OS_DATA = {
    "🏷️ Tipos de venta": {
        "icono": "🏷️",
        "items": [
            ("B — Particular", "Venta directa al público sin cobertura."),
            ("A — Obra social", "Con cobertura de obra social. Requiere receta y credencial."),
            ("C — PAMI", "Cobertura PAMI. Ver procedimiento específico."),
            ("D — Vale", "Producto reservado, ya pagado. Retirar con número de vale."),
            ("R — Reserva", "Producto apartado para el cliente."),
            ("G — Servicio de salud", "Enfermería, diabetes, oximetría, etc."),
        ]
    },
    "🧪 Laboratorios y colores": {
        "icono": "🧪",
        "items": [
            ("Montpellier", "Verde y blanco. Ej: T4. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#fff;border:1px solid #ccc;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#2ecc71;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Glaxo Smith (GSK)", "Levotiroxinas con muchos colores. Se encuentran en la letra L. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#e74c3c;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#3498db;border-radius:2px;vertical-align:middle;margin-left:2px'></span><span style='display:inline-block;width:12px;height:12px;background:#f1c40f;border-radius:2px;vertical-align:middle;margin-left:2px'></span><span style='display:inline-block;width:12px;height:12px;background:#2ecc71;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Roemmers", "Amarillo. Ej: Amoxidal. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#f1c40f;border-radius:2px;vertical-align:middle'></span>"),
            ("Elea", "Blanco y azul claro. Ej: Cronopen. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#fff;border:1px solid #ccc;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#85c1e9;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Raffo", "Blanco y bordo. Ej: Alpertan. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#fff;border:1px solid #ccc;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#922b21;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Casasco", "Blanco y rojo. Ej: Isobloc. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#fff;border:1px solid #ccc;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#c0392b;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Pfizer", "Blanco con franja azul y celeste. Ej: Trapax. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#fff;border:1px solid #ccc;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#2e86c1;border-radius:2px;vertical-align:middle;margin-left:2px'></span><span style='display:inline-block;width:12px;height:12px;background:#85c1e9;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Lepetit", "Blanco, naranja y verde. Ej: Vedilep, Normolipol, Rosux. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#fff;border:1px solid #ccc;border-radius:2px;vertical-align:middle'></span><span style='display:inline-block;width:12px;height:12px;background:#e67e22;border-radius:2px;vertical-align:middle;margin-left:2px'></span><span style='display:inline-block;width:12px;height:12px;background:#27ae60;border-radius:2px;vertical-align:middle;margin-left:2px'></span>"),
            ("Craveri", "Rojo. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#e74c3c;border-radius:2px;vertical-align:middle'></span>"),
            ("Bagó", "Violeta. &nbsp;<span style='display:inline-block;width:12px;height:12px;background:#8e44ad;border-radius:2px;vertical-align:middle'></span>"),
        ]
    },
    "🗄️ Ubicación en farmacia": {
        "icono": "🗄️",
        "items": [
            ("Psicotrópicos", "Cajoneras del lado izquierdo, ordenadas alfabéticamente. La caja debe decir 'Venta bajo receta archivada'."),
            ("Oftálmicos", "Primeras 3 cajoneras en la columna de la V."),
        ]
    },
    "🟠 Medicamentos con + naranja": {
        "icono": "🟠",
        "items": [
            ("Medicamentos con + naranja", "Tienen vademécum TUF o descuento de laboratorio aplicable."),
        ]
    },
    "❓ Preguntas clave en mostrador": {
        "icono": "❓",
        "items": [
            ("Preguntas generales", "¿Qué necesitás? / ¿De qué dosis? / ¿Por cuántos comprimidos? / ¿Por obra social o particular? / ¿Necesitás que te lo realice para reintegro? / ¿Necesitás  algo mas? "),
            ("Ibuprofeno", "¿Lo llevás en cápsulas o comprimidos? ¿De cuánto?"),
            ("Diclofenac", "¿Sos hipertenso? Si sí → dispensar potásico."),
            ("Antigripal (Qura Plus)", "¿Sos hipertenso?"),
            ("Medicamentos de venta libre o suplementos dietarios", "Acompañanar a la gondola a buscarlo."),
            ("Preguntas por gazas, solucion fisiologica, vaselina", "Decir que se encuentran en lo gondola de primeros auxilios."),
        ]
    },
    "💳 TU Farmacity (TUF)": {
        "icono": "💳",
        "items": [
            ("¿Cómo aplicarlo?", "Siempre preguntar si tiene TU Farmacity. Pedir DNI, cargar en punto de venta → Agregar cobertura → Vademécum TUF. No sacar troquel."),
            ("¿Qué decirle al cliente?", "Explicar el beneficio. Ej: 'Te sale con el 20% de descuento, ahorrás $15.000'."),
            ("Cliente sin TUF", "Hay un cartel con QR en el mostrador para que se adhiera en el momento."),
            ("Identificación visual", "Productos con TUF tienen un + naranja en la etiqueta."),
        ]
    },
    "📦 Vales": {
        "icono": "📦",
        "items": [
            ("Retirar un vale", "Punto de venta → Vale → ingresar número de vale (extremo derecho del papel). Buscar en cajonera chica Vale por orden alfabético. Sacar el papel pegado en el medicamento y entregar el papel que se imprime. El cliente lo entrega al personal de seguridad al salir."),
            ("Pedir un vale", "Buscar el medicamento → seleccionarlo → marcar en la etiqueta → colocar nombre del cliente o teléfono. Antes de imprimir el remito, verificar stock en droguería (Del Sud o Barracas)."),
            ("Verificar stock", "Página Suizzo / Del Sud: buscar, ver stock, confirmar. Si supera $600k consultar con el auxiliar farmacéutico. Si no está en una droguería, buscar en la otra. Si no está en ninguna → derivar a otro Farmacity."),
            ("Ver stock interno", "Punto de venta → buscar medicamento → F4 → Farm Amigas → Favoritos → Ver stock."),
            ("Horarios de retiro", "Vale pedido a la mañana (9-10 hs): disponible desde las 19 hs del mismo día. Vale pedido a las 18 hs: disponible al día siguiente desde las 15 hs."),
        ]
    },
    "🏥 Obras sociales — operatoria general": {
        "icono": "🏥",
        "items": [
            ("¿Cómo cargar una OS?", "Punto de venta → Agregar cobertura → nombre de la OS (Galeno, OSDE, Swiss Medical, etc.). Ver la información al lado de cada OS para despejar dudas."),
            ("Receta en papel", "Verificar fecha de validez, legibilidad de matrícula, tinta uniforme. Ante cualquier duda consultar a un compañero."),
            ("Receta digital", "Entrar por Reservorio → escanear número de afiliado → escanear número de receta."),
            ("Ejemplo: Galeno", "Escanear afiliado y receta → buscar medicamento → solicitar token → firmar el papel."),
        ]
    },
    "💰 Descuentos de laboratorios": {
        "icono": "💰",
        "items": [
            ("¿Cómo aplicar?", "Punto de venta → Agregar cobertura → buscar el laboratorio. Ej: PANALAB."),
            ("Panalab — 40% descuento", "Cajas blancas con rayas de color. Ej: Folcres, Valcatil Max, Dutapil, Combinater, Terekol, Ribatra. El paciente puede traer cupón o no. Si trae cupon → Cargar: descuento Panalab papel → escanear cupón + matrícula + fecha. Si no trae cupon → Copiar el número que empieza con 5... y como numero de matricula 5555 y colocar fecha del dia de dispensa. No sacar troquel."),
            ("Cepage / Eximia", "Productos de cosmética en el mueble detrás del mostrador. Agregar cobertura → descuento bono Eximia/Cepage → OK → escanear → sacar troquel → imprimir voucher. Enviar voucher por WhatsApp al 1141610510 o al celular viejo: 1144499024."),
        ]
    },
    "🩺 Servicio de enfermería": {
        "icono": "🩺",
        "items": [
            ("¿Cómo facturar?", "Por el punto de venta de farmacia."),
            ("Servicios disponibles", "Presión arterial / Servicio de diabetes (con o sin insumos) / Aplicación / Oximetría / Índice de masa corporal / Asesoramiento en nebulizadores."),
        ]
    },
}
 
with tab2:
    st.markdown("### 📋 Procedimientos operativos")
 
    for titulo, contenido in OS_DATA.items():
        with st.expander(titulo):
            for nombre, detalle in contenido["items"]:
                st.markdown(
                    f"""
                    <div style="
                        border-left: 3px solid #3b82f6;
                        padding: 8px 12px;
                        margin-bottom: 10px;
                        border-radius: 0 8px 8px 0;
                        background: var(--background-color);
                    ">
                        <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 3px;">{nombre}</div>
                        <div style="font-size: 0.85rem; color: #555; line-height: 1.5;">{detalle}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
 
    # PDF descargable cuando esté disponible
    import os
    pdf_path = "assets/guia_OS_general.pdf"
    if os.path.exists(pdf_path):
        st.divider()
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📥 Descargar guía completa de Obras Sociales (PDF)",
                data=f,
                file_name="guia_OS_general.pdf",
                mime="application/pdf",
                use_container_width=True,
            )