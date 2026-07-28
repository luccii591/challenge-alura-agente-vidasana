"""Interfaz web del Asistente VidaSana (Streamlit).

    streamlit run app.py
"""

from __future__ import annotations

import hashlib
import html
import os
import sys
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------- #
# Recarga del código propio tras un despliegue
# --------------------------------------------------------------------------- #
# Streamlit Cloud vuelve a ejecutar `app.py` cuando cambia el repositorio, pero
# conserva en `sys.modules` los módulos de `src` ya importados. Si un despliegue
# añade una función a `src/`, el script nuevo se encuentra con el módulo viejo y
# la aplicación queda caída con `ImportError` hasta que alguien la reinicia a
# mano. Aquí se detecta ese desfase comparando una huella del código fuente y,
# si cambió, se purgan los módulos para que se importen frescos.

_DIRECTORIO_SRC = Path(__file__).resolve().parent / "src"
_CLAVE_HUELLA = "VS_HUELLA_CODIGO"


def _huella_del_codigo() -> str:
    digest = hashlib.sha256()
    for ruta in sorted(_DIRECTORIO_SRC.glob("*.py")):
        estado = ruta.stat()
        digest.update(ruta.name.encode("utf-8"))
        digest.update(str(estado.st_size).encode("utf-8"))
        digest.update(str(int(estado.st_mtime)).encode("utf-8"))
    return digest.hexdigest()[:16]


_huella_actual = _huella_del_codigo()
CODIGO_RECARGADO = os.environ.get(_CLAVE_HUELLA) not in (None, _huella_actual)

if os.environ.get(_CLAVE_HUELLA) != _huella_actual:
    for _modulo in [n for n in list(sys.modules) if n == "src" or n.startswith("src.")]:
        del sys.modules[_modulo]
    os.environ[_CLAVE_HUELLA] = _huella_actual

from src.agent import AgenteVidaSana, BaseDeConocimiento  # noqa: E402
from src.config import DIRECTORIO_DATOS, NOMBRE_CLINICA  # noqa: E402
from src.estilos import (  # noqa: E402
    AVISO_HTML,
    PIE_HTML,
    construir_css,
    encabezado_html,
    fuentes_html,
    paso_html,
)
from src.prompts import PREGUNTAS_DE_EJEMPLO  # noqa: E402

st.set_page_config(
    page_title="Asistente VidaSana | Agente de IA",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Tema
# --------------------------------------------------------------------------- #

# Si el código se recargó, los objetos cacheados pertenecen a las clases
# antiguas: se descartan para reconstruirlos con el código nuevo.
if CODIGO_RECARGADO:
    st.cache_resource.clear()
    st.session_state.pop("agente", None)

st.session_state.setdefault("tema_oscuro", False)
st.markdown(
    construir_css("oscuro" if st.session_state.tema_oscuro else "claro"),
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Recursos cacheados
# --------------------------------------------------------------------------- #

def huella_del_corpus() -> str:
    """Resume el contenido de `data/` para usarlo como clave de caché.

    Vive aquí, y no en `src/`, a propósito. Streamlit Cloud vuelve a ejecutar
    `app.py` cuando cambia el repositorio, pero conserva en `sys.modules` los
    módulos de `src` ya importados: si este archivo importara una función
    recién añadida a `src/`, se encontraría con la versión antigua del módulo y
    fallaría con `ImportError` hasta que alguien reiniciase la app a mano.
    Al definirla en el propio script que Streamlit recarga, el despliegue se
    recupera solo.
    """
    digest = hashlib.sha256()

    for ruta in sorted(DIRECTORIO_DATOS.glob("*")):
        if ruta.suffix.lower() not in {".pdf", ".csv"}:
            continue
        estado = ruta.stat()
        digest.update(ruta.name.encode("utf-8"))
        digest.update(str(estado.st_size).encode("utf-8"))

    return digest.hexdigest()[:16]


@st.cache_resource(show_spinner=False)
def cargar_base_de_conocimiento(huella: str) -> BaseDeConocimiento:
    """Lee los documentos y construye el índice vectorial una sola vez.

    `huella` no se usa dentro de la función: es la clave de caché. Sin ella, un
    cambio en `data/` seguiría sirviendo el índice construido con la versión
    anterior de los documentos.
    """
    return BaseDeConocimiento.construir()


def obtener_agente() -> AgenteVidaSana:
    """Un agente por sesión de usuario, sobre el índice compartido."""
    if "agente" not in st.session_state:
        base = cargar_base_de_conocimiento(huella_del_corpus())
        st.session_state.agente = AgenteVidaSana(base=base)
    return st.session_state.agente


# --------------------------------------------------------------------------- #
# Arranque
# --------------------------------------------------------------------------- #

try:
    with st.spinner("Indexando la documentación de la clínica..."):
        agente = obtener_agente()
except Exception as error:  # noqa: BLE001 - se muestra al usuario final
    st.error(
        "**No se pudo iniciar el agente.**\n\n"
        f"{error}\n\n"
        "Verifica que la variable `GEMINI_API_KEY` esté configurada en el archivo "
        "`.env` (ejecución local) o en los *Secrets* de Streamlit Cloud (producción)."
    )
    st.stop()

st.session_state.setdefault("mensajes", [])
st.session_state.setdefault("pregunta_pendiente", None)


st.markdown(
    encabezado_html(
        titulo="Asistente VidaSana",
        subtitulo=(
            f"Agente de IA que responde consultas sobre la documentación oficial "
            f"de {NOMBRE_CLINICA}."
        ),
        chips=[
            (f"{agente.total_fragmentos} fragmentos indexados", True),
            (f"{len(agente.documentos_indexados)} documentos", False),
            ("RAG + function calling", False),
            ("Respuesta en streaming", False),
            ("Google Gemini", False),
        ],
    ),
    unsafe_allow_html=True,
)
st.markdown(AVISO_HTML, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Barra lateral
# --------------------------------------------------------------------------- #

def dibujar_mensaje_usuario(texto: str) -> None:
    """Pinta la burbuja del usuario con el marcador que engancha el estilo.

    El texto se escapa porque se renderiza con HTML habilitado: sin ello,
    cualquiera podría escribir etiquetas en el chat de la aplicación pública.
    """
    st.markdown(
        f'<span class="vs-marca-usuario"></span>{html.escape(texto)}',
        unsafe_allow_html=True,
    )


ETIQUETAS_HERRAMIENTA = {
    "buscar_en_documentos": "Búsqueda semántica en las políticas",
    "consultar_catalogo": "Consulta estructurada al catálogo",
    "listar_especialidades": "Lectura del catálogo completo",
}


def dibujar_traza(traza: list[dict]) -> None:
    """Muestra qué herramienta se usó y con qué confianza se citó cada fuente."""
    with st.expander("🔍 Cómo se obtuvo esta respuesta"):
        for indice, paso in enumerate(traza):
            etiqueta = ETIQUETAS_HERRAMIENTA.get(paso["herramienta"], "Herramienta")
            st.markdown(
                paso_html(f"<b>{etiqueta}</b> · <code>{paso['herramienta']}</code>"),
                unsafe_allow_html=True,
            )
            if paso["argumentos"]:
                st.json(paso["argumentos"], expanded=False)
            st.markdown(fuentes_html(paso["fuentes"]), unsafe_allow_html=True)
            if indice < len(traza) - 1:
                st.markdown("")


def responder_en_vivo(pregunta: str):
    """Consume el flujo del agente pintando su progreso en tiempo real.

    Se usan dos marcadores: uno para los pasos del agente, que se reescribe a
    medida que avanza, y otro para la respuesta, que crece token a token con un
    cursor de escritura hasta que el flujo termina.
    """
    hueco_pasos = st.empty()
    hueco_texto = st.empty()

    pasos: list[str] = []
    texto = ""
    respuesta = None

    for evento in agente.preguntar_en_streaming(pregunta):
        if evento.tipo == "razonando":
            # La primera vuelta decide qué herramienta usar; las siguientes ya
            # trabajan sobre lo recuperado.
            pasos.append(
                "<b>Analizando la consulta</b>"
                if evento.dato == 1
                else "<b>Integrando la información recuperada</b>"
            )
        elif evento.tipo == "herramienta":
            nombre, _ = evento.dato
            etiqueta = ETIQUETAS_HERRAMIENTA.get(nombre, "Herramienta")
            pasos.append(f"<b>{etiqueta}</b> · <code>{nombre}</code>")
        elif evento.tipo == "fuentes":
            cantidad = len(evento.dato)
            plural = "s" if cantidad != 1 else ""
            pasos.append(f"<b>{cantidad}</b> documento{plural} recuperado{plural}")
        elif evento.tipo == "esperando":
            pasos.append(
                f"<b>Límite de peticiones alcanzado</b> · reintentando en {evento.dato:.0f} s"
            )
        elif evento.tipo == "texto":
            texto += evento.dato
            hueco_texto.markdown(texto + '<span class="vs-cursor"></span>', unsafe_allow_html=True)
        elif evento.tipo == "fin":
            respuesta = evento.dato

        if evento.tipo in {"razonando", "herramienta", "fuentes", "esperando"}:
            hueco_pasos.markdown(
                '<div class="vs-pasos">'
                + "".join(paso_html(p, activo=(i == len(pasos) - 1)) for i, p in enumerate(pasos))
                + "</div>",
                unsafe_allow_html=True,
            )

    hueco_pasos.empty()
    hueco_texto.markdown(texto or "")
    return respuesta


with st.sidebar:
    st.toggle("🌙 Modo oscuro", key="tema_oscuro")

    st.divider()

    st.subheader("Sobre este agente")
    st.markdown(
        "Responde únicamente con base en la documentación interna de la clínica: "
        "**5 documentos PDF** de políticas y procedimientos más un **catálogo CSV** "
        "de especialidades y tarifas."
    )

    columna_a, columna_b = st.columns(2)
    columna_a.metric("Fragmentos", agente.total_fragmentos)
    columna_b.metric("Documentos", len(agente.documentos_indexados))

    with st.expander("Ver base de conocimiento"):
        for documento in agente.documentos_indexados:
            st.markdown(f"- {documento}")

    st.divider()

    st.subheader("Preguntas de ejemplo")
    for indice, pregunta in enumerate(PREGUNTAS_DE_EJEMPLO):
        if st.button(pregunta, key=f"ejemplo_{indice}", use_container_width=True):
            st.session_state.pregunta_pendiente = pregunta
            st.rerun()

    st.divider()

    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.mensajes = []
        agente.reiniciar()
        st.rerun()

    st.markdown(PIE_HTML, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Historial de la conversación
# --------------------------------------------------------------------------- #

if not st.session_state.mensajes:
    st.info(
        "👋 Hola, soy el Asistente VidaSana. Puedo ayudarte con horarios, tarifas, "
        "coberturas de seguros, preparación de exámenes y políticas de la clínica. "
        "Escribe tu consulta o elige un ejemplo de la barra lateral."
    )

for mensaje in st.session_state.mensajes:
    es_usuario = mensaje["rol"] == "user"
    with st.chat_message(mensaje["rol"], avatar="🙋" if es_usuario else "🩺"):
        if es_usuario:
            dibujar_mensaje_usuario(mensaje["texto"])
        else:
            st.markdown(mensaje["texto"])
            if mensaje.get("traza"):
                dibujar_traza(mensaje["traza"])


# --------------------------------------------------------------------------- #
# Entrada del usuario
# --------------------------------------------------------------------------- #

pregunta = st.chat_input("Escribe tu consulta sobre la clínica...")
if st.session_state.pregunta_pendiente:
    pregunta = st.session_state.pregunta_pendiente
    st.session_state.pregunta_pendiente = None

if pregunta:
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user", avatar="🙋"):
        dibujar_mensaje_usuario(pregunta)

    with st.chat_message("assistant", avatar="🩺"):
        try:
            respuesta = responder_en_vivo(pregunta)
        except Exception as error:  # noqa: BLE001
            st.error(f"Ocurrió un error al consultar el modelo: {error}")
            st.stop()

        traza = [
            {
                "herramienta": uso.herramienta,
                "argumentos": uso.argumentos,
                "fuentes": uso.fuentes,
            }
            for uso in respuesta.herramientas_usadas
        ]
        if traza:
            dibujar_traza(traza)

    st.session_state.mensajes.append(
        {"rol": "assistant", "texto": respuesta.texto, "traza": traza}
    )
