import pathlib

import pytest

from scraping.parsers import (
    PATRON_LISTADO,
    a_entero,
    extraer_articulo,
    extraer_listado,
    extraer_resumen_ia,
    leer_listados,
)

# --- HTML mínimo de ejemplo, con la misma estructura que usa Mercado Libre ---
TARJETA = """
<ol><li class="ui-search-layout__item">
  <a class="poly-component__title"
     href="https://www.mercadolibre.com.co/cafetera-demo/p/MCO123?x=1#polycard">Cafetera Demo 15 Bar</a>
  <s><span class="andes-money-amount__fraction">1.699.900</span></s>
  <div class="poly-price__current">
    <span class="andes-money-amount__fraction">1.299.900</span>
    <span class="andes-money-amount__discount">23% OFF</span>
  </div>
  <span class="poly-reviews__rating">4.8</span>
  <span class="poly-reviews__total">(120)</span>
  {envio}
  <span class="poly-component__seller">Por Krups</span>
</li></ol>
"""
ENVIO_V2 = ('<div class="poly-component__shipping-v2"><div class="poly-shipping-v2__item">'
            '<span aria-hidden="true">Envío gratis</span>'
            '<span class="andes-visually-hidden">Envío gratis</span></div></div>')
ENVIO_V1 = '<div class="poly-component__shipping">Llega gratis mañana</div>'

RESUMEN = """
<div class="ui-review-capability__summary" data-testid="summary-component">
  <div class="ui-review-capability__summary__plain_text">
    <p class="ui-review-capability__summary__plain_text__summary_container">Es fácil de usar y rápida.</p>
  </div>
  <div class="ui-review-capability__summary__description">
    <span class="ui-review-capability__summary__description__text">Resumen de opiniones generado por IA</span>
  </div>
</div>
"""

JSON_LD = """
<script type="application/ld+json">
{"@type": "Product", "name": "Cafetera Demo", "brand": {"name": "Krups"},
 "offers": {"price": 1299900, "priceCurrency": "COP"},
 "aggregateRating": {"ratingValue": 4.5, "reviewCount": 16}}
</script>
"""


# --- Pruebas unitarias ---
def test_a_entero():
    assert a_entero("1.299.900") == 1299900
    assert a_entero("(57)") == 57
    assert a_entero("sin número") is None
    assert a_entero(None) is None


def test_tarjeta_completa():
    fila = extraer_listado(TARJETA.format(envio=ENVIO_V2))[0]
    assert fila["titulo"] == "Cafetera Demo 15 Bar"
    assert fila["url"] == "https://www.mercadolibre.com.co/cafetera-demo/p/MCO123"
    assert fila["precio"] == 1299900
    assert fila["precio_anterior"] == 1699900
    assert fila["calificacion"] == 4.8
    assert fila["num_opiniones"] == 120
    assert fila["vendedor"] == "Por Krups"


def test_resumen_ia_presente():
    r = extraer_resumen_ia(RESUMEN)
    assert r["resumen_ia"] == "Es fácil de usar y rápida."
    assert r["es_generado_por_ia"] is True


def test_resumen_ia_ausente():
    assert extraer_resumen_ia("<html><body></body></html>")["resumen_ia"] is None


def test_json_ld():
    art = extraer_articulo(JSON_LD)
    assert art["marca"] == "Krups"
    assert art["precio"] == 1299900
    assert art["num_opiniones"] == 16


# --- Pruebas de regresión: errores reales encontrados en la Evidencia 1 ---
@pytest.mark.parametrize(
    "envio, esperado",
    [(ENVIO_V2, True), (ENVIO_V1, True), ("", False)],
    ids=["clase-v2", "clase-v1", "sin-envio"],
)
def test_envio_gratis(envio, esperado):
    """El componente fue renombrado a shipping-v2 y la variable daba 0 %."""
    assert extraer_listado(TARJETA.format(envio=envio))[0]["envio_gratis"] is esperado


def test_patron_listado():
    """La ficha 'nespresso_vertuo_pop' se confundía con un listado."""
    assert PATRON_LISTADO.match("maquina_capsulas_p2")["pagina"] == "2"
    assert PATRON_LISTADO.match("nespresso_vertuo_pop") is None


# --- Pruebas de integración sobre las páginas reales guardadas ---
LISTADOS = sorted(p for p in pathlib.Path("html").glob("*.html")
                  if PATRON_LISTADO.match(p.stem))


@pytest.mark.parametrize("ruta", LISTADOS, ids=lambda p: p.name)
def test_listado_real(ruta):
    filas = extraer_listado(ruta.read_text(encoding="utf-8", errors="replace"))
    assert len(filas) >= 20
    assert sum(f["precio"] is not None for f in filas) / len(filas) >= 0.95


def test_envio_gratis_no_es_cero():
    filas = leer_listados("html")
    if not filas:
        pytest.skip("no hay listados guardados")
    assert any(f["envio_gratis"] for f in filas)