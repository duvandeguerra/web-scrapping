import json
import pandas as pd

print("=== BeautifulSoup (listado, 1 página) ===")
bs = pd.read_csv("datos/datos_beautifulsoup.csv")
print(f"Registros: {len(bs)} | Precio completo: {bs['precio'].notna().mean()*100:.1f} %")

print("\n=== Scrapy (por búsqueda) ===")
sc = pd.read_csv("datos/datos_scrapy.csv")
print(f"Registros: {len(sc)} | Únicos por URL: {sc['url'].nunique()}")
resumen = sc.groupby("tipo").agg(
    registros=("titulo", "count"),
    precio_mediana=("precio", "median"),
    precio_min=("precio", "min"),
    precio_max=("precio", "max"),
    pct_envio_gratis=("envio_gratis", "mean"),
)
resumen["pct_envio_gratis"] = (resumen["pct_envio_gratis"] * 100).round(1)
print(resumen)

print("\n=== Selenium (fichas) ===")
with open("datos/fichas_selenium.json", encoding="utf-8") as f:
    fichas = json.load(f)
for ficha in fichas:
    print(f"- {ficha['producto']}: {ficha['calificacion']} ★, "
          f"{len(ficha['especificaciones'])} specs, "
          f"resumen IA: {'sí' if ficha['resumen_ia'] else 'no'}")

print("\n=== BeautifulSoup vs Scrapy por tipo ===")
comparacion = pd.DataFrame({
    "BeautifulSoup": bs.groupby("tipo")["titulo"].count(),
    "Scrapy": sc.groupby("tipo")["titulo"].count(),
})
print(comparacion)

print("\nEnvío gratis (BeautifulSoup vs Scrapy):",
      f"{bs['envio_gratis'].mean()*100:.1f} %", "vs",
      f"{sc['envio_gratis'].mean()*100:.1f} %")