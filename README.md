# Web scraping de cafeteras en Mercado Libre Colombia

Evidencia de aprendizaje 1 – Análisis y herramientas de extracción de datos
Asignatura: Programación para Análisis de Datos

## Descripción

Proyecto de extracción de datos (*web scraping*) sobre Mercado Libre Colombia para responder la pregunta:

> ¿Qué tipo de cafetera de hogar ofrece mejor relación calidad-precio para una familia de clase media en Colombia: de cápsulas o de café en grano/molido?

Se extraen precios, descuentos, calificaciones, envío, especificaciones técnicas y el resumen de opiniones generado por IA de cafeteras e insumos (cápsulas y café), usando tres herramientas:

| Herramienta | Uso en el proyecto |
|---|---|
| **Selenium** | Abre en vivo las fichas de producto, expande las características y guarda el HTML |
| **BeautifulSoup** | Analiza los listados y fichas guardados (selectores CSS y JSON-LD) |
| **Scrapy** | Procesa los listados guardados y exporta a CSV |

Este conjunto de datos es la base de las evidencias de las Unidades 2 (limpieza), 3 (análisis) y la actividad de cierre.

## Estructura del proyecto

```
web-scrapping/
├── README.md
├── requirements.txt
├── diagnostico.py           # Verifica qué devuelve el sitio a una petición directa
├── 1_beautifulsoup.py       # Listados y ficha de la Krups desde html/
├── 2_selenium_fichas.py     # Fichas de producto en vivo (specs, estrellas, resumen IA)
├── 2b_selenium_listado.py   # Intento de listados en vivo (bloqueado por el sitio)
├── 3_scrapy_spider.py       # Listados desde html/ con Scrapy
├── 4_analisis.py            # Resumen y comparación de resultados
├── html/                    # Páginas guardadas (listados y fichas)
└── datos/                   # Resultados (CSV y JSON)
```

## Requisitos

- Python 3.10 o superior
- Google Chrome actualizado (lo usa Selenium; el driver se descarga automáticamente)
- Librerías de `requirements.txt`:

```
requests
beautifulsoup4
selenium
scrapy
pandas
```

## Instalación

1. Descomprimir el archivo `.zip` del proyecto.
2. Abrir una terminal dentro de la carpeta descomprimida.
3. Crear el entorno virtual:

```bash
python -m venv venv
```

Activar el entorno virtual:

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `.\venv\Scripts\Activate.ps1` |
| Windows (cmd) | `venv\Scripts\activate` |
| macOS / Linux | `source venv/bin/activate` |

Si PowerShell bloquea la activación, ejecutar una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Obtención de las páginas (importante)

Mercado Libre protege su sitio contra el tráfico automatizado:

| Página | requests | Selenium | Navegador normal |
|---|---|---|---|
| Listados de búsqueda | ❌ Verificación de cuenta | ❌ Verificación de cuenta | ✅ |
| Fichas de producto | ❌ Verificación de cuenta | ✅ | ✅ |

Por respeto a los términos de uso **no se intentó evadir esta protección**. En su lugar:

1. **Fichas:** las descarga `2_selenium_fichas.py` y las guarda en `html/`.
2. **Listados:** se guardaron manualmente desde el navegador (Ctrl + S → "Página web, completa") en `html/`, con este formato de nombre:

```
<tipo>_p<número de página>.html
```

| Archivo | Búsqueda en Mercado Libre |
|---|---|
| `maquina_grano_molido_p1.html`, `_p2` | cafetera espresso automatica |
| `maquina_capsulas_p1.html`, `_p2` | cafetera nespresso |
| `insumo_capsulas_p1.html`, `_p2` | capsulas nespresso |
| `insumo_grano_p1.html`, `_p2` | cafe en grano 500 g |

Los scripts reconocen como listado solo los archivos que cumplen ese patrón; el resto se trata como ficha.

## Ejecución

Con el entorno virtual activado, en este orden:

```bash
# 1. Fichas en vivo con Selenium (abre Chrome; no tocar la ventana)
python 2_selenium_fichas.py

# 2. Listados y ficha con BeautifulSoup
python 1_beautifulsoup.py

# 3. Listados con Scrapy
scrapy runspider 3_scrapy_spider.py -L INFO

# 4. Resumen y comparación
python 4_analisis.py
```

Para agregar productos, editar el diccionario `PRODUCTOS` en `2_selenium_fichas.py` con URLs limpias (sin el texto después de `?` o `#`).

## Resultados generados

| Archivo | Herramienta | Contenido |
|---|---|---|
| `datos/fichas_selenium.json` | Selenium | 25 fichas: título, precio, calificación, opiniones, distribución de estrellas, resumen IA y especificaciones |
| `datos/datos_beautifulsoup.csv` | BeautifulSoup | 456 publicaciones de listado |
| `datos/datos_scrapy.csv` | Scrapy | 456 publicaciones de listado |

**Variables de listado:** `tipo`, `pagina`, `titulo`, `url`, `precio`, `precio_anterior`, `descuento`, `calificacion`, `num_opiniones`, `envio_gratis`, `vendedor`.

### Resumen de la ejecución

| Herramienta | Fuente | Registros | Tiempo |
|---|---|---|---|
| requests + BeautifulSoup | En vivo | 0 (bloqueado) | — |
| Selenium | 25 fichas en vivo | 25 | 423,3 s |
| BeautifulSoup | 8 listados guardados | 456 | 13,7 s* |
| Scrapy | 8 listados guardados | 456 | 1,4 s |

\* Incluye también el procesamiento de la ficha de la Krups.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError` | Entorno virtual no activado | Activarlo y repetir |
| 0 publicaciones | Cambiaron los selectores CSS | Inspeccionar con F12 y actualizar `SEL` |
| Redirección a `/gz/account-verification` | Protección anti-robots del sitio | Usar páginas guardadas (ver arriba) |
| Scrapy termina sin peticiones | Scrapy ≥ 2.13 usa `async def start()` | Ya implementado en `3_scrapy_spider.py` |
| `invalid literal for int()` en Scrapy | Un archivo que no es listado coincide con el patrón | Se filtra con la expresión regular `PATRON_LISTADO` |
| Envío gratis en 0 % | Clase renombrada a `poly-component__shipping-v2` | El selector acepta ambas versiones |

## Consideraciones éticas

- Solo se extrae información pública de productos, sin datos personales.
- Se respetan las restricciones del sitio: no se usan cuentas, proxies ni técnicas para evadir la detección.
- Se incluyen pausas entre peticiones para no sobrecargar el servidor.
- Para un uso a mayor escala, la vía recomendada es la API oficial de Mercado Libre (developers.mercadolibre.com.co).
- Los datos se usan con fines académicos.

## Contenido del archivo .zip

El proyecto se entrega comprimido e incluye el código, las páginas HTML guardadas y los datos obtenidos, de modo que los scripts de BeautifulSoup, Scrapy y análisis pueden ejecutarse sin conexión.

**Incluido:** `README.md`, `requirements.txt`, todos los `.py`, la carpeta `html/` (solo los archivos `.html`) y la carpeta `datos/`.

**Excluido:** `venv/` (se crea en cada equipo con la instalación), `__pycache__/` y las carpetas `html/*_files/` que crea el navegador al guardar páginas (contienen imágenes y estilos que los scripts no usan).

> Nota: `2_selenium_fichas.py` sí requiere internet y Google Chrome, porque descarga las fichas en vivo.