# Bitácora de Decisiones Técnicas — v2

| # | Decisión | Justificación |
|---|---|---|
| 1 | **pandas + DuckDB en lugar de PySpark** | El dataset (50 MB, 379k filas) cabe en memoria. pandas+DuckDB elimina dependencia de Java, winutils, Python workers y configuración de cluster. Spark se justifica a partir de ~10 GB. |
| 2 | **Parquet + Snappy** en Bronze/Silver/Gold | Columnar, compresión rápida, mismo formato que usa Databricks/Spark — compatible si en el futuro se migra. |
| 3 | **DuckDB para queries analíticas** | Motor OLAP embebido, SQL puro tipo Databricks SQL, lee Parquet directo sin importar tablas, 0 servidores. |
| 4 | **No imputar magnitudes nulas** | Inventar datos sísmicos sesgaría análisis. `magnitud_disponible=False` permite filtrar en cada query según necesidad. |
| 5 | **Particionado por `anio_evento`/`anio`** | Optimiza queries temporales y permite reprocesamiento incremental. |
| 6 | **Regex sobre sufijo de "Referencia de localización"** | El campo es texto libre pero termina consistentemente con código de 2-3 letras (JAL, BCS, GRO…). |
| 7 | **Filtrado geográfico** lat [14, 33], lon [-119, -86] | Limita análisis a territorio mexicano; los eventos fuera se guardan aparte para auditoría. |
| 8 | **Star Schema documental** en `sql/ddl_star_schema.sql` | El modelo OLAP del PDF se preserva como referencia. Las Gold materializan vistas denormalizadas equivalentes. |
| 9 | **Distancia a CDMX (haversine)** pre-calculada | Permite responder "¿qué tan cerca de la capital fue?" sin recalcular. |
| 10 | **`run_all.py`** orquestador | Demo en vivo durante la presentación con un solo comando (~30 s). |
| 11 | **Streamlit + Plotly + Folium** | Dashboard interactivo local, sin servidor, sin Java. |
