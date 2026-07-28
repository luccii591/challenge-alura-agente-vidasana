"""Orquestación del agente: bucle de razonamiento con function calling.

El flujo de una consulta es:

    pregunta -> modelo decide herramienta -> se ejecuta -> el resultado vuelve
    al modelo -> (repetir si hace falta) -> respuesta final citando fuentes

El bucle es explícito a propósito: permite limitar las iteraciones, registrar la
traza de herramientas usadas y mostrarla en la interfaz.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
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
from src.resiliencia import MAX_REINTENTOS, calcular_espera, es_reintentable
from src.tools import (
    DECLARACIONES,
    CajaDeHerramientas,
    Fuente,
    RegistroDeUso,
    serializar,
)
from src.vectorstore import IndiceVectorial


@dataclass
class Respuesta:
    """Respuesta final del agente junto con su traza de ejecución."""

    texto: str
    herramientas_usadas: list[RegistroDeUso] = field(default_factory=list)
    iteraciones: int = 0

    @property
    def fuentes(self) -> list[Fuente]:
        """Documentos citados, sin repetir, conservando la mejor confianza."""
        mejores: dict[str, Fuente] = {}
        for uso in self.herramientas_usadas:
            for fuente in uso.fuentes:
                previa = mejores.get(fuente.nombre)
                if previa is None or fuente.confianza > previa.confianza:
                    mejores[fuente.nombre] = fuente
        return list(mejores.values())


@dataclass
class Evento:
    """Suceso emitido mientras el agente resuelve una consulta.

    Permite que la interfaz muestre en vivo qué está haciendo el agente en vez
    de esperar en silencio a la respuesta final.

    Tipos: `razonando` (nueva iteración), `herramienta` (invocación),
    `fuentes` (documentos recuperados), `texto` (fragmento de la respuesta) y
    `fin` (respuesta completa).
    """

    tipo: str
    dato: object = None


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

    def preguntar_en_streaming(self, pregunta: str) -> Iterator[Evento]:
        """Resuelve la consulta emitiendo eventos a medida que ocurren.

        La respuesta final se transmite en fragmentos según los produce el
        modelo, y cada invocación de herramienta se anuncia antes de
        ejecutarse, de modo que la interfaz refleja el razonamiento en vivo.
        """
        self.herramientas.reiniciar_traza()
        self.historial.append(
            types.Content(role="user", parts=[types.Part.from_text(text=pregunta)])
        )

        acumulado: list[str] = []

        for iteracion in range(1, MAX_ITERACIONES_AGENTE + 1):
            yield Evento("razonando", iteracion)

            partes: list[types.Part] = []
            emitido = False

            # `generate_content_stream` devuelve un generador perezoso: la
            # petición HTTP —y por tanto un posible 429 por cuota— ocurre al
            # iterarlo, no al crearlo. Por eso el reintento envuelve el consumo
            # completo del flujo y no la llamada. Solo se reintenta mientras no
            # se haya emitido texto: lo ya mostrado no se puede retirar.
            for intento in range(1, MAX_REINTENTOS + 1):
                partes = []
                try:
                    flujo = self.cliente.models.generate_content_stream(
                        model=MODELO_CHAT,
                        contents=self.historial,
                        config=self.configuracion,
                    )
                    for trozo in flujo:
                        candidato = trozo.candidates[0] if trozo.candidates else None
                        contenido = candidato.content if candidato else None
                        if contenido is None or not contenido.parts:
                            continue

                        for parte in contenido.parts:
                            # El razonamiento interno no es parte de la respuesta.
                            if getattr(parte, "thought", False):
                                continue
                            partes.append(parte)
                            if parte.text:
                                acumulado.append(parte.text)
                                emitido = True
                                yield Evento("texto", parte.text)
                    break
                except Exception as error:  # noqa: BLE001 - se reclasifica aquí
                    if emitido or not es_reintentable(error) or intento == MAX_REINTENTOS:
                        raise
                    espera = calcular_espera(error, intento)
                    yield Evento("esperando", espera)
                    time.sleep(espera)

            llamadas = [p.function_call for p in partes if p.function_call]
            self.historial.append(types.Content(role="model", parts=partes))

            # Sin llamadas a herramientas: el modelo ya dio la respuesta final.
            if not llamadas:
                texto = "".join(acumulado).strip()
                yield Evento(
                    "fin",
                    Respuesta(
                        texto=texto
                        or "No pude generar una respuesta. Intenta reformular tu pregunta.",
                        herramientas_usadas=list(self.herramientas.usos),
                        iteraciones=iteracion,
                    ),
                )
                return

            partes_resultado = []
            for llamada in llamadas:
                argumentos = dict(llamada.args or {})
                yield Evento("herramienta", (llamada.name, argumentos))

                resultado = self.herramientas.ejecutar(llamada.name, argumentos)
                if self.herramientas.usos:
                    yield Evento("fuentes", self.herramientas.usos[-1].fuentes)

                partes_resultado.append(
                    types.Part.from_function_response(
                        name=llamada.name,
                        response={"resultado": serializar(resultado)},
                    )
                )

            self.historial.append(types.Content(role="user", parts=partes_resultado))

        yield Evento(
            "fin",
            Respuesta(
                texto=(
                    "La consulta resultó demasiado compleja y alcancé el límite de pasos. "
                    "¿Puedes dividirla en preguntas más específicas?"
                ),
                herramientas_usadas=list(self.herramientas.usos),
                iteraciones=MAX_ITERACIONES_AGENTE,
            ),
        )

    def preguntar(self, pregunta: str) -> Respuesta:
        """Versión síncrona: consume el flujo y devuelve la respuesta final."""
        ultima: Respuesta | None = None
        for evento in self.preguntar_en_streaming(pregunta):
            if evento.tipo == "fin":
                ultima = evento.dato  # type: ignore[assignment]
        return ultima or Respuesta(texto="No se obtuvo respuesta del agente.")
