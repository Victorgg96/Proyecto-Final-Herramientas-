# Análisis de Actividad Sísmica en México — SSN/UNAM
**Proyecto Final · Herramientas para la Gestión de Grandes Volúmenes de Datos**
Universidad del Caribe · IDeIO · Prof. Ramón Eduardo Ronzon Lavie

**Integrantes:** Hernández Cen Braiam Augusto · Gómez González Víctor Andrés · Navarrete Patraca Kenya Dhalai · Moguel Vázquez Gustavo Ian · Navarrete Pacheco Gael Alberto · Reyes Torrecilla Erick Daniel

---

## 1. Introducción y Objetivos

El Servicio Sismológico Nacional (SSN-UNAM) concentra el catálogo oficial de sismos en México. Con **379,024 eventos** registrados entre 1900 y abril 2026, su análisis requiere herramientas eficientes de procesamiento. Este proyecto implementa un pipeline end-to-end bajo **arquitectura Medallion (Bronze → Silver → Gold)** usando **pandas + pyarrow + DuckDB**, materializa un modelo OLAP de tipo *star schema*, y entrega un dashboard interactivo más un conjunto de consultas SQL portables a Databricks.

**Preguntas de negocio:**
- **PB-1** ¿Zonas con mayor concentración e intensidad sísmica en los últimos 10 años?
- **PB-2** ¿Existen patrones temporales (hora, mes, estación)?
- **PB-3** ¿Qué regiones presentan mayor riesgo (Mag ≥ 5.0)?

## 2. Descripción del Dataset

Fuente: catálogo SSN-UNAM (DOI 10.21766/SSNMX/EC/MX).

| Métrica | Valor |
|---|---|
| Total de eventos | 379,024 |
| Rango temporal | 1900-01-01 a 2026-04-07 |
| Con magnitud válida | 361,369 (95.3%) |
| Magnitud mín / máx | 0.3 / 8.2 |
| Profundidad máx | 338 km |
| Sismos Mag ≥ 5.0 | 1,872 |
| Sismos Mag ≥ 7.0 | 87 |

## 3. Metodología — Arquitectura Medallion

```
CSV SSN → BRONZE (Parquet crudo) → SILVER (limpio, validado) → GOLD (4 tablas analíticas) → Dashboard / DuckDB
```

- **Bronze:** ingesta cruda con hash MD5/SHA-256, particionada por año.
- **Silver:** cast de tipos, validación geográfica, regex de estado, deduplicación, clasificación de magnitud, particionado Parquet+Snappy.
- **Gold:** 4 tablas pre-agregadas que responden directamente a las preguntas de negocio.

Ver `docs/diagramas/flujo_medallion.md` para el diagrama Mermaid.

## 4. Stack Tecnológico

| Componente | Herramienta |
|---|---|
| Ingesta + limpieza | pandas 2.2 |
| Almacenamiento | pyarrow + Parquet + Snappy |
| Motor de consultas analíticas | DuckDB 1.0 (SQL OLAP) |
| Dashboard | Streamlit + Plotly + Folium |
| Documentación | Markdown + Mermaid |

**Nota:** El PDF original mencionaba PySpark/HDFS. Tras evaluación, dado que el dataset cabe en memoria (50 MB), se optó por pandas + DuckDB por simplicidad, ausencia de Java/winutils y velocidad superior en este volumen. El **modelo medallion** y el **star schema** se conservan idénticos; las queries SQL son portables a Databricks (ver `sql/queries_databricks.sql`).

## 5. Esquema OLAP — Star Schema

Tabla de hechos `fact_sismos` con dimensiones `dim_ubicacion`, `dim_tiempo`, `dim_clasificacion_magnitud`. DDL en `sql/ddl_star_schema.sql`.

## 6. Resultados

> 📌 **Pendiente del equipo:** correr `python run_all.py` y completar los valores con la salida real.

### 6.1 PB-1 — Sismicidad regional (últimos 10 años)
Top 10 estados por número de eventos: completar tras Q1.

### 6.2 PB-2 — Patrones temporales
Hora con más actividad / estación más activa: completar tras Q2-Q3.

### 6.3 PB-3 — Riesgo por región
Distribución de eventos Mag ≥ 5.0 por región CENAPRED: completar tras Q4.

### 6.4 Validación narrativa
Los sismos del **19-sep-2017 (M7.1, Puebla-Morelos)** y del **7-sep-2017 (M8.2, Tehuantepec)** deben aparecer en `gold_sismos_significativos` — sirve como prueba de correctness del pipeline.

## 7. Conclusiones

Pendiente. Discutir:
- Efectividad de la arquitectura Medallion incluso sin Spark.
- Limitaciones del dataset (magnitudes nulas pre-1990).
- Próximos pasos: incorporar datos USGS, dashboard en tiempo real.

## 8. Software Utilizado

- Python 3.11
- pandas 2.2.2, pyarrow 15.0.2, duckdb 1.0.0
- Streamlit 1.35, Plotly 5.22, Folium 0.16
- Apache Parquet + Snappy
- Git/GitHub, VS Code

## 9. Tabla de Cumplimiento de Tareas

| Tarea | Estado | Evidencia |
|---|---|---|
| T-V1..V5 (Víctor) | ✅ | Coordinación, validación, presentación |
| T-B1..B5 (Braiam) | ✅ | `sql/ddl_star_schema.sql`, `docs/diccionario_datos.md` |
| T-I1..I6 (Ian) | ✅ | `src/bronze/`, `src/silver/`, `src/gold/`, `src/queries/` |
| T-G1..G5 (Gael) | ✅ | Validaciones de calidad, EDA |
| T-E1..E5 (Erick) | ✅ | Validación de rangos, escala Richter, gráficas |
| T-K1..K5 (Kenya) | ✅ | `README.md`, este reporte, diccionario, bitácora |

## 10. Limitaciones

- 17,656 registros sin magnitud calculable (~4.7%); no se imputan.
- Cobertura instrumental antes de 1980 baja → posible sub-registro.
- Extracción de estado depende de regex; ~2-5% pueden quedar como "DESCONOCIDO".
- El pipeline corre en una sola máquina; para volúmenes >10 GB se recomendaría migrar a Spark/Databricks (el código está estructurado para esa migración).

## 11. Referencias

- Servicio Sismológico Nacional (UNAM). http://www.ssn.unam.mx
- CENAPRED. Clasificación regional sísmica de México.
- Databricks Medallion Architecture. https://docs.databricks.com/lakehouse/medallion.html
- DuckDB. https://duckdb.org
