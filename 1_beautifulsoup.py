"""
Scraping con requests + BeautifulSoup.
- Extrae la 1.a página de resultados de la búsqueda.
- Extrae el detalle del artículo seleccionado leyendo su JSON-LD.
"""
import csv
import json
import os
import time
import pathlib

import requests
from bs4 import BeautifulSoup
import re
PATRON_LISTADO = re.compile(r"^(?P<tipo>.+)_p(?P<pagina>\d+)$")
   

# BUSQUEDA_URL = "https://listado.mercadolibre.com.co/cafetera-espresso"
# ARTICULO_URL = "https://www.mercadolibre.com.co/cafetera-automatica-espresso-compacta-krups-coffee-crush-experience-con-molinillo-cold-brew-y-espumador/p/MCO69965681"

BUSQUEDA_URL = "html/listado_1.html"   # o la URL si no hay bloqueo
ARTICULO_URL = "html/krups_coffee_crush_extra.html"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/130.0 Safari/537.36"),
    "Accept-Language": "es-CO,es;q=0.9",
}

# Selectores CSS (verificar con F12 antes de ejecutar)
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
}

def obtener_html(fuente):
    """Acepta una URL o la ruta de un archivo HTML guardado."""
    if fuente.startswith("http"):
        return descargar(fuente)
    with open(fuente, encoding="utf-8") as f:
        return f.read()

def extraer_resumen_ia(soup):
    """Resumen de opiniones generado por IA (viene en el HTML del servidor)."""
    bloque = (soup.select_one('[data-testid="summary-component"]')
              or soup.select_one(".ui-review-capability__summary"))
    if not bloque:
        return {"resumen_ia": None, "es_generado_por_ia": False}

    parrafo = bloque.select_one(".ui-review-capability__summary__plain_text__summary_container")
    etiqueta = bloque.select_one(".ui-review-capability__summary__description__text")
    return {
        "resumen_ia": parrafo.get_text(" ", strip=True) if parrafo else None,
        "es_generado_por_ia": bool(etiqueta and "IA" in etiqueta.get_text()),
    }

def extraer_especificaciones(html):
    """Busca filas de tabla con encabezado (th) y valor (td): así presenta ML las características."""
    soup = BeautifulSoup(html, "html.parser")
    specs = {}
    for fila in soup.select("table tr"):
        th, td = fila.find("th"), fila.find("td")
        if th and td:
            specs[th.get_text(strip=True)] = td.get_text(strip=True)
    return specs

def a_entero(texto):
    """'1.299.900' -> 1299900 ; '(57)' -> 57"""
    if not texto:
        return None
    digitos = "".join(c for c in texto if c.isdigit())
    return int(digitos) if digitos else None


def a_decimal(texto):
    try:
        return float(texto.replace(",", ".")) if texto else None
    except ValueError:
        return None


def texto_de(nodo, selector):
    el = nodo.select_one(selector)
    return el.get_text(strip=True) if el else None


def descargar(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()  # lanza error si la respuesta no es 200
    return resp.text


def extraer_listado(html):
    soup = BeautifulSoup(html, "html.parser")
    filas = []
    for card in soup.select(SEL["tarjeta"]):
        enlace = card.select_one(SEL["titulo"])
        filas.append({
            "titulo": enlace.get_text(strip=True) if enlace else None,
            "url": enlace["href"].split("#")[0] if enlace else None,
            "precio": a_entero(texto_de(card, SEL["precio"])),
            "precio_anterior": a_entero(texto_de(card, SEL["precio_anterior"])),
            "descuento": texto_de(card, SEL["descuento"]),
            "calificacion": a_decimal(texto_de(card, SEL["calificacion"])),
            "num_opiniones": a_entero(texto_de(card, SEL["opiniones"])),
            "envio_gratis": "gratis" in (texto_de(card, SEL["envio"]) or "").lower(),
            "vendedor": texto_de(card, SEL["vendedor"]),
        })
    return filas


def extraer_articulo(html):
    """Lee el bloque <script type="application/ld+json"> con los datos del producto."""
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
            return {
                "nombre": data.get("name"),
                "marca": (data.get("brand") or {}).get("name")
                         if isinstance(data.get("brand"), dict) else data.get("brand"),
                "precio": ofertas.get("price"),
                "moneda": ofertas.get("priceCurrency"),
                "disponibilidad": ofertas.get("availability"),
                "calificacion": rating.get("ratingValue"),
                "num_opiniones": rating.get("reviewCount") or rating.get("ratingCount"),
            }
    # Plan B si no hay JSON-LD: el título visible
    titulo = soup.select_one("h1.ui-pdp-title")
    return {"nombre": titulo.get_text(strip=True) if titulo else None}


def guardar_csv(filas, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)


if __name__ == "__main__":
    inicio = time.time()

    # Listados guardados
    filas = []
    for ruta in sorted(pathlib.Path("html").glob("*.html")):
            m = PATRON_LISTADO.match(ruta.stem)
            if not m:
                continue
            for fila in extraer_listado(ruta.read_text(encoding="utf-8")):
                fila["tipo"] = m["tipo"]
                filas.append(fila)

    print(f"Listados: {len(filas)} publicaciones")
    if filas:
        guardar_csv(filas, "datos/datos_beautifulsoup.csv")

    # Ficha guardada por Selenium
    ruta_ficha = pathlib.Path("html/krups_coffee_crush_extra.html")
    if ruta_ficha.exists():
        html = ruta_ficha.read_text(encoding="utf-8")
        articulo = extraer_articulo(html)
        articulo["especificaciones"] = extraer_especificaciones(html)
        articulo.update(extraer_resumen_ia(BeautifulSoup(html, "html.parser")))
        print(json.dumps(articulo, ensure_ascii=False, indent=2))

    print(f"Tiempo: {time.time() - inicio:.1f} s")