from collections import Counter

import requests
from bs4 import BeautifulSoup

URL = "https://www.mercadolibre.com.co/cafetera-espresso-automatica-krups-coffee-crush-extra/up/MCOU4151294121"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/130.0 Safari/537.36"),
    "Accept-Language": "es-CO,es;q=0.9",
}

r = requests.get(URL, headers=HEADERS, timeout=20)
print("Estado HTTP:", r.status_code)
print("URL final:  ", r.url)
print("Tamaño HTML:", len(r.text), "caracteres")

soup = BeautifulSoup(r.text, "html.parser")
print("Título:     ", soup.title.get_text(strip=True) if soup.title else None)

print("\nSelectores candidatos:")
for sel in ["li.ui-search-layout__item", "ol.ui-search-layout", "div.poly-card",
            "a.poly-component__title", "h3.poly-component__title-wrapper",
            ".andes-money-amount__fraction", "div.ui-search-result__wrapper",'[data-testid="summary-component"]', "h1.ui-pdp-title", "table tr",
            "li.ui-search-layout__item"]:
    print(f"  {sel:38} -> {len(soup.select(sel))}")

print("\nClases más frecuentes del listado:")
clases = Counter(c for tag in soup.find_all(class_=True) for c in tag["class"]
                 if "poly" in c or "ui-search" in c)
for clase, n in clases.most_common(15):
    print(f"  {clase:45} {n}")

with open("diagnostico.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print("\nHTML guardado en diagnostico.html")