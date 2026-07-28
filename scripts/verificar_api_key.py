"""Comprueba que la API key de Gemini está bien configurada y funciona.

    python scripts/verificar_api_key.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MODELO_CHAT, MODELO_EMBEDDINGS  # noqa: E402


def main() -> int:
    print("1/4  Leyendo la API key...")
    try:
        from src.config import obtener_api_key

        api_key = obtener_api_key()
    except RuntimeError as error:
        print(f"     ERROR: {error}")
        return 1

    if api_key.strip() in {"", "PEGA_AQUI_TU_API_KEY", "tu_api_key_de_google_gemini"}:
        print("     ERROR: todavía tienes el texto de ejemplo en el archivo .env.")
        print("     Abre .env y reemplázalo por tu clave real (empieza con AIza...).")
        return 1

    print(f"     OK. Clave detectada: {api_key[:6]}...{api_key[-4:]} ({len(api_key)} caracteres)")

    print("2/4  Conectando con Google Gemini...")
    from google import genai

    cliente = genai.Client(api_key=api_key)

    print(f"3/4  Probando el modelo de chat ({MODELO_CHAT})...")
    try:
        respuesta = cliente.models.generate_content(
            model=MODELO_CHAT,
            contents="Responde unicamente con la palabra: LISTO",
        )
        print(f"     OK. El modelo respondio: {(respuesta.text or '').strip()}")
    except Exception as error:  # noqa: BLE001
        print(f"     ERROR al llamar al modelo de chat: {error}")
        return 1

    print(f"4/4  Probando el modelo de embeddings ({MODELO_EMBEDDINGS})...")
    try:
        from google.genai import types

        emb = cliente.models.embed_content(
            model=MODELO_EMBEDDINGS,
            contents=["prueba de conexion"],
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        print(f"     OK. Vector de {len(emb.embeddings[0].values)} dimensiones.")
    except Exception as error:  # noqa: BLE001
        print(f"     ERROR al generar embeddings: {error}")
        return 1

    print("\nTODO CORRECTO. Ya puedes ejecutar el agente:")
    print("   python cli.py")
    print("   streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
