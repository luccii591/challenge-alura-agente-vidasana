"""Índice vectorial en memoria para la recuperación semántica (RAG).

Con un corpus del tamaño de VidaSana (decenas de fragmentos), una matriz NumPy
con búsqueda por coseno es exacta e instantánea, y evita arrastrar una base
vectorial pesada al deploy. La interfaz es la misma que expondría FAISS o
Chroma, así que cambiar de motor más adelante no obliga a tocar el agente.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from google import genai
from google.genai import types

from src.config import (
    DIMENSION_EMBEDDINGS,
    FRAGMENTOS_A_RECUPERAR,
    MODELO_EMBEDDINGS,
    UMBRAL_SIMILITUD_MINIMA,
)
from src.loaders import Fragmento
from src.resiliencia import llamar_con_reintentos

TAMANO_LOTE_EMBEDDINGS = 32


@dataclass
class Coincidencia:
    """Fragmento recuperado junto con su score de similitud."""

    fragmento: Fragmento
    similitud: float


def _normalizar(matriz: np.ndarray) -> np.ndarray:
    """Normaliza filas a norma 1 para que el producto punto sea el coseno."""
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    normas[normas == 0] = 1e-12
    return matriz / normas


class IndiceVectorial:
    """Almacena los embeddings del corpus y resuelve búsquedas por similitud."""

    def __init__(self, cliente: genai.Client) -> None:
        self.cliente = cliente
        self.fragmentos: list[Fragmento] = []
        self.matriz: np.ndarray | None = None

    # ------------------------------------------------------------------ #
    # Construcción del índice
    # ------------------------------------------------------------------ #

    def _incrustar(self, textos: list[str], tipo_tarea: str) -> np.ndarray:
        """Llama a la API de embeddings en lotes y devuelve la matriz resultante."""
        vectores: list[list[float]] = []

        for inicio in range(0, len(textos), TAMANO_LOTE_EMBEDDINGS):
            lote = textos[inicio : inicio + TAMANO_LOTE_EMBEDDINGS]
            respuesta = llamar_con_reintentos(
                lambda lote=lote: self.cliente.models.embed_content(
                    model=MODELO_EMBEDDINGS,
                    contents=lote,
                    config=types.EmbedContentConfig(
                        task_type=tipo_tarea,
                        output_dimensionality=DIMENSION_EMBEDDINGS,
                    ),
                ),
                descripcion="el modelo de embeddings",
            )
            vectores.extend(dato.values for dato in respuesta.embeddings)

        return _normalizar(np.array(vectores, dtype=np.float32))

    def construir(self, fragmentos: list[Fragmento]) -> "IndiceVectorial":
        """Vectoriza el corpus completo. Se ejecuta una sola vez por sesión."""
        self.fragmentos = fragmentos
        self.matriz = self._incrustar(
            [f.texto for f in fragmentos],
            tipo_tarea="RETRIEVAL_DOCUMENT",
        )
        return self

    # ------------------------------------------------------------------ #
    # Consulta
    # ------------------------------------------------------------------ #

    def buscar(
        self,
        consulta: str,
        k: int = FRAGMENTOS_A_RECUPERAR,
        umbral: float = UMBRAL_SIMILITUD_MINIMA,
    ) -> list[Coincidencia]:
        """Devuelve los `k` fragmentos más parecidos a la consulta."""
        if self.matriz is None:
            raise RuntimeError("El índice no ha sido construido todavía.")

        vector_consulta = self._incrustar([consulta], tipo_tarea="RETRIEVAL_QUERY")[0]
        similitudes = self.matriz @ vector_consulta

        mejores = np.argsort(similitudes)[::-1][:k]
        resultados = [
            Coincidencia(fragmento=self.fragmentos[i], similitud=float(similitudes[i]))
            for i in mejores
            if similitudes[i] >= umbral
        ]

        # Si nada supera el umbral devolvemos igualmente el mejor candidato: es
        # preferible que el modelo vea contexto débil y admita no saber, a que
        # responda sin ninguna fuente.
        if not resultados and len(mejores):
            mejor = mejores[0]
            resultados = [
                Coincidencia(
                    fragmento=self.fragmentos[mejor],
                    similitud=float(similitudes[mejor]),
                )
            ]

        return resultados

    def __len__(self) -> int:
        return len(self.fragmentos)
