"""
Scrapy procesando las páginas de listado guardadas en html/.
Ejecutar:  scrapy runspider 3_scrapy_spider.py
"""
import pathlib

import scrapy
import re

PATRON_LISTADO = re.compile(r"^(?P<tipo>.+)_p(?P<pagina>\d+)$")

CARPETA = pathlib.Path("html").resolve()


def a_entero(texto):
    digitos = "".join(c for c in (texto or "") if c.isdigit())
    return int(digitos) if digitos else None


class CafeterasSpider(scrapy.Spider):
    name = "cafeteras"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # no aplica: se leen archivos locales
        "FEEDS": {"datos/datos_scrapy.csv": {
            "format": "csv", "encoding": "utf-8-sig", "overwrite": True}},
    }

    async def start(self):
        listados = []
        for ruta in sorted(CARPETA.glob("*.html")):
            m = PATRON_LISTADO.match(ruta.stem)
            if m:  # se ignoran las fichas guardadas por Selenium
                listados.append((ruta, m["tipo"], int(m["pagina"])))
        self.logger.info(f"Listados encontrados: {len(listados)} en {CARPETA}")
        for ruta, tipo, pagina in listados:
            yield scrapy.Request(ruta.as_uri(), callback=self.parse,
                                 cb_kwargs={"tipo": tipo, "pagina": pagina})

    def parse(self, response, tipo, pagina):
        for card in response.css("li.ui-search-layout__item"):
            titulo = card.css("a.poly-component__title::text, h3 a::text").get()
            url = card.css("a.poly-component__title::attr(href), h3 a::attr(href)").get()
            envio = " ".join(card.css(
                ".poly-component__shipping-v2 ::text, .poly-component__shipping ::text").getall())
            yield {
                "tipo": tipo,
                "pagina": pagina,
                "titulo": titulo.strip() if titulo else None,
                "url": url.split("#")[0].split("?")[0] if url else None,
                "precio": a_entero(card.css(
                    ".poly-price__current .andes-money-amount__fraction::text").get()),
                "precio_anterior": a_entero(card.css(
                    "s .andes-money-amount__fraction::text").get()),
                "descuento": card.css(".andes-money-amount__discount::text").get(),
                "calificacion": card.css(".poly-reviews__rating::text").get(),
                "num_opiniones": a_entero(card.css(".poly-reviews__total::text").get()),
                "envio_gratis": "gratis" in envio.lower(),
                "vendedor": card.css(".poly-component__seller::text").get(),
            }