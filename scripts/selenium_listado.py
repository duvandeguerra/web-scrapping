"""
Selenium: abre las búsquedas, recorre la paginación y guarda cada página en html/
para procesarlas luego con BeautifulSoup y Scrapy.
"""
import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BUSQUEDAS = {
    "cafetera espresso automatica": "maquina_grano_molido",
    "cafetera nespresso": "maquina_capsulas",
    "capsulas nespresso": "insumo_capsulas",
    "cafe en grano 500 g": "insumo_grano",
}
PAGINAS = 3


def main():
    op = Options()
    op.add_argument("--window-size=1366,900")
    op.add_argument("--lang=es-CO")
    driver = webdriver.Chrome(options=op)
    espera = WebDriverWait(driver, 15)
    os.makedirs("html", exist_ok=True)
    inicio = time.time()

    try:
        for termino, tipo in BUSQUEDAS.items():
            driver.get("https://listado.mercadolibre.com.co/" + termino.replace(" ", "-"))
            time.sleep(2)
            if "account-verification" in driver.current_url:
                print(f"⚠ {termino}: verificación de cuenta, se omite")
                continue

            for pagina in range(1, PAGINAS + 1):
                try:
                    espera.until(EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "li.ui-search-layout__item")))
                except TimeoutException:
                    print(f"⚠ {termino} p{pagina}: no aparecieron resultados")
                    break

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                archivo = f"html/{tipo}_p{pagina}.html"
                with open(archivo, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                n = len(driver.find_elements(By.CSS_SELECTOR, "li.ui-search-layout__item"))
                print(f"✔ {archivo}: {n} publicaciones")

                try:
                    boton = driver.find_element(
                        By.CSS_SELECTOR, "li.andes-pagination__button--next a")
                except NoSuchElementException:
                    break
                primera = driver.find_element(By.CSS_SELECTOR, "li.ui-search-layout__item")
                driver.execute_script("arguments[0].click();", boton)
                espera.until(EC.staleness_of(primera))
                time.sleep(3)  # pausa respetuosa entre páginas
    finally:
        driver.quit()

    print(f"Listo en {time.time() - inicio:.1f} s")


if __name__ == "__main__":
    main()