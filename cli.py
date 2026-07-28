"""Interfaz de línea de comandos del Asistente VidaSana.

    python cli.py                                  # modo conversacional
    python cli.py "¿Cuánto cuesta cardiología?"    # pregunta única
"""

from __future__ import annotations

import sys

from src.agent import AgenteVidaSana
from src.config import NOMBRE_AGENTE, NOMBRE_CLINICA
from src.prompts import PREGUNTAS_DE_EJEMPLO


def _imprimir_respuesta(respuesta) -> None:
    print(f"\n{respuesta.texto}\n")
    if respuesta.herramientas_usadas:
        detalle = ", ".join(uso.herramienta for uso in respuesta.herramientas_usadas)
        print(f"  [herramientas: {detalle} | pasos: {respuesta.iteraciones}]")
    print()


def main() -> None:
    print(f"Iniciando {NOMBRE_AGENTE}: indexando la documentación de {NOMBRE_CLINICA}...")
    agente = AgenteVidaSana()
    print(
        f"Listo. {agente.total_fragmentos} fragmentos indexados "
        f"de {len(agente.documentos_indexados)} documentos.\n"
    )

    if len(sys.argv) > 1:
        pregunta = " ".join(sys.argv[1:])
        print(f"Tú: {pregunta}")
        _imprimir_respuesta(agente.preguntar(pregunta))
        return

    print("Escribe tu consulta. Usa 'salir' para terminar.")
    print("Preguntas de ejemplo:")
    for pregunta in PREGUNTAS_DE_EJEMPLO[:4]:
        print(f"  - {pregunta}")
    print()

    while True:
        try:
            pregunta = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            return

        if not pregunta:
            continue
        if pregunta.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            return

        _imprimir_respuesta(agente.preguntar(pregunta))


if __name__ == "__main__":
    main()
