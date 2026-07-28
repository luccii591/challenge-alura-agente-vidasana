"""Herramientas que el agente puede invocar (function calling).

El agente no recibe todo el corpus en el prompt: decide por sí mismo qué
herramienta usar según la pregunta. Hay dos vías de acceso al conocimiento:

* `buscar_en_documentos` — búsqueda semántica sobre los PDFs de políticas.
* `consultar_catalogo` / `listar_especialidades` — consulta estructurada con
  pandas sobre el CSV, que responde con exactitud cosas como precios o filtros
  por sede, donde la búsqueda semántica sería imprecisa.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from google.genai import types

from src.vectorstore import IndiceVectorial


@dataclass
class RegistroDeUso:
    """Traza de una invocación de herramienta, para mostrarla en la interfaz."""

    herramienta: str
    argumentos: dict
    fuentes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Declaraciones expuestas al modelo
# --------------------------------------------------------------------------- #

DECLARACIONES = [
    types.FunctionDeclaration(
        name="buscar_en_documentos",
        description=(
            "Busca información en los documentos oficiales de la clínica: política de "
            "privacidad y datos del paciente, política de cancelaciones y reagendamiento, "
            "guía de convenios y coberturas médicas, instrucciones de preparación pre y "
            "post consulta, y preguntas frecuentes. Úsala para preguntas sobre normas, "
            "plazos, requisitos, procedimientos, preparación de exámenes, seguros, "
            "membresía VidaSana Plus, horarios de sede o cualquier tema explicado en texto."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "consulta": types.Schema(
                    type=types.Type.STRING,
                    description=(
                        "Consulta de búsqueda en español, reformulada de forma completa y "
                        "autocontenida. Ejemplo: 'plazo para cancelar una cita sin penalidad'."
                    ),
                )
            },
            required=["consulta"],
        ),
    ),
    types.FunctionDeclaration(
        name="consultar_catalogo",
        description=(
            "Consulta el catálogo estructurado de especialidades médicas. Devuelve datos "
            "exactos de profesional, sede, días y horario de atención, duración, tarifa "
            "particular en soles, tarifa con membresía VidaSana Plus, si requiere orden "
            "médica, si acepta teleconsulta y qué seguros acepta. Úsala siempre que la "
            "pregunta involucre precios, médicos, sedes o disponibilidad por especialidad."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "especialidad": types.Schema(
                    type=types.Type.STRING,
                    description="Nombre de la especialidad, por ejemplo 'Cardiología'. Opcional.",
                ),
                "sede": types.Schema(
                    type=types.Type.STRING,
                    description="Sede a filtrar: 'San Isidro', 'Miraflores' o 'Surco'. Opcional.",
                ),
                "solo_teleconsulta": types.Schema(
                    type=types.Type.BOOLEAN,
                    description="Si es true, devuelve solo especialidades que aceptan teleconsulta.",
                ),
                "seguro": types.Schema(
                    type=types.Type.STRING,
                    description="Aseguradora a filtrar, por ejemplo 'Rímac' o 'Pacífico'. Opcional.",
                ),
                "ordenar_por": types.Schema(
                    type=types.Type.STRING,
                    description=(
                        "Orden del resultado: 'tarifa_asc' (de menor a mayor precio), "
                        "'tarifa_desc' (de mayor a menor) o 'especialidad'. Opcional."
                    ),
                ),
                "limite": types.Schema(
                    type=types.Type.INTEGER,
                    description="Número máximo de filas a devolver. Por defecto 25.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="listar_especialidades",
        description=(
            "Devuelve la lista completa de especialidades disponibles en la clínica con su "
            "tarifa particular y las sedes donde se atienden. Úsala cuando el paciente "
            "pregunte de forma general qué especialidades hay o no sepa cuál necesita."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
]


# --------------------------------------------------------------------------- #
# Implementación
# --------------------------------------------------------------------------- #

class CajaDeHerramientas:
    """Ejecuta las herramientas declaradas sobre el índice y el catálogo."""

    def __init__(self, indice: IndiceVectorial, catalogo: pd.DataFrame) -> None:
        self.indice = indice
        self.catalogo = catalogo
        self.usos: list[RegistroDeUso] = []

    # -- despachador ---------------------------------------------------- #

    def ejecutar(self, nombre: str, argumentos: dict[str, Any]) -> dict:
        manejadores = {
            "buscar_en_documentos": self._buscar_en_documentos,
            "consultar_catalogo": self._consultar_catalogo,
            "listar_especialidades": self._listar_especialidades,
        }
        manejador = manejadores.get(nombre)
        if manejador is None:
            return {"error": f"La herramienta '{nombre}' no existe."}
        return manejador(**argumentos)

    def reiniciar_traza(self) -> None:
        self.usos = []

    # -- herramienta 1: RAG --------------------------------------------- #

    def _buscar_en_documentos(self, consulta: str) -> dict:
        coincidencias = self.indice.buscar(consulta)
        pasajes = [
            {
                "fuente": c.fragmento.cita,
                "similitud": round(c.similitud, 3),
                "contenido": c.fragmento.texto,
            }
            for c in coincidencias
        ]

        self.usos.append(
            RegistroDeUso(
                herramienta="buscar_en_documentos",
                argumentos={"consulta": consulta},
                fuentes=[p["fuente"] for p in pasajes],
            )
        )
        return {"consulta": consulta, "pasajes": pasajes}

    # -- herramienta 2: consulta estructurada --------------------------- #

    def _consultar_catalogo(
        self,
        especialidad: str | None = None,
        sede: str | None = None,
        solo_teleconsulta: bool | None = None,
        seguro: str | None = None,
        ordenar_por: str | None = None,
        limite: int = 25,
    ) -> dict:
        df = self.catalogo.copy()

        if especialidad:
            df = df[df["especialidad"].str.contains(especialidad, case=False, na=False)]
        if sede:
            df = df[df["sede"].str.contains(sede, case=False, na=False)]
        if solo_teleconsulta:
            df = df[df["acepta_teleconsulta"].str.strip().str.lower() == "sí"]
        if seguro:
            df = df[df["seguros_aceptados"].str.contains(seguro, case=False, na=False)]

        if ordenar_por == "tarifa_asc":
            df = df.sort_values("tarifa_particular_pen")
        elif ordenar_por == "tarifa_desc":
            df = df.sort_values("tarifa_particular_pen", ascending=False)
        elif ordenar_por == "especialidad":
            df = df.sort_values("especialidad")

        df = df.head(max(1, int(limite)))

        self.usos.append(
            RegistroDeUso(
                herramienta="consultar_catalogo",
                argumentos={
                    k: v
                    for k, v in {
                        "especialidad": especialidad,
                        "sede": sede,
                        "solo_teleconsulta": solo_teleconsulta,
                        "seguro": seguro,
                        "ordenar_por": ordenar_por,
                    }.items()
                    if v
                },
                fuentes=["Catálogo de especialidades y tarifas (CSV)"],
            )
        )

        if df.empty:
            return {
                "coincidencias": 0,
                "resultados": [],
                "nota": "No hay registros que cumplan esos filtros en el catálogo.",
            }

        return {"coincidencias": len(df), "resultados": df.to_dict(orient="records")}

    # -- herramienta 3: catálogo resumido ------------------------------- #

    def _listar_especialidades(self) -> dict:
        resumen = (
            self.catalogo.groupby("especialidad")
            .agg(
                tarifa_particular_pen=("tarifa_particular_pen", "min"),
                sedes=("sede", lambda s: ", ".join(sorted(set(s)))),
            )
            .reset_index()
            .sort_values("especialidad")
        )

        self.usos.append(
            RegistroDeUso(
                herramienta="listar_especialidades",
                argumentos={},
                fuentes=["Catálogo de especialidades y tarifas (CSV)"],
            )
        )
        return {
            "total": len(resumen),
            "especialidades": resumen.to_dict(orient="records"),
        }


def serializar(resultado: dict) -> str:
    """Convierte el resultado de una herramienta a JSON legible por el modelo."""
    return json.dumps(resultado, ensure_ascii=False, default=str)
