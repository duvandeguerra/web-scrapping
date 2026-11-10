"""Genera datos/datos_beautifulsoup.csv y aplica una puerta de calidad.
Uso:  python -m scraping.pipeline"""
import pathlib
import sys
import time

import pandas as pd

from scraping.parsers import leer_listados

COMPLETITUD_MINIMA = 0.95  # métrica de éxito definida en la Evidencia 1


def main(carpeta="html", salida="datos/datos_beautifulsoup.csv"):
    inicio = time.perf_counter()
    filas = leer_listados(carpeta)
    if not filas:
        print(f"ERROR: no se extrajo ningún registro de {carpeta}/")
        return 1

    df = pd.DataFrame(filas)
    pathlib.Path(salida).parent.mkdir(exist_ok=True)
    df.to_csv(salida, index=False, encoding="utf-8-sig")

    completitud = df["precio"].notna().mean()
    print(f"Registros: {len(df)} | Únicos por URL: {df['url'].nunique()} | "
          f"Precio completo: {completitud:.1%} | "
          f"Tiempo: {time.perf_counter() - inicio:.1f} s")

    if completitud < COMPLETITUD_MINIMA:
        print("ERROR: la completitud del precio está por debajo de la meta")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())