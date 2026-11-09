"""
Selenium: extrae de cada ficha de cafetera
- título, precio, calificación y número de opiniones
- especificaciones técnicas completas (expandiendo 'Ver todas las características')
- distribución de estrellas y resumen de opiniones generado por IA
"""
import json
import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PRODUCTOS = {
    "Krups Coffee Crush Extra": "https://www.mercadolibre.com.co/cafetera-espresso-automatica-krups-coffee-crush-extra/up/MCOU4151294121",
    "Nespresso Essenza Mini": "https://www.mercadolibre.com.co/cafetera-nespresso-essenza-mini-negra/p/MCO28984167",
    "Nespresso Vertuo Pop": "https://www.mercadolibre.com.co/maquina-nespresso-vertuo-pop-black-espumador-de-leche-color-negro/p/MCO44489388",
    "KRUPS Espresso Essential": "https://www.mercadolibre.com.co/cafetera-espresso-essential-krups-negra/p/MCO15086566",
    "Cafetera Espresso Capuccino": "https://www.mercadolibre.com.co/cafetera-espresso-capuccino-espumador-leche-home-elements/up/MCOU2405146323",
    "Cafetera Espresso Portátil": "https://www.mercadolibre.com.co/cafetera-espresso-portatil-15-bar-usb-7800-mah/up/MCOU5288913663",
    "Cafetera Automática Espresso": "https://www.mercadolibre.com.co/cafetera-automatica-espresso-oster-primalatte-bvstem6604ss/p/MCO59327612",
    "Cafetera Espresso Compacta": "https://www.mercadolibre.com.co/cafetera-espresso-automatica-compacta-krups-coffee-crush-extra-con-molinillo-15-bares-de-presion-3-niveles-de-molienda-negra/p/MCO75779923",
    "Cafetera Espresso Perfect Brew": "https://www.mercadolibre.com.co/cafetera-espresso-perfect-brew-compacta-oster-bvstem7201/p/MCO67721845",
    "Cafetera Espresso Kalley": "https://www.mercadolibre.com.co/cafetera-expresso-kalley-k-ex-negra/p/MCO33316493",
    "Cafetera Oster Para Espresso Y Cappuccino": "https://www.mercadolibre.com.co/cafetera-oster-para-espresso-y-cappuccino4-tazas-tubo-de-vapor-para-espumar-la-leche-negro-bvstem3300/p/MCO33308926",
    "Cafetera Espresso Hamilton Beach": "https://www.mercadolibre.com.co/cafetera-espresso-hamilton-beach-40715-15-bares-1480-ml/p/MCO37257469",
    "Cafetera Imusa Café City XL": "https://www.mercadolibre.com.co/cafetera-imusa-cafe-city-xl-color-negro/p/MCO25989215",
    "Cafetera Ninja PB051": "https://www.mercadolibre.com.co/cafetera-ninja-pb051-compacta-con-espumador-165-l/p/MCO48710880",
    "Pack Milk x 50 cápsulas de café original Nespresso": "https://www.mercadolibre.com.co/pack-milk-x-50-capsulas-de-cafe-original-nespresso/p/MCO26344865",
    "Cápsulas Nespresso café reutilizables recargables pack x 4": "https://www.mercadolibre.com.co/capsulas-nespresso-cafe-reutilizables-recargables-pack-x-4/up/MCOU2419043526",
    "Pack World Explorations x 60 cápsulas de café Nespresso": "https://www.mercadolibre.com.co/pack-world-explorations-x-60-capsulas-de-cafe-nespresso/p/MCO26505395",
    "Pack Mug x 40 cápsulas de café Vertuo Nespresso": "https://www.mercadolibre.com.co/pack-mug-x-40-capsulas-de-cafe-vertuo-nespresso/p/MCO26108947",
    "Cápsulas Nespresso Master Origin Colombia": "https://www.mercadolibre.com.co/capsulas-nespresso-master-origin-colombia-10-capsulas/p/MCO19858409",
    "Cápsulas Nespresso Premium Excelso": "https://www.mercadolibre.com.co/capsulas-de-cafe-premium-excelso/p/MCO35912900",
    "Café Especial Bourbon Rosado": "https://articulo.mercadolibre.com.co/MCO-2659299938-cafe-especial-bourbon-rosado-_JM",
    "Café Especial en Grano - Origen Huila": "https://www.mercadolibre.com.co/cafe-especial-en-grano-origen-huila-500gr/up/MCOU3855066983",
    "Café Oma Institucional - Grano": "https://www.mercadolibre.com.co/cafe-oma-institucional-grano-2500g/p/MCO28387818",
    "Café En Grano - Premium Members - 25 Kilos": "https://www.mercadolibre.com.co/cafe-en-grano-premium-members-25-kilos/up/MCOU2412958341",
    "Café Members Roasted Molido - 1 Kilogramo": "https://www.mercadolibre.com.co/2-cafe-members-roasted-molido-x-1-kil-kg-a/p/MCO25725731"
}

# Textos que suelen acompañar al resumen de IA (verificar con F12)
FRASES_RESUMEN_IA = ["Resumen de opiniones generado por IA"]
BOTONES_EXPANDIR = ["Ver todas las características", "Ver más características"]


def crear_driver(headless=True):
    op = Options()
    if headless:
        op.add_argument("--headless=new")
    op.add_argument("--window-size=1366,900")
    op.add_argument("--lang=es-CO")
    return webdriver.Chrome(options=op)


def texto_css(driver, *selectores):
    """Devuelve el texto del primer selector que exista."""
    for sel in selectores:
        try:
            t = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
            if t:
                return t
        except NoSuchElementException:
            continue
    return None


def hacer_scroll_completo(driver, pasos=8):
    """Baja poco a poco para que carguen las secciones diferidas (opiniones, specs)."""
    altura = driver.execute_script("return document.body.scrollHeight")
    for i in range(1, pasos + 1):
        driver.execute_script(f"window.scrollTo(0, {altura * i / pasos});")
        time.sleep(0.8)


def clic_por_texto(driver, textos):
    for t in textos:
        elementos = driver.find_elements(
            By.XPATH, f"//button[contains(., '{t}')] | //a[contains(., '{t}')]")
        if elementos:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elementos[0])
            driver.execute_script("arguments[0].click();", elementos[0])
            time.sleep(1.5)
            return True
    return False


def extraer_especificaciones(driver):
    specs = {}
    for fila in driver.find_elements(By.XPATH, "//table//tr[th and td]"):
        clave = fila.find_element(By.TAG_NAME, "th").text.strip()
        valor = fila.find_element(By.TAG_NAME, "td").text.strip()
        if clave:
            specs[clave] = valor
    return specs


def extraer_distribucion_estrellas(driver):
    """Ej. {'5 estrellas': '80%', ...}; depende del diseño, verificar con F12."""
    dist = {}
    for nivel in driver.find_elements(By.CSS_SELECTOR, ".ui-review-capability-rating__level"):
        partes = [p for p in nivel.text.split("\n") if p.strip()]
        if len(partes) >= 2:
            dist[partes[0]] = partes[-1]
    return dist


def buscar_resumen_ia(driver):
    # 1) Selector exacto encontrado con F12
    try:
        bloque = driver.find_element(By.CSS_SELECTOR, '[data-testid="summary-component"]')
        parrafo = bloque.find_element(
            By.CSS_SELECTOR, ".ui-review-capability__summary__plain_text__summary_container")
        return parrafo.get_attribute("textContent").strip()
    except NoSuchElementException:
        pass

    # 2) Plan B: buscar por la etiqueta visible
    for frase in FRASES_RESUMEN_IA:
        els = driver.find_elements(By.XPATH, f"//*[contains(text(), '{frase}')]")
        if els:
            bloque = els[0].find_element(By.XPATH, "./ancestor::div[2]")
            return bloque.get_attribute("textContent").strip()
    return None

def extraer_ficha(driver, nombre, url):
    driver.get(url)

    time.sleep(2)
    if "account-verification" in driver.current_url:
        print(f"{nombre}: Mercado Libre pidió verificación de cuenta")
        return {"producto": nombre, "url": url, "bloqueado": True}
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
    hacer_scroll_completo(driver)
    expandido = clic_por_texto(driver, BOTONES_EXPANDIR)

    os.makedirs("html", exist_ok=True)
    nombre_archivo = nombre.lower().replace(" ", "_")
    with open(f"html/{nombre_archivo}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    return {
        "producto": nombre,
        "url": url,
        "titulo": texto_css(driver, "h1.ui-pdp-title", "h1"),
        "precio": texto_css(driver,
                            ".ui-pdp-price__second-line .andes-money-amount__fraction"),
        "calificacion": texto_css(driver, ".ui-pdp-review__rating",
                                  ".ui-review-capability__rating__average"),
        "num_opiniones": texto_css(driver, ".ui-pdp-review__amount"),
        "distribucion_estrellas": extraer_distribucion_estrellas(driver),
        "resumen_ia": buscar_resumen_ia(driver),
        "specs_expandidas": expandido,
        "especificaciones": extraer_especificaciones(driver),
    }


def main():
    inicio = time.time()
    driver = crear_driver(headless=False)  # False para ver qué pasa la primera vez
    fichas = []
    try:
        for nombre, url in PRODUCTOS.items():
            try:
                ficha = extraer_ficha(driver, nombre, url)
                fichas.append(ficha)
                print(f"✔ {nombre}: {len(ficha['especificaciones'])} specs, "
                      f"resumen IA: {'sí' if ficha['resumen_ia'] else 'no'}")
            except TimeoutException:
                print(f"✘ {nombre}: la página no cargó")
            time.sleep(3)  # pausa entre productos
    finally:
        driver.quit()

    os.makedirs("datos", exist_ok=True)
    with open("datos/fichas_selenium.json", "w", encoding="utf-8") as f:
        json.dump(fichas, f, ensure_ascii=False, indent=2)
    print(f"Listo: {len(fichas)} fichas en {time.time() - inicio:.1f} s")


if __name__ == "__main__":
    main()