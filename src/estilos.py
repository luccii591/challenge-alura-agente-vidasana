"""Tema visual de la aplicación: paletas clara y oscura, y CSS derivado.

Streamlit no permite cambiar de tema en caliente desde su configuración, así
que el tema se resuelve aquí: se definen las dos paletas como variables CSS y
se inyecta la hoja de estilos correspondiente en cada render. Los selectores se
apoyan en atributos `data-testid`, que son la superficie más estable de
Streamlit frente a los nombres de clase autogenerados.
"""

from __future__ import annotations

from string import Template

PALETAS: dict[str, dict[str, str]] = {
    "claro": {
        "fondo": "#F1F5F9",
        "fondo_degradado": "radial-gradient(1200px 600px at 15% -10%, #E0F2F1 0%, transparent 55%), radial-gradient(900px 500px at 100% 0%, #E0E7FF 0%, transparent 50%)",
        "superficie": "#FFFFFF",
        "superficie_alt": "#F8FAFC",
        "borde": "#E2E8F0",
        "texto": "#0F172A",
        "texto_suave": "#64748B",
        "acento": "#0D9488",
        "acento_fuerte": "#0F766E",
        "acento_tenue": "#CCFBF1",
        "burbuja_usuario": "#0F766E",
        "burbuja_usuario_texto": "#FFFFFF",
        "aviso_fondo": "#FEF3C7",
        "aviso_borde": "#F59E0B",
        "aviso_texto": "#78350F",
        "sombra": "0 1px 2px rgba(15,23,42,.04), 0 8px 24px -12px rgba(15,23,42,.15)",
        "codigo_fondo": "#F1F5F9",
        "codigo_texto": "#0F766E",
    },
    "oscuro": {
        "fondo": "#0B1220",
        "fondo_degradado": "radial-gradient(1200px 600px at 15% -10%, #0F2E2B 0%, transparent 55%), radial-gradient(900px 500px at 100% 0%, #16203C 0%, transparent 50%)",
        "superficie": "#131C2E",
        "superficie_alt": "#0F1728",
        "borde": "#243044",
        "texto": "#E8EEF7",
        "texto_suave": "#93A3B8",
        "acento": "#2DD4BF",
        "acento_fuerte": "#5EEAD4",
        "acento_tenue": "#134E4A",
        "burbuja_usuario": "#134E4A",
        "burbuja_usuario_texto": "#E8FFFB",
        "aviso_fondo": "#2A2010",
        "aviso_borde": "#B45309",
        "aviso_texto": "#FCD9A0",
        "sombra": "0 1px 2px rgba(0,0,0,.4), 0 12px 32px -14px rgba(0,0,0,.7)",
        "codigo_fondo": "#0B1220",
        "codigo_texto": "#5EEAD4",
    },
}


_PLANTILLA_CSS = Template(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --vs-fondo: $fondo;
  --vs-superficie: $superficie;
  --vs-superficie-alt: $superficie_alt;
  --vs-borde: $borde;
  --vs-texto: $texto;
  --vs-texto-suave: $texto_suave;
  --vs-acento: $acento;
  --vs-acento-fuerte: $acento_fuerte;
  --vs-acento-tenue: $acento_tenue;
  --vs-sombra: $sombra;
}

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* ---------- Lienzo ---------- */
[data-testid="stAppViewContainer"] {
  background: $fondo_degradado, $fondo;
  color: var(--vs-texto);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMain"] .block-container { padding-top: 2.2rem; max-width: 52rem; }

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 { color: var(--vs-texto); }

/* ---------- Encabezado ---------- */
.vs-hero {
  background: var(--vs-superficie);
  border: 1px solid var(--vs-borde);
  border-radius: 20px;
  padding: 1.6rem 1.8rem;
  box-shadow: var(--vs-sombra);
  position: relative;
  overflow: hidden;
  margin-bottom: 1rem;
}
.vs-hero::before {
  content: "";
  position: absolute; inset: 0 0 auto 0; height: 4px;
  background: linear-gradient(90deg, var(--vs-acento), var(--vs-acento-fuerte), transparent);
}
.vs-hero-fila { display: flex; align-items: center; gap: 1rem; }
.vs-hero-icono {
  width: 54px; height: 54px; flex: 0 0 54px;
  display: grid; place-items: center;
  border-radius: 16px; font-size: 1.7rem;
  background: var(--vs-acento-tenue);
  border: 1px solid var(--vs-borde);
}
.vs-hero-titulo {
  margin: 0; font-size: 1.85rem; font-weight: 800;
  letter-spacing: -.02em; color: var(--vs-texto); line-height: 1.15;
}
.vs-hero-sub { margin: .3rem 0 0; font-size: .92rem; color: var(--vs-texto-suave); }
.vs-chips { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: 1rem; }
.vs-chip {
  font-size: .72rem; font-weight: 600; letter-spacing: .02em;
  padding: .28rem .6rem; border-radius: 999px;
  background: var(--vs-superficie-alt);
  border: 1px solid var(--vs-borde);
  color: var(--vs-texto-suave);
}
.vs-chip-acento {
  background: var(--vs-acento-tenue);
  border-color: var(--vs-acento);
  color: var(--vs-acento-fuerte);
}

/* ---------- Aviso de proyecto ficticio ---------- */
.vs-aviso {
  display: flex; gap: .7rem; align-items: flex-start;
  background: $aviso_fondo;
  border: 1px solid $aviso_borde;
  border-left-width: 4px;
  border-radius: 12px;
  padding: .8rem 1rem;
  margin-bottom: 1.4rem;
  font-size: .82rem; line-height: 1.5;
  color: $aviso_texto;
}
.vs-aviso strong { color: $aviso_texto; }

/* ---------- Mensajes de chat ---------- */
[data-testid="stChatMessage"] {
  background: var(--vs-superficie);
  border: 1px solid var(--vs-borde);
  border-radius: 16px;
  padding: 1rem 1.1rem;
  box-shadow: var(--vs-sombra);
  margin-bottom: .7rem;
}
/* Streamlit no expone ningún atributo estable que distinga el mensaje del
   usuario del de la asistente: solo cambia una clase autogenerada del tipo
   `st-emotion-cache-1fee4w7`, que varía entre versiones. Por eso la propia
   aplicación inserta un marcador vacío en los mensajes del usuario y el estilo
   se engancha a él. */
.vs-marca-usuario { display: none; }
[data-testid="stChatMessage"]:has(.vs-marca-usuario) {
  background: $burbuja_usuario;
  border-color: $burbuja_usuario;
}
[data-testid="stChatMessage"]:has(.vs-marca-usuario) p,
[data-testid="stChatMessage"]:has(.vs-marca-usuario) span {
  color: $burbuja_usuario_texto !important;
  font-weight: 500;
}
[data-testid="stChatMessage"] table {
  border-collapse: collapse; width: 100%; font-size: .86rem;
}
[data-testid="stChatMessage"] th, [data-testid="stChatMessage"] td {
  border: 1px solid var(--vs-borde); padding: .45rem .6rem;
}
[data-testid="stChatMessage"] th { background: var(--vs-superficie-alt); }

/* ---------- Entrada de chat ---------- */
/* La franja inferior la pinta Streamlit con su propio color de tema; se
   transparenta para que el degradado del lienzo continúe hasta abajo. */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
  background: transparent !important;
}
[data-testid="stBottomBlockContainer"] { padding-bottom: 1.2rem; }

[data-testid="stChatInput"] {
  background: var(--vs-superficie) !important;
  border: 1px solid var(--vs-borde);
  border-radius: 14px;
  box-shadow: var(--vs-sombra);
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: var(--vs-texto) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--vs-texto-suave) !important; }
[data-testid="stChatInput"] button { background: transparent !important; }
[data-testid="stChatInput"] svg { fill: var(--vs-acento); }

/* ---------- Barra lateral ---------- */
[data-testid="stSidebar"] {
  background: var(--vs-superficie);
  border-right: 1px solid var(--vs-borde);
}
[data-testid="stSidebar"] * { color: var(--vs-texto); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-size: .78rem !important; font-weight: 700; letter-spacing: .09em;
  text-transform: uppercase; color: var(--vs-texto-suave) !important;
  margin-bottom: .5rem;
}
[data-testid="stSidebar"] hr { border-color: var(--vs-borde); }

/* Tarjeta de métrica */
[data-testid="stMetric"] {
  background: var(--vs-superficie-alt);
  border: 1px solid var(--vs-borde);
  border-radius: 14px;
  padding: .8rem .9rem;
}
[data-testid="stMetricValue"] {
  font-size: 1.9rem !important; font-weight: 800;
  color: var(--vs-acento) !important; letter-spacing: -.02em;
}
[data-testid="stMetricLabel"] p {
  font-size: .74rem !important; font-weight: 600;
  letter-spacing: .05em; text-transform: uppercase;
  color: var(--vs-texto-suave) !important;
}

/* Botones de pregunta sugerida */
[data-testid="stSidebar"] .stButton > button {
  width: 100%; text-align: left; justify-content: flex-start;
  white-space: normal; height: auto; line-height: 1.35;
  background: var(--vs-superficie-alt);
  border: 1px solid var(--vs-borde);
  border-radius: 12px;
  padding: .6rem .75rem;
  font-size: .82rem; font-weight: 500;
  color: var(--vs-texto);
  transition: transform .12s ease, border-color .12s ease, background .12s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--vs-acento);
  background: var(--vs-acento-tenue);
  transform: translateX(2px);
}
[data-testid="stSidebar"] .stButton > button:focus:not(:active) {
  border-color: var(--vs-acento); color: var(--vs-texto);
}

/* ---------- Avisos (st.info / st.error) ---------- */
[data-testid="stAlert"] {
  background: var(--vs-superficie) !important;
  border: 1px solid var(--vs-borde);
  border-radius: 14px;
  box-shadow: var(--vs-sombra);
}
[data-testid="stAlertContainer"] {
  background: transparent !important;
  color: var(--vs-texto) !important;
}
[data-testid="stAlertContainer"] p { color: var(--vs-texto) !important; }

/* ---------- Desplegables ---------- */
[data-testid="stExpander"] {
  background: var(--vs-superficie-alt);
  border: 1px solid var(--vs-borde);
  border-radius: 12px;
  overflow: hidden;
}
[data-testid="stExpander"] details,
[data-testid="stExpander"] summary,
[data-testid="stExpanderDetails"] {
  background: var(--vs-superficie-alt) !important;
  border: none !important;
  color: var(--vs-texto) !important;
}
[data-testid="stExpander"] summary { font-size: .84rem; font-weight: 600; }
[data-testid="stExpander"] summary:hover { color: var(--vs-acento) !important; }
[data-testid="stExpander"] summary svg { fill: var(--vs-texto-suave); }

/* Bloque JSON de los argumentos de la herramienta */
[data-testid="stJson"] {
  background: var(--vs-superficie) !important;
  border: 1px solid var(--vs-borde);
  border-radius: 8px;
  padding: .45rem .65rem;
}
[data-testid="stJson"] * { background: transparent !important; }

/* Nombre de herramienta en la traza */
[data-testid="stMain"] code {
  background: $codigo_fondo;
  color: $codigo_texto;
  border: 1px solid var(--vs-borde);
  border-radius: 6px;
  padding: .12rem .4rem;
  font-size: .82em; font-weight: 600;
}

/* ---------- Interruptor de tema ---------- */
[data-testid="stSidebar"] [data-testid="stToggle"] { margin-bottom: .2rem; }

/* ---------- Pie ---------- */
.vs-pie {
  margin-top: 1.2rem; padding-top: .9rem;
  border-top: 1px solid var(--vs-borde);
  font-size: .72rem; color: var(--vs-texto-suave); line-height: 1.5;
}
.vs-pie a { color: var(--vs-acento); text-decoration: none; }

/* ---------- Responsive ---------- */
@media (max-width: 640px) {
  .vs-hero-titulo { font-size: 1.4rem; }
  .vs-hero-icono { width: 44px; height: 44px; flex-basis: 44px; font-size: 1.35rem; }
  [data-testid="stMain"] .block-container { padding-top: 1.2rem; }
}
</style>
"""
)


def construir_css(tema: str) -> str:
    """Devuelve la hoja de estilos completa para el tema indicado."""
    return _PLANTILLA_CSS.substitute(PALETAS[tema])


def encabezado_html(titulo: str, subtitulo: str, chips: list[tuple[str, bool]]) -> str:
    """Construye el encabezado destacado de la aplicación.

    `chips` es una lista de pares (texto, destacado).
    """
    etiquetas = "".join(
        f'<span class="vs-chip{" vs-chip-acento" if destacado else ""}">{texto}</span>'
        for texto, destacado in chips
    )
    return f"""
<div class="vs-hero">
  <div class="vs-hero-fila">
    <div class="vs-hero-icono">🩺</div>
    <div>
      <h1 class="vs-hero-titulo">{titulo}</h1>
      <p class="vs-hero-sub">{subtitulo}</p>
    </div>
  </div>
  <div class="vs-chips">{etiquetas}</div>
</div>
"""


AVISO_HTML = """
<div class="vs-aviso">
  <span>⚠️</span>
  <div><strong>Proyecto académico.</strong> Clínica VidaSana es una empresa ficticia y toda
  la documentación es material de demostración. Los nombres, precios, direcciones y
  teléfonos son inventados: no corresponden a ningún establecimiento de salud real ni
  deben usarse para tomar decisiones médicas o administrativas.</div>
</div>
"""


PIE_HTML = """
<div class="vs-pie">
  <strong>Challenge Alura Agente</strong> · Oracle Next Education (ONE) — Fase Tech AI Builder<br/>
  Agente RAG con <em>function calling</em> sobre Google Gemini ·
  <a href="https://github.com/luccii591/challenge-alura-agente-vidasana" target="_blank">Código en GitHub</a>
</div>
"""
