"""Captura la evidencia visual del deploy contra la aplicación en producción.

Abre la URL pública con un navegador real, lanza una consulta de ejemplo y
guarda tres capturas en `docs/capturas/`. Al automatizarlo, la evidencia se
puede regenerar en cualquier momento sin depender de capturas manuales.

    python scripts/capturar_evidencia.py

Nota: Streamlit Community Cloud sirve la aplicación dentro de un iframe
(`/~/+/`), así que los selectores se resuelven contra ese frame y no contra el
documento principal.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Frame, Page, sync_playwright

URL_APP = "https://asistente-vidasana.streamlit.app/"
PREGUNTA = "¿Cuánto cuesta una consulta de cardiología y en qué sedes la atienden?"

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "capturas"
VIEWPORT = {"width": 1440, "height": 1100}

ESPERA_LARGA = 180_000


def obtener_frame_app(pagina: Page) -> Frame:
    """Devuelve el frame interno donde Streamlit monta la aplicación."""
    pagina.wait_for_selector('iframe[src*="/~/+/"]', timeout=ESPERA_LARGA)
    elemento = pagina.query_selector('iframe[src*="/~/+/"]')
    frame = elemento.content_frame() if elemento else None
    if frame is None:
        raise RuntimeError("No se encontró el iframe de la aplicación.")
    return frame


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport=VIEWPORT, device_scale_factor=2)

        print(f"Abriendo {URL_APP} ...")
        pagina.goto(URL_APP, wait_until="domcontentloaded", timeout=ESPERA_LARGA)

        app = obtener_frame_app(pagina)

        # La app puede estar dormida (plan gratuito de Streamlit Cloud).
        despertar = app.get_by_text("get this app back up", exact=False)
        if despertar.count():
            print("La app estaba dormida: reactivandola...")
            despertar.first.click()
            pagina.wait_for_timeout(20_000)
            app = obtener_frame_app(pagina)

        print("Esperando a que termine la indexacion del corpus...")
        app.wait_for_selector("text=Fragmentos indexados", timeout=ESPERA_LARGA)
        pagina.wait_for_timeout(2_500)

        ruta = DESTINO / "01-app-desplegada.png"
        pagina.screenshot(path=str(ruta))
        print(f"  1/3  {ruta.name}")

        print(f"Lanzando la consulta: {PREGUNTA}")
        app.get_by_role("button", name=PREGUNTA).click()

        app.wait_for_selector("text=Cómo se obtuvo esta respuesta", timeout=ESPERA_LARGA)
        pagina.wait_for_timeout(2_000)

        ruta = DESTINO / "02-respuesta-agente.png"
        pagina.screenshot(path=str(ruta))
        print(f"  2/3  {ruta.name}")

        print("Desplegando la traza de herramientas...")
        app.get_by_text("Cómo se obtuvo esta respuesta", exact=False).last.click()
        app.wait_for_selector("text=consultar_catalogo", timeout=60_000)
        pagina.wait_for_timeout(1_500)

        # La traza se despliega al final del hilo; hay que arrastrar el scroll
        # del contenedor de chat para que la cita de la fuente quede visible.
        app.get_by_text("Catálogo de especialidades y tarifas", exact=False).last.scroll_into_view_if_needed()
        pagina.wait_for_timeout(2_000)

        ruta = DESTINO / "03-traza-fuentes.png"
        pagina.screenshot(path=str(ruta))
        print(f"  3/3  {ruta.name}")

        print("Cambiando a modo oscuro...")
        app.get_by_text("Modo oscuro", exact=False).click()
        pagina.wait_for_timeout(3_500)

        ruta = DESTINO / "04-modo-oscuro.png"
        pagina.screenshot(path=str(ruta))
        print(f"  4/4  {ruta.name}")

        navegador.close()

    print(f"\nCapturas guardadas en {DESTINO}")


if __name__ == "__main__":
    main()
