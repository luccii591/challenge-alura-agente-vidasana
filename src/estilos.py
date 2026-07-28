"""Sistema visual de la aplicación: paletas, animaciones y componentes.

Streamlit no permite alternar de tema en caliente desde su configuración, así
que el tema se resuelve aquí: cada paleta se materializa en variables CSS y la
hoja de estilos se inyecta en cada render.

Los selectores se apoyan en atributos `data-testid`, que son la superficie más
estable de Streamlit frente a los nombres de clase autogenerados.
"""

from __future__ import annotations

import html
from string import Template

PALETAS: dict[str, dict[str, str]] = {
    "claro": {
        "fondo": "#EEF2F7",
        "aurora_a": "rgba(13,148,136,.30)",
        "aurora_b": "rgba(99,102,241,.22)",
        "aurora_c": "rgba(56,189,248,.20)",
        "vidrio": "rgba(255,255,255,.72)",
        "vidrio_alt": "rgba(255,255,255,.55)",
        "vidrio_borde": "rgba(15,23,42,.09)",
        "superficie_solida": "#FFFFFF",
        "texto": "#0B1220",
        "texto_suave": "#5A6B84",
        "acento": "#0D9488",
        "acento_2": "#4F46E5",
        "acento_tenue": "rgba(13,148,136,.12)",
        "burbuja_usuario": "linear-gradient(135deg,#0F766E,#115E59)",
        "burbuja_usuario_texto": "#F0FDFA",
        "aviso_fondo": "rgba(251,191,36,.14)",
        "aviso_borde": "#F59E0B",
        "aviso_texto": "#78350F",
        "sombra": "0 1px 2px rgba(15,23,42,.04), 0 18px 40px -24px rgba(15,23,42,.35)",
        "codigo_fondo": "rgba(13,148,136,.10)",
        "codigo_texto": "#0F766E",
        "pista": "rgba(15,23,42,.08)",
    },
    "oscuro": {
        "fondo": "#070B14",
        "aurora_a": "rgba(45,212,191,.26)",
        "aurora_b": "rgba(99,102,241,.26)",
        "aurora_c": "rgba(14,165,233,.18)",
        "vidrio": "rgba(19,28,46,.68)",
        "vidrio_alt": "rgba(13,20,34,.55)",
        "vidrio_borde": "rgba(148,163,184,.16)",
        "superficie_solida": "#111A2B",
        "texto": "#E9F0FA",
        "texto_suave": "#8FA2BC",
        "acento": "#2DD4BF",
        "acento_2": "#818CF8",
        "acento_tenue": "rgba(45,212,191,.14)",
        "burbuja_usuario": "linear-gradient(135deg,#0F766E,#155E75)",
        "burbuja_usuario_texto": "#ECFEFF",
        "aviso_fondo": "rgba(180,83,9,.18)",
        "aviso_borde": "#B45309",
        "aviso_texto": "#FCD9A0",
        "sombra": "0 1px 2px rgba(0,0,0,.5), 0 22px 50px -26px rgba(0,0,0,.9)",
        "codigo_fondo": "rgba(45,212,191,.10)",
        "codigo_texto": "#5EEAD4",
        "pista": "rgba(148,163,184,.16)",
    },
}


_PLANTILLA_CSS = Template(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap');

:root {
  --vs-fondo: $fondo;
  --vs-vidrio: $vidrio;
  --vs-vidrio-alt: $vidrio_alt;
  --vs-borde: $vidrio_borde;
  --vs-solido: $superficie_solida;
  --vs-texto: $texto;
  --vs-suave: $texto_suave;
  --vs-acento: $acento;
  --vs-acento-2: $acento_2;
  --vs-acento-tenue: $acento_tenue;
  --vs-sombra: $sombra;
  --vs-pista: $pista;
}

html, body, [data-testid="stAppViewContainer"], [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ===================== Lienzo y aurora ===================== */
[data-testid="stAppViewContainer"] {
  background: $fondo;
  color: var(--vs-texto);
  /* `isolation` basta para crear el contexto de apilamiento que necesita la
     aurora. No se toca `position`: Streamlit lo fija en `absolute` para ceñir
     el contenedor a la altura de la ventana, y cambiarlo lo hace crecer con su
     contenido, dejando la barra lateral sin scroll. */
  isolation: isolate;
}
/* La aurora se manda al fondo con z-index negativo dentro del contexto de
   apilamiento que crea `isolation: isolate`. Es deliberado no elevar el
   contenido con `position: relative`: la barra lateral de Streamlit usa
   `position: fixed` para ceñirse a la altura de la ventana, y sobrescribir su
   posicionamiento la hace crecer con su contenido, dejando sin efecto el
   `overflow: auto` que le da scroll. */
[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed; inset: -20%;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(38% 42% at 18% 22%, $aurora_a 0%, transparent 62%),
    radial-gradient(34% 40% at 82% 12%, $aurora_b 0%, transparent 60%),
    radial-gradient(42% 38% at 62% 88%, $aurora_c 0%, transparent 62%);
  filter: blur(46px) saturate(120%);
  animation: vs-aurora 26s ease-in-out infinite alternate;
  will-change: transform;
}
@keyframes vs-aurora {
  0%   { transform: translate3d(0,0,0) scale(1); }
  50%  { transform: translate3d(2.5%, -2%, 0) scale(1.08); }
  100% { transform: translate3d(-2%, 2.5%, 0) scale(1.04); }
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stMain"] .block-container { padding-top: 2rem; max-width: 54rem; }

[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4 {
  color: var(--vs-texto);
}

/* ===================== Encabezado ===================== */
.vs-hero {
  position: relative;
  background: var(--vs-vidrio);
  -webkit-backdrop-filter: blur(22px) saturate(180%);
  backdrop-filter: blur(22px) saturate(180%);
  border: 1px solid var(--vs-borde);
  border-radius: 24px;
  padding: 1.7rem 1.9rem 1.5rem;
  box-shadow: var(--vs-sombra);
  overflow: hidden;
  margin-bottom: .9rem;
  animation: vs-entrada .55s cubic-bezier(.2,.7,.3,1) both;
}
.vs-hero::after {
  content: "";
  position: absolute; inset: 0 0 auto 0; height: 3px;
  background: linear-gradient(90deg, transparent, var(--vs-acento), var(--vs-acento-2), transparent);
  background-size: 200% 100%;
  animation: vs-barrido 6s linear infinite;
}
@keyframes vs-barrido { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@keyframes vs-entrada { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform:none; } }

.vs-hero-fila { display: flex; align-items: center; gap: 1.05rem; }
.vs-logo {
  width: 58px; height: 58px; flex: 0 0 58px;
  border-radius: 18px;
  display: grid; place-items: center;
  background: linear-gradient(140deg, var(--vs-acento), var(--vs-acento-2));
  box-shadow: 0 10px 26px -12px var(--vs-acento);
}
.vs-logo svg { width: 34px; height: 34px; }
.vs-logo .vs-trazo {
  stroke: #fff; stroke-width: 2.1; fill: none;
  stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: 66; stroke-dashoffset: 66;
  animation: vs-latido 2.6s ease-in-out infinite;
}
@keyframes vs-latido {
  0%   { stroke-dashoffset: 66; opacity: .35; }
  45%  { stroke-dashoffset: 0;  opacity: 1; }
  75%  { stroke-dashoffset: 0;  opacity: 1; }
  100% { stroke-dashoffset: -66; opacity: .35; }
}

.vs-titulo {
  margin: 0; font-size: 2.05rem; font-weight: 900; letter-spacing: -.035em; line-height: 1.08;
  background: linear-gradient(100deg, var(--vs-texto) 10%, var(--vs-acento) 45%, var(--vs-acento-2) 70%, var(--vs-texto) 95%);
  background-size: 220% auto;
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent;
  animation: vs-brillo 9s linear infinite;
}
@keyframes vs-brillo { to { background-position: 220% center; } }
.vs-sub { margin: .35rem 0 0; font-size: .92rem; color: var(--vs-suave); }

.vs-chips { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: 1.05rem; }
.vs-chip {
  font-size: .715rem; font-weight: 600; letter-spacing: .015em;
  padding: .3rem .68rem; border-radius: 999px;
  background: var(--vs-vidrio-alt);
  border: 1px solid var(--vs-borde);
  color: var(--vs-suave);
  transition: transform .18s ease, border-color .18s ease, color .18s ease;
}
.vs-chip:hover { transform: translateY(-2px); border-color: var(--vs-acento); color: var(--vs-texto); }
.vs-chip-vivo {
  background: var(--vs-acento-tenue);
  border-color: var(--vs-acento);
  color: var(--vs-acento);
  display: inline-flex; align-items: center; gap: .38rem;
}
.vs-punto {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--vs-acento);
  box-shadow: 0 0 0 0 var(--vs-acento);
  animation: vs-pulso 2s infinite;
}
@keyframes vs-pulso {
  0%   { box-shadow: 0 0 0 0 var(--vs-acento); opacity: 1; }
  70%  { box-shadow: 0 0 0 7px transparent; opacity: .75; }
  100% { box-shadow: 0 0 0 0 transparent; opacity: 1; }
}

/* ===================== Aviso ===================== */
.vs-aviso {
  display: flex; gap: .7rem; align-items: flex-start;
  background: $aviso_fondo;
  border: 1px solid $aviso_borde; border-left-width: 3px;
  border-radius: 14px; padding: .8rem 1rem; margin-bottom: 1.3rem;
  font-size: .8rem; line-height: 1.55; color: $aviso_texto;
  -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
}
.vs-aviso strong { color: $aviso_texto; }

/* ===================== Chat ===================== */
[data-testid="stChatMessage"] {
  background: var(--vs-vidrio);
  -webkit-backdrop-filter: blur(18px) saturate(170%);
  backdrop-filter: blur(18px) saturate(170%);
  border: 1px solid var(--vs-borde);
  border-radius: 18px;
  padding: 1rem 1.15rem;
  box-shadow: var(--vs-sombra);
  margin-bottom: .65rem;
  animation: vs-entrada .4s cubic-bezier(.2,.7,.3,1) both;
}
/* Streamlit no expone ningún atributo estable que distinga el mensaje del
   usuario del de la asistente: solo cambia una clase autogenerada del tipo
   `st-emotion-cache-1fee4w7`, que varía entre versiones. Por eso la propia
   aplicación inserta un marcador vacío y el estilo se engancha a él. */
.vs-marca-usuario { display: none; }
[data-testid="stChatMessage"]:has(.vs-marca-usuario) {
  background: $burbuja_usuario;
  border-color: transparent;
}
[data-testid="stChatMessage"]:has(.vs-marca-usuario) p {
  color: $burbuja_usuario_texto !important; font-weight: 500;
}
[data-testid="stChatMessage"] table { border-collapse: collapse; width: 100%; font-size: .86rem; }
[data-testid="stChatMessage"] th, [data-testid="stChatMessage"] td {
  border: 1px solid var(--vs-borde); padding: .45rem .6rem;
}
[data-testid="stChatMessage"] th { background: var(--vs-vidrio-alt); }

/* Cursor de escritura durante el streaming */
.vs-cursor {
  display: inline-block; width: 7px; height: 1.05em;
  background: var(--vs-acento); border-radius: 2px;
  vertical-align: text-bottom; margin-left: 2px;
  animation: vs-parpadeo 1s steps(2, start) infinite;
}
@keyframes vs-parpadeo { 50% { opacity: 0; } }

/* ===================== Pasos del agente en vivo ===================== */
.vs-pasos { display: flex; flex-direction: column; gap: .32rem; margin: .1rem 0 .2rem; }
.vs-paso {
  display: flex; align-items: center; gap: .55rem;
  font-size: .78rem; color: var(--vs-suave);
  padding: .34rem .6rem; border-radius: 10px;
  background: var(--vs-vidrio-alt); border: 1px solid var(--vs-borde);
  animation: vs-entrada .3s ease both;
}
.vs-paso b { color: var(--vs-texto); font-weight: 600; }
.vs-paso code {
  font-family: 'JetBrains Mono', monospace; font-size: .74rem;
  color: $codigo_texto; background: $codigo_fondo;
  padding: .08rem .35rem; border-radius: 5px;
}
.vs-paso-activo { border-color: var(--vs-acento); }

/* ===================== Tarjetas de fuente ===================== */
.vs-fuentes { display: flex; flex-direction: column; gap: .45rem; margin-top: .2rem; }
.vs-fuente {
  background: var(--vs-vidrio-alt);
  border: 1px solid var(--vs-borde);
  border-radius: 12px; padding: .55rem .7rem;
  transition: border-color .18s ease, transform .18s ease;
}
.vs-fuente:hover { border-color: var(--vs-acento); transform: translateX(2px); }
.vs-fuente-fila { display: flex; justify-content: space-between; align-items: center; gap: .6rem; }
.vs-fuente-nombre { font-size: .8rem; font-weight: 600; color: var(--vs-texto); }
.vs-fuente-valor { font-size: .72rem; font-weight: 700; color: var(--vs-acento); font-variant-numeric: tabular-nums; }
.vs-pista {
  height: 4px; border-radius: 999px; background: var(--vs-pista);
  margin-top: .42rem; overflow: hidden;
}
.vs-pista span {
  display: block; height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--vs-acento), var(--vs-acento-2));
  animation: vs-llenar .8s cubic-bezier(.2,.7,.3,1) both;
}
@keyframes vs-llenar { from { width: 0 !important; } }
.vs-fuente-tipo { font-size: .66rem; color: var(--vs-suave); letter-spacing: .04em; text-transform: uppercase; }

/* ===================== Entrada ===================== */
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] { background: transparent !important; }
[data-testid="stBottomBlockContainer"] { padding-bottom: 1.1rem; }
[data-testid="stChatInput"] {
  background: var(--vs-vidrio) !important;
  -webkit-backdrop-filter: blur(18px) saturate(180%);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid var(--vs-borde);
  border-radius: 16px; box-shadow: var(--vs-sombra);
  transition: border-color .2s ease, box-shadow .2s ease;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--vs-acento);
  box-shadow: 0 0 0 3px var(--vs-acento-tenue), var(--vs-sombra);
}
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea {
  background: transparent !important; color: var(--vs-texto) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--vs-suave) !important; }
[data-testid="stChatInput"] button { background: transparent !important; }
[data-testid="stChatInput"] svg { fill: var(--vs-acento); }

/* ===================== Barra lateral ===================== */
[data-testid="stSidebar"] {
  background: var(--vs-vidrio);
  -webkit-backdrop-filter: blur(20px) saturate(170%);
  backdrop-filter: blur(20px) saturate(170%);
  border-right: 1px solid var(--vs-borde);
}
[data-testid="stSidebar"] * { color: var(--vs-texto); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-size: .72rem !important; font-weight: 800; letter-spacing: .11em;
  text-transform: uppercase; color: var(--vs-suave) !important; margin-bottom: .5rem;
}
[data-testid="stSidebar"] hr { border-color: var(--vs-borde); }

[data-testid="stMetric"] {
  background: var(--vs-vidrio-alt); border: 1px solid var(--vs-borde);
  border-radius: 14px; padding: .75rem .85rem;
  transition: border-color .18s ease, transform .18s ease;
}
[data-testid="stMetric"]:hover { border-color: var(--vs-acento); transform: translateY(-2px); }
[data-testid="stMetricValue"] {
  font-size: 1.85rem !important; font-weight: 900; letter-spacing: -.03em;
  background: linear-gradient(120deg, var(--vs-acento), var(--vs-acento-2));
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
[data-testid="stMetricLabel"] p {
  font-size: .68rem !important; font-weight: 700; letter-spacing: .07em;
  text-transform: uppercase; color: var(--vs-suave) !important;
}

[data-testid="stSidebar"] .stButton > button {
  width: 100%; text-align: left; justify-content: flex-start;
  white-space: normal; height: auto; line-height: 1.35;
  background: var(--vs-vidrio-alt); border: 1px solid var(--vs-borde);
  border-radius: 12px; padding: .6rem .75rem;
  font-size: .81rem; font-weight: 500; color: var(--vs-texto);
  position: relative; overflow: hidden;
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}
[data-testid="stSidebar"] .stButton > button::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
  background: linear-gradient(180deg, var(--vs-acento), var(--vs-acento-2));
  transform: scaleY(0); transform-origin: top; transition: transform .18s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--vs-acento); transform: translateX(3px);
  box-shadow: 0 8px 20px -14px var(--vs-acento);
}
[data-testid="stSidebar"] .stButton > button:hover::before { transform: scaleY(1); }
[data-testid="stSidebar"] .stButton > button:focus:not(:active) {
  border-color: var(--vs-acento); color: var(--vs-texto);
}

/* ===================== Avisos y desplegables ===================== */
[data-testid="stAlert"] {
  background: var(--vs-vidrio) !important;
  -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px);
  border: 1px solid var(--vs-borde); border-radius: 16px; box-shadow: var(--vs-sombra);
}
[data-testid="stAlertContainer"] { background: transparent !important; color: var(--vs-texto) !important; }
[data-testid="stAlertContainer"] p { color: var(--vs-texto) !important; }

[data-testid="stExpander"] {
  background: var(--vs-vidrio-alt); border: 1px solid var(--vs-borde);
  border-radius: 14px; overflow: hidden;
}
[data-testid="stExpander"] details, [data-testid="stExpander"] summary,
[data-testid="stExpanderDetails"] {
  background: transparent !important; border: none !important; color: var(--vs-texto) !important;
}
[data-testid="stExpander"] summary { font-size: .82rem; font-weight: 600; }
[data-testid="stExpander"] summary:hover { color: var(--vs-acento) !important; }
[data-testid="stExpander"] summary svg { fill: var(--vs-suave); }

[data-testid="stJson"] {
  background: var(--vs-solido) !important; border: 1px solid var(--vs-borde);
  border-radius: 10px; padding: .45rem .65rem;
}
[data-testid="stJson"] * { background: transparent !important; }

[data-testid="stMain"] code {
  font-family: 'JetBrains Mono', monospace;
  background: $codigo_fondo; color: $codigo_texto;
  border: 1px solid var(--vs-borde); border-radius: 6px;
  padding: .12rem .4rem; font-size: .8em; font-weight: 500;
}

/* ===================== Pie ===================== */
.vs-pie {
  margin-top: 1.1rem; padding-top: .85rem; border-top: 1px solid var(--vs-borde);
  font-size: .7rem; color: var(--vs-suave); line-height: 1.55;
}
.vs-pie a { color: var(--vs-acento); text-decoration: none; }
.vs-pie a:hover { text-decoration: underline; }

/* ===================== Responsive y accesibilidad ===================== */
@media (max-width: 640px) {
  .vs-titulo { font-size: 1.5rem; }
  .vs-logo { width: 46px; height: 46px; flex-basis: 46px; }
  .vs-logo svg { width: 27px; height: 27px; }
  [data-testid="stMain"] .block-container { padding-top: 1.1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""
)


_LOGO_SVG = """
<svg viewBox="0 0 40 40" aria-hidden="true">
  <path class="vs-trazo" d="M3 21h7l3.2-8.4 4.6 15.6 4-11.2 2.6 4h12.6"/>
</svg>
"""


def construir_css(tema: str) -> str:
    """Devuelve la hoja de estilos completa para el tema indicado."""
    return _PLANTILLA_CSS.substitute(PALETAS[tema])


def encabezado_html(titulo: str, subtitulo: str, chips: list[tuple[str, bool]]) -> str:
    """Encabezado con logo animado, título en degradado y etiquetas del corpus."""
    etiquetas = "".join(
        (
            f'<span class="vs-chip vs-chip-vivo"><span class="vs-punto"></span>{html.escape(texto)}</span>'
            if vivo
            else f'<span class="vs-chip">{html.escape(texto)}</span>'
        )
        for texto, vivo in chips
    )
    return f"""
<div class="vs-hero">
  <div class="vs-hero-fila">
    <div class="vs-logo">{_LOGO_SVG}</div>
    <div>
      <h1 class="vs-titulo">{html.escape(titulo)}</h1>
      <p class="vs-sub">{html.escape(subtitulo)}</p>
    </div>
  </div>
  <div class="vs-chips">{etiquetas}</div>
</div>
"""


def paso_html(texto: str, activo: bool = False) -> str:
    """Píldora que describe un paso del agente. `texto` admite `<b>` y `<code>`."""
    clase = "vs-paso vs-paso-activo" if activo else "vs-paso"
    return f'<div class="{clase}">{texto}</div>'


def fuentes_html(fuentes: list) -> str:
    """Tarjetas de documento con la confianza de la recuperación semántica."""
    if not fuentes:
        return ""

    tarjetas = []
    for fuente in fuentes:
        exacta = fuente.similitud is None
        etiqueta = "consulta exacta" if exacta else "similitud semántica"
        valor = "100%" if exacta else f"{fuente.confianza}%"
        tarjetas.append(
            f"""
<div class="vs-fuente">
  <div class="vs-fuente-fila">
    <span class="vs-fuente-nombre">📄 {html.escape(fuente.nombre)}</span>
    <span class="vs-fuente-valor">{valor}</span>
  </div>
  <div class="vs-pista"><span style="width:{fuente.confianza}%"></span></div>
  <div class="vs-fuente-tipo">{etiqueta}</div>
</div>"""
        )

    return f'<div class="vs-fuentes">{"".join(tarjetas)}</div>'


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
  <strong>Challenge Alura Agente</strong> · Oracle Next Education (ONE) — Tech AI Builder<br/>
  Agente RAG con <em>function calling</em> sobre Google Gemini ·
  <a href="https://github.com/luccii591/challenge-alura-agente-vidasana" target="_blank">Código en GitHub</a>
</div>
"""
