"""Orquestador end-to-end: Bronze -> Silver -> Gold -> Queries DuckDB."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PASOS = [
    ("Verificacion entorno",      "check_env.py"),
    ("B-1/B-2 Descarga + hash",   "src/bronze/01_descarga.py"),
    ("B-3..B-5 Bronze (pandas)",  "src/bronze/02_ingesta_bronze.py"),
    ("Silver limpieza",           "src/silver/03_limpieza_silver.py"),
    ("Gold sismicidad regional",  "src/gold/04_gold_sismicidad_regional.py"),
    ("Gold patrones temporales",  "src/gold/05_gold_patrones_temporales.py"),
    ("Gold sismos significativos","src/gold/06_gold_sismos_significativos.py"),
    ("Gold evolucion historica",  "src/gold/07_gold_evolucion_historica.py"),
    ("Consultas DuckDB (PB-1/2/3)","src/queries/08_consultas_duckdb.py"),
]

for nombre, script in PASOS:
    print(f"\n{'='*70}\n>>> {nombre}  ({script})\n{'='*70}")
    r = subprocess.run([sys.executable, str(ROOT / script)], cwd=str(ROOT))
    if r.returncode != 0:
        print(f"\n[ERROR] Fallo '{nombre}'")
        sys.exit(r.returncode)

print("\n" + "="*70)
print(" PIPELINE COMPLETO.")
print(" Levantar dashboard:  streamlit run src/dashboard/app_streamlit.py")
print("="*70)
