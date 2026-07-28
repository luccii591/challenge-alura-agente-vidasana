"""Orquestación del agente: bucle de razonamiento con function calling.

El flujo de una consulta es:

    pregunta -> modelo decide herramienta -> se ejecuta -> el resultado vuelve
    al modelo -> (repetir si hace falta) -> respuesta final citando fuentes

El bucle es explícito a propósito: permite limitar las iteraciones, registrar la
traza de herramientas usadas y mostrarla en la interfaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from google import genai
from google.genai import types

from src.config import (
    MAX_ITERACIONES_AGENTE,
    MODELO_CHAT,
    PRESUPUESTO_RAZONAMIENTO,
    TEMPERATURA,
    obtener_api_key,
)
from src.loaders import cargar_corpus, cargar_csv
from src.prompts import INSTRUCCION_SISTEMA
from src.resiliencia import llamar_con_reintentos
from src.tools import DECLARACIONES, CajaDeHerramientas, RegistroDeUso, serializar
from src.vectorstore import IndiceVectorial


@dataclass
class Respuesta:
    """Respuesta final del agente junto con su traza de ejecución."""

    texto: str
    herramientas_usadas: list[RegistroDeUso] = field(default_factory=list)
    iteraciones: int = 0

    @property
    def fuentes(self) -> list[str]:
        vistas: list[str] = []
        for uso in self.herramientas_usadas:
            for fuente in uso.fuentes:
                if fuente not in vistas:
                    vistas.append(fuente)
        return vistas


@dataclass
class BaseDeConocimiento:
    """Recursos costosos de construir: cliente, índice vectorial y catálogo.

    Se separan del agente para poder cachearlos una sola vez por proceso (en
    Streamlit, con `@st.cache_resource`) y crear agentes ligeros por sesión.
    """

    cliente: genai.Client
    indice: IndiceVectorial
    catalogo: pd.DataFrame

    @classmethod
    def construir(cls, api_key: str | None = None) -> "BaseDeConocimiento":
        cliente = genai.Client(api_key=api_key or obtener_api_key())
        indice = IndiceVectorial(cliente).construir(cargar_corpus())
        return cls(cliente=cliente, indice=indice, catalogo=cargar_csv())


class AgenteVidaSana:
    """Agente conversacional sobre la base documental de la clínica."""

    def __init__(
        self,
        api_key: str | None = None,
        base: BaseDeConocimiento | None = None,
    ) -> None:
        base = base or BaseDeConocimiento.construir(api_key)

        self.cliente = base.cliente
        self.indice = base.indice
        self.catalogo = base.catalogo
        self.herramientas = CajaDeHerramientas(self.indice, self.catalogo)

        extras = {}
        if PRESUPUESTO_RAZONAMIENTO is not None:
            extras["thinking_config"] = types.ThinkingConfig(
                thinking_budget=PRESUPUESTO_RAZONAMIENTO
            )

        self.configuracion = types.GenerateContentConfig(
            system_instruction=INSTRUCCION_SISTEMA,
            tools=[types.Tool(function_declarations=DECLARACIONES)],
            temperature=TEMPERATURA,
            # El bucle de herramientas se controla manualmente para poder
            # registrar la traza y limitar las iteraciones.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            **extras,
        )

        self.historial: list[types.Content] = []

    # ------------------------------------------------------------------ #
    # Información de arranque
    # ------------------------------------------------------------------ #

    @property
    def total_fragmentos(self) -> int:
        return len(self.indice)

    @property
    def documentos_indexados(self) -> list[str]:
        vistos: list[str] = []
        for fragmento in self.indice.fragmentos:
            if fragmento.documento not in vistos:
                vistos.append(fragmento.documento)
        return vistos

    # ------------------------------------------------------------------ #
    # Conversación
    # ------------------------------------------------------------------ #

    def reiniciar(self) -> None:
        """Borra el historial de la conversación (el índice se conserva)."""
        self.historial = []

    def preguntar(self, pregunta: str) -> Respuesta:
        """Ejecuta el bucle del agente hasta obtener una respuesta en texto."""
        self.herramientas.reiniciar_traza()
        self.historial.append(
            types.Content(role="user", parts=[types.Part.from_text(text=pregunta)])
        )

        for iteracion in range(1, MAX_ITERACIONES_AGENTE + 1):
            respuesta = llamar_con_reintentos(
                lambda: self.cliente.models.generate_content(
                    model=MODELO_CHAT,
                    contents=self.historial,
                    config=self.configuracion,
                ),
                descripcion="el modelo de chat",
            )

            candidato = respuesta.candidates[0] if respuesta.candidates else None
            contenido = candidato.content if candidato else None
            partes = list(contenido.parts) if contenido and contenido.parts else []

            llamadas = [p.function_call for p in partes if p.function_call]

            # Sin llamadas a herramientas: el modelo ya tiene la respuesta final.
            if not llamadas:
                texto = (respuesta.text or "").strip()
                if contenido is not None:
                    self.historial.append(contenido)
                return Respuesta(
                    texto=texto or "No pude generar una respuesta. Intenta reformular tu pregunta.",
                    herramientas_usadas=list(self.herramientas.usos),
                    iteraciones=iteracion,
                )

            # Hay llamadas: se ejecutan y sus resultados se devuelven al modelo.
            self.historial.append(contenido)

            partes_resultado = []
            for llamada in llamadas:
                resultado = self.herramientas.ejecutar(llamada.name, dict(llamada.args or {}))
                partes_resultado.append(
                    types.Part.from_function_response(
                        name=llamada.name,
                        response={"resultado": serializar(resultado)},
                    )
                )

            self.historial.append(types.Content(role="user", parts=partes_resultado))

        return Respuesta(
            texto=(
                "La consulta resultó demasiado compleja y alcancé el límite de pasos. "
                "¿Puedes dividirla en preguntas más específicas?"
            ),
            herramientas_usadas=list(self.herramientas.usos),
            iteraciones=MAX_ITERACIONES_AGENTE,
        )
