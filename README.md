# Web scraping de cafeteras en Mercado Libre Colombia

[![CI/CD](https://github.com/duvandeguerra/web-scrapping/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/duvandeguerra/web-scrapping/actions/workflows/ci-cd.yml)

Extracción y análisis de datos públicos de cafeteras de hogar e insumos de café en Mercado Libre Colombia, con pruebas automatizadas y despliegue continuo.

**Resultados publicados:** https://duvandeguerra.github.io/web-scrapping/

## Descripción

El proyecto reúne precios, descuentos, calificaciones, envío, especificaciones técnicas y resúmenes de opiniones para comparar cafeteras de cápsulas con cafeteras de café en grano o molido.

| Herramienta | Uso en el proyecto |
|---|---|
| **Selenium** | Abre en vivo las fichas de producto y guarda su HTML (solo en local) |
| **BeautifulSoup** | Analiza los listados y fichas guardados (módulo `scraping/`) |
| **Scrapy** | Procesa los listados guardados y exporta a CSV |

## Estructura del proyecto

```
web-scrapping/
├── .github/workflows/ci-cd.yml   Pipeline de CI/CD
├── scraping/
│   ├── parsers.py                Funciones de extracción con BeautifulSoup
│   └── pipeline.py               Genera el CSV y valida la calidad
├── scripts/
│   ├── selenium_fichas.py        Fichas en vivo con Selenium (solo local)
│   ├── selenium_listado.py       Intento de listados en vivo (bloqueado por el sitio)
│   └── scrapy_spider.py          Listados con Scrapy
├── tests/test_parsers.py         Pruebas unitarias, de regresión e integración
├── html/                         Páginas guardadas (8 listados y 25 fichas)
├── datos/                        Resultados (CSV y JSON)
├── informe.ipynb                 Notebook de análisis de resultados
├── pyproject.toml                Configuración de pytest y ruff
└── requirements.txt
```

## Requisitos

- Python 3.14 o superior
- Git
- Google Chrome (solo para los scripts de Selenium)

## Instalación

```bash
git clone https://github.com/duvandeguerra/web-scrapping.git
cd web-scrapping
python -m venv venv
```

Activar el entorno virtual:

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `.\venv\Scripts\Activate.ps1` |
| Windows (cmd) | `venv\Scripts\activate` |
| macOS / Linux | `source venv/bin/activate` |

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Generar los datos a partir de las páginas guardadas
python -m scraping.pipeline
scrapy runspider scripts/scrapy_spider.py -L INFO

# Ejecutar el notebook y generar la página de resultados
jupyter nbconvert --to html --execute informe.ipynb --output index.html --output-dir site --ExecutePreprocessor.kernel_name=python3
```

El notebook también puede abrirse en Jupyter o VS Code y ejecutarse celda por celda.

Opcional, solo en local (requiere Chrome e internet):

```bash
python scripts/selenium_fichas.py
```

## Pruebas

```bash
ruff check scraping tests
pytest -v
```

| Tipo | Cantidad | Qué verifican |
|---|---|---|
| Unitarias | 5 | Conversión de números, tarjeta de listado, resumen de IA y JSON-LD |
| De regresión | 4 | Errores ya corregidos: selector de envío renombrado y confusión entre fichas y listados |
| De integración | 9 | Los 8 listados reales: al menos 20 publicaciones y 95 % de precios por archivo; envío gratis distinto de cero |

## Integración y despliegue continuos

El pipeline está definido en [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) y tiene tres trabajos encadenados:

```
Pruebas (CI)  ──>  Generar datos e informe  ──>  Desplegar (CD)
```

| Trabajo | Cuándo se ejecuta | Qué hace |
|---|---|---|
| **Pruebas (CI)** | En cada push y pull request | Instala el proyecto en una máquina limpia, revisa el estilo con `ruff` y ejecuta las pruebas con `pytest` |
| **Generar datos e informe** | Solo en `main`, si las pruebas pasan | Regenera los datos con BeautifulSoup y Scrapy, valida que el precio esté completo en al menos el 95 % de los registros y ejecuta el notebook |
| **Desplegar (CD)** | Después de la construcción | Publica el notebook en HTML y los datos en GitHub Pages |

## Flujo de trabajo

1. Crear una rama desde `main` con un prefijo según el tipo de cambio.
2. Hacer commits pequeños con mensajes descriptivos.
3. Verificar en local con `ruff check scraping tests` y `pytest -v`.
4. Subir la rama y abrir un pull request hacia `main`.
5. Fusionar con *merge commit* cuando el chequeo **Pruebas (CI)** esté en verde.

| Prefijo | Uso | Ejemplo de rama |
|---|---|---|
| `feat` | Funcionalidad nueva | `feat/notebook-informe` |
| `refactor` | Reorganización sin cambiar el resultado | `refactor/modulo-parsers` |
| `test` | Pruebas | `test/pruebas-parsers` |
| `ci` / `cd` | Pipeline de integración o despliegue | `ci/github-actions` |
| `docs` | Documentación | `docs/readme` |
| `chore` | Datos, dependencias y mantenimiento | — |

Los mensajes de commit usan el mismo prefijo, por ejemplo: `refactor: extraer funciones de parsing a un módulo`.

## Datos y limitaciones

Mercado Libre redirige el tráfico automatizado a una verificación de cuenta: las peticiones directas se bloquean siempre, y Selenium solo accede a las fichas de producto. Esa protección no se evade. Por eso:

- Las **fichas** se descargan con Selenium en local.
- Los **listados** se guardan manualmente desde el navegador con el nombre `<tipo>_p<página>.html`.
- El **pipeline no hace scraping en vivo**: trabaja sobre las páginas guardadas en `html/`, lo que hace reproducibles los resultados.

| Archivo | Contenido |
|---|---|
| `datos/datos_beautifulsoup.csv` | Publicaciones de listado extraídas con BeautifulSoup |
| `datos/datos_scrapy.csv` | Publicaciones de listado extraídas con Scrapy |
| `datos/fichas_selenium.json` | Fichas con especificaciones, calificación y resumen de IA |

Para agregar datos: guardar nuevos listados en `html/` con el patrón de nombre indicado, o agregar URLs al diccionario `PRODUCTOS` de `scripts/selenium_fichas.py`.

Solo se usa información pública de productos, sin datos personales. Para un uso a mayor escala, la vía recomendada es la API oficial de Mercado Libre.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ERROR: no se extrajo ningún registro de html/` | Faltan los listados o no cumplen el patrón de nombre | Verificar que existan archivos `<tipo>_p<página>.html` directamente en `html/` |
| 0 publicaciones en un listado | Cambiaron las clases CSS del sitio | Inspeccionar la página y actualizar `SEL` en `scraping/parsers.py` |
| Redirección a `/gz/account-verification` | Protección del sitio contra tráfico automatizado | Usar páginas guardadas |
| `Invalid workflow file` en GitHub Actions | Sangría incorrecta en el archivo YAML | Las claves `name`, `on`, `permissions`, `concurrency` y `jobs` deben empezar en la columna 1 |

## Autor

Duvan Quintero Guerra