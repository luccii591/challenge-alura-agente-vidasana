"""Reintentos con espera exponencial para las llamadas a la API de Gemini.

La capa gratuita de Gemini limita las peticiones por minuto. Como cada consulta
del agente puede gastar varias llamadas (una por cada paso de razonamiento), sin
reintentos la aplicación desplegada fallaría ante un pico de uso. Este módulo
absorbe esos errores transitorios de forma transparente.
"""

from __future__ import annotations

import random
import re
import time
from typing import Callable, TypeVar

T = TypeVar("T")

MAX_REINTENTOS = 4
ESPERA_BASE = 2.0
ESPERA_MAXIMA = 45.0

# Errores que tiene sentido reintentar: cuota agotada y fallos temporales del servicio.
CODIGOS_REINTENTABLES = (429, 500, 502, 503, 504)


def _espera_sugerida(mensaje: str) -> float | None:
    """Extrae el `retryDelay` que la propia API sugiere, si viene en el error."""
    coincidencia = re.search(r"'retryDelay':\s*'(\d+(?:\.\d+)?)s'", mensaje)
    if coincidencia:
        return float(coincidencia.group(1))

    coincidencia = re.search(r"retry in (\d+(?:\.\d+)?)s", mensaje)
    if coincidencia:
        return float(coincidencia.group(1))

    return None


def es_reintentable(error: Exception) -> bool:
    """Indica si el error es transitorio y merece otro intento."""
    codigo = getattr(error, "code", None) or getattr(error, "status_code", None)
    if codigo in CODIGOS_REINTENTABLES:
        return True
    return any(str(c) in str(error)[:80] for c in CODIGOS_REINTENTABLES)


def calcular_espera(error: Exception, intento: int) -> float:
    """Segundos a esperar antes del siguiente intento.

    Da prioridad al `retryDelay` que sugiere la propia API y añade *jitter*
    para que varios usuarios simultáneos no reintenten todos a la vez.
    """
    espera = _espera_sugerida(str(error))
    if espera is None:
        espera = ESPERA_BASE * (2 ** (intento - 1))
    return min(espera + random.uniform(0, 1.5), ESPERA_MAXIMA)


def llamar_con_reintentos(operacion: Callable[[], T], descripcion: str = "la API") -> T:
    """Ejecuta `operacion`, reintentando ante errores transitorios de la API."""
    ultimo_error: Exception | None = None

    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            return operacion()
        except Exception as error:  # noqa: BLE001 - se reclasifica más abajo
            ultimo_error = error

            if not es_reintentable(error) or intento == MAX_REINTENTOS:
                raise

            time.sleep(calcular_espera(error, intento))

    raise RuntimeError(f"No se pudo completar la llamada a {descripcion}.") from ultimo_error
