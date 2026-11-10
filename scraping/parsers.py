"""Extracción (parsing) de páginas de Mercado Libre con BeautifulSoup.
No hace peticiones de red: recibe HTML y devuelve datos."""
import json
import pathlib
import re

from bs4 import BeautifulSoup

# Un listado se llama <tipo>_p<número>.html; cualquier otro archivo es una ficha
PATRON_LISTADO = re.compile(r"^(?P<tipo>.+)_p(?P<pagina>\d+)$")

SEL = {
    "tarjeta": "li.ui-search-layout__item",
    "titulo": "a.poly-component__title, h3 a",
    "precio": ".poly-price__current .andes-money-amount__fraction",
    "precio_anterior": "s .andes-money-amount__fraction",
    "descuento": ".andes-money-amount__discount",
    "calificacion": ".poly-reviews__rating",
    "opiniones": ".poly-reviews__total",
    "envio": ".poly-component__shipping-v2, .poly-component__shipping",
    "vendedor": ".poly-component__seller",
    "resumen_ia": '[data-testid="summary-component"]',
    "resumen_ia_texto": ".ui-review-capability__summary__plain_text__summary_container",
    "resumen_ia_etiqueta": ".ui-review-capability__summary__description__text",
}


def a_entero(texto):
    """'1.299.900' -> 1299900 ; '(57)' -> 57 ; sin dígitos -> None"""
    digitos = "".join(c for c in (texto or "") if c.isdigit())
    return int(digitos) if digitos else None


def a_decimal(texto):
    try:
        return float(texto.replace(",", ".")) if texto else None
    except ValueError:
        return None


def _texto(nodo, selector):
    el = nodo.select_one(selector)
    return el.get_text(" ", strip=True) if el else None


def extraer_listado(html):
    """Devuelve una lista de diccionarios, uno por publicación."""
    soup = BeautifulSoup(html, "html.parser")
    filas = []
    for card in soup.select(SEL["tarjeta"]):
        enlace = card.select_one(SEL["titulo"])
        url = enlace.get("href") if enlace else None
        filas.append({
            "titulo": enlace.get_text(strip=True) if enlace else None,
            "url": url.split("#")[0].split("?")[0] if url else None,
            "precio": a_entero(_texto(card, SEL["precio"])),
            "precio_anterior": a_entero(_texto(card, SEL["precio_anterior"])),
            "descuento": _texto(card, SEL["descuento"]),
            "calificacion": a_decimal(_texto(card, SEL["calificacion"])),
            "num_opiniones": a_entero(_texto(card, SEL["opiniones"])),
            "envio_gratis": "gratis" in (_texto(card, SEL["envio"]) or "").lower(),
            "vendedor": _texto(card, SEL["vendedor"]),
        })
    return filas


def extraer_articulo(html):
    """Lee el JSON-LD (schema.org/Product) de una ficha."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            ofertas = data.get("offers") or {}
            if isinstance(ofertas, list):
                ofertas = ofertas[0] if ofertas else {}
            rating = data.get("aggregateRating") or {}
            marca = data.get("brand")
            return {
                "nombre": data.get("name"),
                "marca": marca.get("name") if isinstance(marca, dict) else marca,
                "precio": ofertas.get("price"),
                "moneda": ofertas.get("priceCurrency"),
                "calificacion": rating.get("ratingValue"),
                "num_opiniones": rating.get("reviewCount") or rating.get("ratingCount"),
            }
    return {}


def extraer_especificaciones(html):
    soup = BeautifulSoup(html, "html.parser")
    specs = {}
    for fila in soup.select("table tr"):
        th, td = fila.find("th"), fila.find("td")
        if th and td:
            specs[th.get_text(strip=True)] = td.get_text(strip=True)
    return specs


def extraer_resumen_ia(html):
    soup = BeautifulSoup(html, "html.parser")
    bloque = soup.select_one(SEL["resumen_ia"])
    if not bloque:
        return {"resumen_ia": None, "es_generado_por_ia": False}
    etiqueta = _texto(bloque, SEL["resumen_ia_etiqueta"]) or ""
    return {
        "resumen_ia": _texto(bloque, SEL["resumen_ia_texto"]),
        "es_generado_por_ia": "IA" in etiqueta,
    }


def leer_listados(carpeta="html"):
    """Procesa todos los listados guardados y etiqueta cada fila con tipo y página."""
    filas = []
    for ruta in sorted(pathlib.Path(carpeta).glob("*.html")):
        m = PATRON_LISTADO.match(ruta.stem)
        if not m:
            continue  # es una ficha
        html = ruta.read_text(encoding="utf-8", errors="replace")
        for fila in extraer_listado(html):
            filas.append({"tipo": m["tipo"], "pagina": int(m["pagina"]), **fila})
    return filas