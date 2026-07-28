"""Configuración centralizada del Asistente VidaSana.

Todo parámetro ajustable del proyecto (modelos, rutas, tamaños de chunk,
umbrales de recuperación) vive aquí para no dispersar constantes por el código.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
DIRECTORIO_DATOS = RAIZ_PROYECTO / "data"
RUTA_CSV = DIRECTORIO_DATOS / "especialidades_y_tarifas_vidasana.csv"

# --------------------------------------------------------------------------- #
# Modelos de Google Gemini
# --------------------------------------------------------------------------- #

# Los modelos `flash-lite` son los que tienen mayor cuota de peticiones por
# minuto en la capa gratuita, lo que importa porque cada consulta del agente
# gasta varias llamadas (una por cada paso de razonamiento).
MODELO_CHAT = os.getenv("MODELO_CHAT", "gemini-3.5-flash-lite")
MODELO_EMBEDDINGS = os.getenv("MODELO_EMBEDDINGS", "gemini-embedding-001")

# Presupuesto de razonamiento interno. `None` deja el valor por defecto del
# modelo; no todos los modelos aceptan que se fije explícitamente.
PRESUPUESTO_RAZONAMIENTO: int | None = None

# Dimensión de salida de los embeddings. 768 mantiene buena calidad semántica
# con un índice liviano, suficiente para un corpus de este tamaño.
DIMENSION_EMBEDDINGS = 768

# --------------------------------------------------------------------------- #
# Fragmentación (chunking) del corpus documental
# --------------------------------------------------------------------------- #

TAMANO_FRAGMENTO = 900
SOLAPAMIENTO_FRAGMENTO = 150

# --------------------------------------------------------------------------- #
# Recuperación semántica
# --------------------------------------------------------------------------- #

FRAGMENTOS_A_RECUPERAR = 5
UMBRAL_SIMILITUD_MINIMA = 0.35

# --------------------------------------------------------------------------- #
# Comportamiento del agente
# --------------------------------------------------------------------------- #

MAX_ITERACIONES_AGENTE = 6
TEMPERATURA = 0.2

NOMBRE_CLINICA = "Clínica VidaSana"
NOMBRE_AGENTE = "Asistente VidaSana"


def obtener_api_key() -> str:
    """Devuelve la API key de Google Gemini.

    Busca primero en las variables de entorno (uso local con `.env`) y luego en
    `st.secrets`, que es como Streamlit Community Cloud inyecta los secretos.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key

    try:  # Import perezoso: la CLI no depende de Streamlit.
        import streamlit as st

        secreto = st.secrets.get("GEMINI_API_KEY")
        if secreto:
            return secreto
    except Exception:  # pragma: no cover - entorno sin Streamlit o sin secrets
        pass

    raise RuntimeError(
        "No se encontró la API key de Gemini. Define GEMINI_API_KEY en el "
        "archivo .env (local) o en los Secrets de Streamlit Cloud (producción). "
        "Puedes obtener una gratis en https://aistudio.google.com/apikey"
    )
