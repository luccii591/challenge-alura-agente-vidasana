"""Lectura y fragmentación de la base documental de VidaSana.

Este módulo cubre la primera etapa del challenge: leer y procesar los
documentos fuente (PDF y CSV) para convertirlos en fragmentos indexables.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from src.config import (
    DIRECTORIO_DATOS,
    RUTA_CSV,
    SOLAPAMIENTO_FRAGMENTO,
    TAMANO_FRAGMENTO,
)


@dataclass
class Fragmento:
    """Unidad mínima de conocimiento que el agente puede recuperar y citar."""

    texto: str
    documento: str
    pagina: int | None = None
    metadatos: dict = field(default_factory=dict)

    @property
    def cita(self) -> str:
        if self.pagina is not None:
            return f"{self.documento} (pág. {self.pagina})"
        return self.documento


# --------------------------------------------------------------------------- #
# Normalización y fragmentación
# --------------------------------------------------------------------------- #

def limpiar_texto(texto: str) -> str:
    """Colapsa espacios y saltos de línea que introduce la extracción de PDF."""
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"-\n(?=[a-záéíóúñ])", "", texto)  # une palabras cortadas
    texto = re.sub(r"\s*\n\s*", " ", texto)
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    return texto.strip()


def dividir_en_fragmentos(
    texto: str,
    tamano: int = TAMANO_FRAGMENTO,
    solapamiento: int = SOLAPAMIENTO_FRAGMENTO,
) -> list[str]:
    """Divide un texto largo respetando los límites de oración.

    Se acumulan oraciones completas hasta acercarse a `tamano` caracteres. Al
    cerrar un fragmento se arrastran las últimas oraciones como `solapamiento`,
    de modo que una idea partida entre dos fragmentos siga siendo recuperable.
    """
    texto = texto.strip()
    if not texto:
        return []
    if len(texto) <= tamano:
        return [texto]

    oraciones = re.split(r"(?<=[.:;!?])\s+", texto)
    fragmentos: list[str] = []
    actual: list[str] = []
    largo_actual = 0

    for oracion in oraciones:
        if largo_actual + len(oracion) > tamano and actual:
            fragmentos.append(" ".join(actual).strip())

            cola: list[str] = []
            largo_cola = 0
            for previa in reversed(actual):
                if largo_cola + len(previa) > solapamiento:
                    break
                cola.insert(0, previa)
                largo_cola += len(previa)

            actual = cola
            largo_actual = largo_cola

        actual.append(oracion)
        largo_actual += len(oracion)

    if actual:
        fragmentos.append(" ".join(actual).strip())

    return [f for f in fragmentos if len(f) > 40]


# --------------------------------------------------------------------------- #
# Carga de PDFs
# --------------------------------------------------------------------------- #

def _nombre_legible(ruta: Path) -> str:
    """`01_Politica_de_Cancelaciones.pdf` -> `Politica de Cancelaciones`."""
    nombre = ruta.stem
    nombre = re.sub(r"^\d+[_-]", "", nombre)
    return nombre.replace("_", " ").strip()


def cargar_pdf(ruta: Path) -> list[Fragmento]:
    """Extrae el texto de un PDF y lo devuelve fragmentado por página."""
    lector = PdfReader(str(ruta))
    documento = _nombre_legible(ruta)
    fragmentos: list[Fragmento] = []

    for numero_pagina, pagina in enumerate(lector.pages, start=1):
        texto = limpiar_texto(pagina.extract_text() or "")
        for trozo in dividir_en_fragmentos(texto):
            fragmentos.append(
                Fragmento(
                    texto=trozo,
                    documento=documento,
                    pagina=numero_pagina,
                    metadatos={"tipo": "pdf", "archivo": ruta.name},
                )
            )

    return fragmentos


# --------------------------------------------------------------------------- #
# Carga del CSV
# --------------------------------------------------------------------------- #

def cargar_csv(ruta: Path = RUTA_CSV) -> pd.DataFrame:
    """Devuelve el catálogo de especialidades como DataFrame."""
    return pd.read_csv(ruta)


def csv_a_fragmentos(df: pd.DataFrame, nombre_documento: str = "Catálogo de especialidades y tarifas") -> list[Fragmento]:
    """Convierte cada fila del CSV en una oración indexable.

    Permite que preguntas en lenguaje natural ("¿quién ve cardiología en Surco?")
    también encuentren respuesta por vía semántica, además de la consulta
    estructurada con pandas que expone la herramienta `consultar_catalogo`.
    """
    fragmentos: list[Fragmento] = []

    for _, fila in df.iterrows():
        texto = (
            f"Especialidad: {fila['especialidad']}. "
            f"Profesional: {fila['profesional']}. "
            f"Sede: {fila['sede']}. "
            f"Días de atención: {fila['dias_atencion']}, horario {fila['horario']}. "
            f"Duración de la consulta: {fila['duracion_min']} minutos. "
            f"Tarifa particular: S/ {fila['tarifa_particular_pen']}. "
            f"Tarifa con membresía VidaSana Plus: S/ {fila['tarifa_vidasana_plus_pen']}. "
            f"¿Requiere orden médica?: {fila['requiere_orden_medica']}. "
            f"¿Acepta teleconsulta?: {fila['acepta_teleconsulta']}. "
            f"Seguros aceptados: {fila['seguros_aceptados']}."
        )
        fragmentos.append(
            Fragmento(
                texto=texto,
                documento=nombre_documento,
                metadatos={
                    "tipo": "csv",
                    "archivo": RUTA_CSV.name,
                    "especialidad": fila["especialidad"],
                    "sede": fila["sede"],
                },
            )
        )

    return fragmentos


# --------------------------------------------------------------------------- #
# Punto de entrada del módulo
# --------------------------------------------------------------------------- #

def huella_del_corpus(directorio: Path = DIRECTORIO_DATOS) -> str:
    """Devuelve una huella del contenido de `data/`.

    Sirve como clave de caché del índice vectorial. Streamlit puede recargar el
    código de la aplicación sin reiniciar el proceso, y en ese caso un
    `@st.cache_resource` sin clave seguiría sirviendo un índice construido con
    documentos ya obsoletos. Al depender de esta huella, el índice se reconstruye
    solo cuando la base documental realmente cambia.
    """
    digest = hashlib.sha256()

    for ruta in sorted(directorio.glob("*")):
        if ruta.suffix.lower() not in {".pdf", ".csv"}:
            continue
        estado = ruta.stat()
        digest.update(ruta.name.encode("utf-8"))
        digest.update(str(estado.st_size).encode("utf-8"))
        digest.update(str(int(estado.st_mtime)).encode("utf-8"))

    return digest.hexdigest()[:16]


def cargar_corpus(directorio: Path = DIRECTORIO_DATOS) -> list[Fragmento]:
    """Carga todos los PDFs y el CSV de `data/` en una única lista de fragmentos."""
    fragmentos: list[Fragmento] = []

    for ruta_pdf in sorted(directorio.glob("*.pdf")):
        fragmentos.extend(cargar_pdf(ruta_pdf))

    if RUTA_CSV.exists():
        fragmentos.extend(csv_a_fragmentos(cargar_csv()))

    if not fragmentos:
        raise FileNotFoundError(
            f"No se encontraron documentos en {directorio}. "
            "Ejecuta `python scripts/generar_documentos.py` para crearlos."
        )

    return fragmentos
