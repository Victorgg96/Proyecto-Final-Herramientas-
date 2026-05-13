# Proyecto SSN-UNAM v2 · Análisis de Sismos en México 🌎

Pipeline **Bronze → Silver → Gold** sobre 379k sismos del Servicio Sismológico Nacional (1900–2026), implementado con **pandas + pyarrow + DuckDB** (sin PySpark, sin Java). Incluye dashboard Streamlit interactivo y queries SQL portables a Databricks.

**Universidad del Caribe · IDeIO · Herramientas para la gestión de grandes volúmenes de datos**

---

## 📁 Estructura

```
proyecto_sismos_v2/
├── config/settings.py
├── data/{raw,bronze,silver,gold}
├── src/
│   ├── bronze/   01_descarga.py · 02_ingesta_bronze.py
│   ├── silver/   03_limpieza_silver.py
│   ├── gold/     04..07_gold_*.py
│   ├── queries/  08_consultas_duckdb.py
│   ├── utils/    regex_estados.py · clasificacion_magnitud.py
│   └── dashboard/app_streamlit.py
├── sql/  ddl_star_schema.sql · queries_databricks.sql
├── docs/ diccionario_datos.md · decisiones_tecnicas.md · diagramas/
├── run_all.py        # Orquestador end-to-end
├── check_env.py      # Verifica entorno
├── REPORTE_FINAL.md
└── requirements.txt
```

## 🔧 Requisitos

- **Python 3.9 a 3.12** (recomendado 3.11)
- ~200 MB libres en disco
- NO requiere Java, NO requiere winutils, NO requiere Spark

## ⚙️ Instalación

```powershell
cd "C:\Users\vican\OneDrive\Escritorio\Claude Code\proyecto_sismos_v2"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## ▶️ Ejecución

### Pipeline completo (un solo comando)

```powershell
python run_all.py
```

Esto ejecuta en orden: verificación de entorno → descarga + hash → Bronze (pandas) → Silver → 4 tablas Gold → queries DuckDB con PB-1, PB-2, PB-3. Tarda ~30 segundos.

### Paso a paso (opcional)

```powershell
python check_env.py
python src/bronze/01_descarga.py
python src/bronze/02_ingesta_bronze.py
python src/silver/03_limpieza_silver.py
python src/gold/04_gold_sismicidad_regional.py
python src/gold/05_gold_patrones_temporales.py
python src/gold/06_gold_sismos_significativos.py
python src/gold/07_gold_evolucion_historica.py
python src/queries/08_consultas_duckdb.py
```

## 📊 Dashboard

Requisito: haber corrido el pipeline al menos hasta Gold.

```powershell
streamlit run src/dashboard/app_streamlit.py
```

Streamlit abre el navegador en `http://localhost:8501`. Pestañas:

- 🗺️ **Mapa** — Folium con epicentros (slider de años)
- ⏰ **Temporal** — Sismos por hora, estación, evolución anual
- 📍 **Regional** — Top estados y regiones CENAPRED
- ⚠️ **Significativos** — Catálogo Mag ≥ 5.0 y scatter
- ✅ **Calidad** — Métricas entre capas

Detener: `Ctrl+C` en la terminal.

## 🗄️ Queries SQL

### DuckDB local (incluido en el pipeline)
```powershell
python src/queries/08_consultas_duckdb.py
```
Imprime PB-1, PB-2, PB-3 + extras en consola.

### Databricks
1. Sube `data/gold/` a DBFS.
2. Registra vistas externas con `CREATE OR REPLACE TEMP VIEW … USING parquet`.
3. Abre `sql/queries_databricks.sql` en el SQL Editor y ejecuta Q1-Q10.

## 📝 Entregables

- ✅ Código fuente (`src/`)
- ✅ Queries SQL Databricks-ready (`sql/`)
- ✅ Dashboard interactivo (`src/dashboard/`)
- ✅ Reporte académico (`REPORTE_FINAL.md`)
- ✅ Diccionario + bitácora de decisiones (`docs/`)
- ⏳ Screenshots del dashboard *(generar al ejecutar)*
- ⏳ Notebook opcional para Colab/Databricks

## ❗ Troubleshooting

| Problema | Solución |
|---|---|
| `ModuleNotFoundError` | Activar venv y `pip install -r requirements.txt` |
| `No se encontró CSV` | Verificar ruta en `config/settings.py` (`CSV_FUENTE`) |
| Streamlit no abre | Abrir manualmente `http://localhost:8501` |
| Pandas usa mucha memoria | El dataset son ~50 MB; con 4 GB de RAM va sobrado |

## 👥 Integrantes y roles
Ver `REPORTE_FINAL.md` §9 (tabla de cumplimiento T-V/T-B/T-I/T-G/T-E/T-K).
