"""Interfaz web del Asistente VidaSana (Streamlit).

    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.agent import AgenteVidaSana, BaseDeConocimiento
from src.config import NOMBRE_AGENTE, NOMBRE_CLINICA
from src.prompts import PREGUNTAS_DE_EJEMPLO

st.set_page_config(
    page_title=f"{NOMBRE_AGENTE} | Agente de IA",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Recursos cacheados
# --------------------------------------------------------------------------- #

@st.cache_resource(show_spinner=False)
def cargar_base_de_conocimiento() -> BaseDeConocimiento:
    """Lee los documentos y construye el índice vectorial una sola vez."""
    return BaseDeConocimiento.construir()


def obtener_agente() -> AgenteVidaSana:
    """Un agente por sesión de usuario, sobre el índice compartido."""
    if "agente" not in st.session_state:
        st.session_state.agente = AgenteVidaSana(base=cargar_base_de_conocimiento())
    return st.session_state.agente


# --------------------------------------------------------------------------- #
# Arranque
# --------------------------------------------------------------------------- #

st.title("🩺 Asistente VidaSana")
st.caption(
    f"Agente de IA que responde consultas sobre la documentación oficial de {NOMBRE_CLINICA}."
)
st.caption(
    "⚠️ **Proyecto académico.** Clínica VidaSana es una empresa ficticia y toda la "
    "documentación es material de demostración. Los nombres, precios, direcciones y "
    "teléfonos son inventados: no corresponden a ningún establecimiento de salud real "
    "ni deben usarse para tomar decisiones médicas o administrativas."
)

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

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = None


# --------------------------------------------------------------------------- #
# Barra lateral
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.header("Sobre este agente")
    st.markdown(
        "Responde únicamente con base en la documentación interna de la clínica: "
        "**5 documentos PDF** de políticas y procedimientos más un **catálogo CSV** "
        "de especialidades y tarifas."
    )

    st.metric("Fragmentos indexados", agente.total_fragmentos)

    with st.expander("Documentos en la base de conocimiento"):
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

    st.caption("Challenge Alura Agente · ONE — Tech AI Builder")


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
    with st.chat_message(mensaje["rol"], avatar="🩺" if mensaje["rol"] == "assistant" else None):
        st.markdown(mensaje["texto"])
        if mensaje.get("traza"):
            with st.expander("🔍 Cómo se obtuvo esta respuesta"):
                for paso in mensaje["traza"]:
                    st.markdown(f"**Herramienta:** `{paso['herramienta']}`")
                    if paso["argumentos"]:
                        st.json(paso["argumentos"], expanded=False)
                    for fuente in paso["fuentes"]:
                        st.markdown(f"📄 {fuente}")
                    st.markdown("---")


# --------------------------------------------------------------------------- #
# Entrada del usuario
# --------------------------------------------------------------------------- #

pregunta = st.chat_input("Escribe tu consulta sobre la clínica...")
if st.session_state.pregunta_pendiente:
    pregunta = st.session_state.pregunta_pendiente
    st.session_state.pregunta_pendiente = None

if pregunta:
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner("Consultando la documentación..."):
            try:
                respuesta = agente.preguntar(pregunta)
            except Exception as error:  # noqa: BLE001
                st.error(f"Ocurrió un error al consultar el modelo: {error}")
                st.stop()

        st.markdown(respuesta.texto)

        traza = [
            {
                "herramienta": uso.herramienta,
                "argumentos": uso.argumentos,
                "fuentes": uso.fuentes,
            }
            for uso in respuesta.herramientas_usadas
        ]

        if traza:
            with st.expander("🔍 Cómo se obtuvo esta respuesta"):
                for paso in traza:
                    st.markdown(f"**Herramienta:** `{paso['herramienta']}`")
                    if paso["argumentos"]:
                        st.json(paso["argumentos"], expanded=False)
                    for fuente in paso["fuentes"]:
                        st.markdown(f"📄 {fuente}")
                    st.markdown("---")

    st.session_state.mensajes.append(
        {"rol": "assistant", "texto": respuesta.texto, "traza": traza}
    )
