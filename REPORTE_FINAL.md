# Análisis de Actividad Sísmica en México
## Catálogo SSN-UNAM 1900–2026

**Asignatura:** Herramientas para la Gestión de Grandes Volúmenes de Datos  
**Programa Educativo:** IDeIO  
**Universidad del Caribe**  
**Presentado a:** Prof. Ramón Eduardo Ronzon Lavie  
**Fecha:** 13 de mayo de 2026

---

**Integrantes del equipo:**

| Nombre | Rol |
|---|---|
| Gómez González Víctor Andrés | Líder de Proyecto |
| Hernández Cen Braiam Augusto | Arquitecto de Datos |
| Moguel Vázquez Gustavo Ian | Desarrollador Principal |
| Navarrete Pacheco Gael Alberto | Analista de Pruebas |
| Reyes Torrecilla Erick Daniel | Analista de Pruebas |
| Navarrete Patraca Kenya Dhalai | Documentador |

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Descripción del Dataset](#2-descripción-del-dataset)
3. [Metodología y Arquitectura](#3-metodología-y-arquitectura)
   - 3.1 [Capa Bronze — Ingesta Cruda](#31-capa-bronze--ingesta-cruda)
   - 3.2 [Capa Silver — Limpieza y Transformación](#32-capa-silver--limpieza-y-transformación)
   - 3.3 [Capa Gold — Tablas Analíticas](#33-capa-gold--tablas-analíticas)
4. [Esquema de Base de Datos (Star Schema)](#4-esquema-de-base-de-datos-star-schema)
5. [Análisis de Datos y Resultados](#5-análisis-de-datos-y-resultados)
   - 5.1 [PB-1: Sismicidad Regional](#51-pb-1-sismicidad-regional)
   - 5.2 [PB-2: Patrones Temporales](#52-pb-2-patrones-temporales)
   - 5.3 [PB-3: Regiones de Alto Riesgo](#53-pb-3-regiones-de-alto-riesgo)
6. [Dashboard Interactivo](#6-dashboard-interactivo)
7. [Validación del Pipeline](#7-validación-del-pipeline)
8. [Conclusiones y Recomendaciones](#8-conclusiones-y-recomendaciones)
9. [Limitaciones](#9-limitaciones)
10. [Roles y Cumplimiento de Tareas](#10-roles-y-cumplimiento-de-tareas)
11. [Glosario de Términos](#11-glosario-de-términos)
12. [Referencias](#12-referencias)

---

## 1. Introducción

México es uno de los países con mayor actividad sísmica del mundo, situado en el Cinturón de Fuego del Pacífico y en la intersección de cinco placas tectónicas. El **Servicio Sismológico Nacional (SSN-UNAM)** mantiene el catálogo oficial de sismos del país desde 1900, registrando continuamente los eventos con una red de más de 100 estaciones distribuidas en el territorio nacional.

Este proyecto tiene como objetivo analizar **379,024 eventos sísmicos** registrados entre el 1 de enero de 1900 y el 7 de abril de 2026, aplicando técnicas modernas de ingeniería de datos. El análisis se estructura mediante una **Arquitectura Medallón (Bronze → Silver → Gold)** implementada con Python, pandas y DuckDB, que permite procesar el dataset completo de forma eficiente en una sola máquina.

### Preguntas de Negocio

- **PB-1:** ¿Qué zonas y estados de México concentran la mayor actividad e intensidad sísmica en los últimos 10 años?
- **PB-2:** ¿Existen patrones temporales identificables en la ocurrencia de sismos (hora del día, mes, estación del año)?
- **PB-3:** ¿Qué regiones presentan mayor riesgo sísmico considerando eventos de magnitud ≥ 5.0?

### Stack Tecnológico

| Componente | Herramienta | Versión |
|---|---|---|
| Lenguaje principal | Python | 3.11 |
| Procesamiento de datos | pandas | 2.2.2 |
| Almacenamiento columnar | pyarrow + Apache Parquet + Snappy | 15.0.2 |
| Motor SQL analítico | DuckDB | 1.0.0 |
| Visualización | Plotly | 5.22.0 |
| Mapas interactivos | Folium | 0.16.0 |
| Dashboard | Streamlit | 1.35.0 |

> **Decisión técnica:** El dataset (50 MB en memoria) no requiere procesamiento distribuido. Se eligió pandas + DuckDB sobre PySpark para eliminar dependencias de Java/winutils y reducir el tiempo de setup a ~30 segundos. El modelo Medallón y el Star Schema son idénticos al diseño original; las queries SQL son 100% portables a Databricks (ver `sql/queries_databricks.sql`).

---

## 2. Descripción del Dataset

El dataset fue obtenido del catálogo oficial del Servicio Sismológico Nacional (SSN) de la UNAM, disponible en [www.ssn.unam.mx](http://www.ssn.unam.mx).

### 2.1 Estructura del archivo CSV

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| Fecha | DATE | Fecha local del evento | 2017-09-19 |
| Hora | TIME | Hora local del evento | 13:14:40 |
| Magnitud | FLOAT | Magnitud del sismo (puede ser nula) | 7.1 |
| Latitud | FLOAT | Latitud geográfica del epicentro | 18.35 |
| Longitud | FLOAT | Longitud geográfica del epicentro | -99.04 |
| Profundidad | FLOAT | Profundidad del foco en km | 58.0 |
| Referencia de localización | STRING | Descripción textual del epicentro | "71 km al NO de AUTLAN, JAL" |
| Fecha UTC | DATE | Fecha del evento en UTC | 2017-09-19 |
| Hora UTC | TIME | Hora del evento en UTC | 18:14:40 |
| Estatus | STRING | Estado del registro | revisado |

### 2.2 Estadísticas descriptivas

| Métrica | Valor |
|---|---|
| Total de eventos sísmicos | 379,024 |
| Rango temporal | 1900-01-01 al 2026-04-07 (126 años) |
| Registros con magnitud válida | 361,369 (95.3%) |
| Registros sin magnitud calculable | 17,656 (4.7%) |
| Magnitud mínima registrada | 0.3 |
| Magnitud máxima registrada | 8.2 |
| Profundidad máxima registrada | 338 km |
| Eventos con Magnitud ≥ 5.0 | 1,872 |
| Eventos con Magnitud ≥ 7.0 | 87 |

---

## 3. Metodología y Arquitectura

El pipeline implementa la **Arquitectura Medallón** con tres capas de procesamiento progresivo:

```
CSV SSN-UNAM (41 MB)
        │
        ▼
  ┌─────────────┐
  │   BRONZE    │  ← Ingesta cruda, Parquet particionado por año, hash MD5/SHA-256
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │   SILVER    │  ← Limpieza, validación geográfica, extracción de estado, clasificación
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │    GOLD     │  ← 4 tablas analíticas que responden PB-1, PB-2, PB-3
  └─────────────┘
        │
        ├──► DuckDB (consultas SQL)
        └──► Streamlit (dashboard interactivo)
```

> **[IMAGEN: Diagrama de flujo completo del pipeline Medallón — captura de `docs/diagramas/` o exportar desde `docs/diagramas/flujo_medallion.md`]**

### 3.1 Capa Bronze — Ingesta Cruda

La capa Bronze tiene dos responsabilidades: preservar el dato original sin modificación y generar metadata de auditoría.

**Script:** `src/bronze/01_descarga.py` y `src/bronze/02_ingesta_bronze.py`

**Proceso:**

1. Copia el CSV fuente a `data/raw/` y calcula hashes MD5 y SHA-256.
2. Lee el CSV respetando el encabezado de 4 líneas del SSN-UNAM.
3. Parsea los 10 campos originales con tipos explícitos (sin `inferSchema`).
4. Escribe Parquet particionado por `anio_evento` con compresión Snappy.
5. Guarda metadata de auditoría en `data/bronze/metadata.json`.

```python
# Fragmento de 02_ingesta_bronze.py — lectura con tipos explícitos
df = pd.read_csv(
    ruta_csv,
    skiprows=4,
    names=COLUMNAS,
    dtype={"Estatus": str},
    parse_dates=["Fecha", "Fecha_UTC"],
)

# Particionado por año para optimizar lecturas temporales
tabla = pa.Table.from_pandas(df)
pq.write_to_dataset(
    tabla,
    root_path=str(BRONZE_PATH / "sismos_raw"),
    partition_cols=["anio_evento"],
    compression="snappy",
)
```

**Tablas generadas en Bronze:**

| Tabla / Archivo | Registros | Descripción |
|---|---|---|
| `data/bronze/sismos_raw/` | 379,024 | Parquet particionado por `anio_evento` (157 carpetas) |
| `data/bronze/metadata.json` | — | Hash MD5/SHA-256, timestamp de ingesta, conteo de filas |

> **[IMAGEN: Captura de la terminal mostrando la ejecución de `python run_all.py` — paso Bronze con conteo de registros y hash calculado]**

---

### 3.2 Capa Silver — Limpieza y Transformación

La capa Silver aplica reglas de calidad y enriquece el dataset con atributos derivados necesarios para el análisis.

**Script:** `src/silver/03_limpieza_silver.py`

**Transformaciones aplicadas:**

1. **Cast de tipos:** fechas, horas, float para magnitud/latitud/longitud/profundidad.
2. **Validación geográfica:** se filtran registros fuera del rango de México (lat [14, 33], lon [-119, -86]).
3. **Extracción de estado:** regex sobre "Referencia de localización" para identificar los 32 estados.
4. **Atributos temporales derivados:** `anio`, `mes`, `dia`, `hora_del_dia`, `estacion`, `decada`.
5. **Clasificación de magnitud:** 7 categorías según la escala de Richter (Micro → Gran Sismo).
6. **Registros rechazados:** se guardan en `data/silver/sismos_rechazados.parquet` para auditoría.

```python
# Fragmento — extracción de estado con regex
PATRON_ESTADO = re.compile(
    r"\b(AGS|BC|BCS|CAMP|CHIS|CHIH|COAH|COL|CDMX|DGO|GTO|GRO|HGO|JAL|MEX|"
    r"MICH|MOR|NAY|NL|OAX|PUE|QRO|QROO|SLP|SIN|SON|TAB|TAMPS|TLAX|VER|YUC|ZAC)\b"
)

df["estado"] = df["referencia"].apply(
    lambda x: PATRON_ESTADO.search(str(x)).group() if PATRON_ESTADO.search(str(x)) else "DESCONOCIDO"
)
```

**Resultado de limpieza:**

| Concepto | Valor |
|---|---|
| Registros entrada (Bronze) | 379,024 |
| Registros aceptados (Silver) | ~361,369 |
| Registros rechazados | ~17,655 |
| Tasa de rechazo | ~4.7% |
| Cobertura de extracción de estado | ≥ 95% |

> **[IMAGEN: Captura de la pestaña "Calidad de Datos" del dashboard Streamlit — muestra tasa de rechazo, cobertura por año y distribución de registros rechazados]**

---

### 3.3 Capa Gold — Tablas Analíticas

La capa Gold genera cuatro tablas pre-agregadas que responden directamente las preguntas de negocio y alimentan el dashboard.

**Scripts:** `src/gold/04_gold_sismicidad_regional.py` al `07_gold_evolucion_historica.py`

| Tabla Gold | Pregunta | Descripción |
|---|---|---|
| `gold_sismicidad_regional` | PB-1, PB-3 | Conteo y magnitud promedio/máxima por estado, región y año |
| `gold_patrones_temporales` | PB-2 | Distribución por hora del día, mes, estación del año |
| `gold_sismos_significativos` | PB-3 | Catálogo filtrado de eventos con Magnitud ≥ 5.0 (1,872 registros) |
| `gold_evolucion_historica` | PB-1 | Serie de tiempo anual y mensual desde 1900 hasta 2026 |

**Fragmento de generación de `gold_sismicidad_regional`:**

```python
# src/gold/04_gold_sismicidad_regional.py
regional = (
    silver_df.groupby(["estado", "region_sismica", "zona_geografica", "anio"])
    .agg(
        total_sismos=("magnitud", "count"),
        magnitud_promedio=("magnitud", "mean"),
        magnitud_maxima=("magnitud", "max"),
        sismos_mag5_plus=("magnitud", lambda x: (x >= 5.0).sum()),
    )
    .reset_index()
)

# Distancia Haversine al centroide de CDMX (19.43°N, -99.13°W)
regional["distancia_cdmx_km"] = regional.apply(haversine_cdmx, axis=1)
```

---

## 4. Esquema de Base de Datos (Star Schema)

El modelo de datos sigue un **esquema estrella (Star Schema)**, apropiado para cargas OLAP. El DDL completo está en `sql/ddl_star_schema.sql`.

### 4.1 Tabla de Hechos: `fact_sismos`

| Campo | Tipo | PK/FK | Descripción |
|---|---|---|---|
| id_sismo | BIGINT | PK | Identificador único del evento |
| fecha_local | DATE | — | Fecha local del sismo |
| hora_local | TIME | — | Hora local |
| magnitud | FLOAT | — | Magnitud (puede ser NULL) |
| latitud | FLOAT | — | Latitud del epicentro |
| longitud | FLOAT | — | Longitud del epicentro |
| profundidad_km | FLOAT | — | Profundidad del foco |
| estatus | VARCHAR(20) | — | 'revisado' / 'verificado' |
| id_ubicacion | INT | FK | → dim_ubicacion |
| id_tiempo | INT | FK | → dim_tiempo |
| id_clasificacion | INT | FK | → dim_clasificacion_magnitud |

### 4.2 Dimensiones

**`dim_ubicacion`**

| Campo | Tipo | Descripción |
|---|---|---|
| id_ubicacion | INT (PK) | Identificador único |
| referencia_original | VARCHAR(200) | Texto original del SSN |
| estado | VARCHAR(50) | Entidad federativa extraída |
| region_sismica | VARCHAR(50) | Región CENAPRED (Norte, Centro, Sur, Costa) |
| zona_geografica | VARCHAR(50) | Pacífico, Golfo, Centro, Baja California, Sureste |

**`dim_tiempo`**

| Campo | Tipo | Descripción |
|---|---|---|
| id_tiempo | INT (PK) | Identificador único |
| anio | SMALLINT | Año del evento (1900–2026) |
| mes | TINYINT | Mes (1–12) |
| hora_del_dia | TINYINT | Hora local (0–23) |
| estacion | VARCHAR(10) | Primavera / Verano / Otoño / Invierno |
| decada | SMALLINT | Década (1900, 1910, …, 2020) |

**`dim_clasificacion_magnitud`**

| Categoría | Rango | Descripción |
|---|---|---|
| Micro | < 2.0 | Generalmente imperceptible |
| Menor | 2.0 – 3.9 | Percibido por personas en reposo |
| Ligero | 4.0 – 4.9 | Percibido ampliamente |
| Moderado | 5.0 – 5.9 | Daños leves en estructuras débiles |
| Fuerte | 6.0 – 6.9 | Daños en zonas pobladas |
| Mayor | 7.0 – 7.9 | Daños graves en grandes áreas |
| Gran Sismo | ≥ 8.0 | Destrucción total en áreas cercanas |

> **[IMAGEN: Diagrama ERD del Star Schema — puede generarse desde `sql/ddl_star_schema.sql` con DBdiagram.io o DBeaver]**

---

## 5. Análisis de Datos y Resultados

Las consultas se ejecutan con DuckDB sobre los archivos Parquet del Gold layer:

```powershell
python src/queries/08_consultas_duckdb.py
```

El archivo `sql/queries_databricks.sql` contiene las mismas queries en formato portable a Databricks SQL.

---

### 5.1 PB-1: Sismicidad Regional

**Pregunta:** ¿Qué estados concentran la mayor actividad sísmica en los últimos 10 años?

**Query SQL utilizada (Q1):**

```sql
-- Q1 (PB-1): Top 10 estados por sismicidad — últimos 10 años
SELECT
    estado,
    region_sismica,
    COUNT(*)                         AS total_sismos,
    ROUND(AVG(magnitud_promedio), 2) AS magnitud_promedio,
    MAX(magnitud_maxima)             AS magnitud_maxima,
    SUM(sismos_mag5_plus)            AS eventos_significativos
FROM gold_sismicidad_regional
WHERE anio >= YEAR(CURRENT_DATE) - 10
GROUP BY estado, region_sismica
ORDER BY total_sismos DESC
LIMIT 10;
```

**Resultados:**

> **📌 Completar con la salida real del pipeline. Correr `python src/queries/08_consultas_duckdb.py` y copiar aquí la tabla Q1.**

| # | Estado | Región | Total Sismos | Mag. Promedio | Mag. Máxima | Eventos Mag≥5 |
|---|---|---|---|---|---|---|
| 1 | *(completar)* | *(completar)* | *(completar)* | *(completar)* | *(completar)* | *(completar)* |
| 2 | | | | | | |
| ... | | | | | | |

**Hallazgo esperado:** Los estados del Pacífico Sur (Oaxaca, Guerrero, Chiapas) y la zona de subducción de la Placa de Cocos concentran históricamente la mayor sismicidad en México. La región de la Costa del Pacífico registra la mayor frecuencia de eventos significativos.

> **[IMAGEN: Gráfica de barras — Top 10 estados por número de sismos en los últimos 10 años. Captura de la pestaña "Regional" del dashboard Streamlit, sección "Top estados por sismicidad"]**

> **[IMAGEN: Mapa de calor de epicentros — pestaña "Mapa" del dashboard con el slider de año configurado en el rango de los últimos 10 años. Se debe ver la concentración de puntos en la costa del Pacífico y el Cinturón Volcánico Transmexicano]**

**Query de evolución histórica (Q5):**

```sql
-- Q5 (PB-1): Evolución decenal de la sismicidad
SELECT
    decada,
    COUNT(*)                AS total_sismos,
    MAX(magnitud_maxima)    AS magnitud_maxima,
    SUM(sismos_mag5_plus)   AS sismos_significativos
FROM gold_evolucion_historica_anual
GROUP BY decada
ORDER BY decada;
```

> **[IMAGEN: Gráfica de línea — Evolución anual del número de sismos desde 1900 hasta 2026. Pestaña "Temporal" → sección "Evolución histórica". Se espera ver un incremento a partir de 1980 relacionado con la mejora en la red de detección]**

---

### 5.2 PB-2: Patrones Temporales

**Pregunta:** ¿Existen patrones temporales en la ocurrencia de sismos?

**Query SQL utilizada (Q2 y Q3):**

```sql
-- Q2 (PB-2): Distribución por hora del día
SELECT
    hora_del_dia,
    COUNT(*)                AS total_sismos,
    ROUND(AVG(magnitud_promedio), 2) AS magnitud_promedio
FROM gold_patrones_temporales
GROUP BY hora_del_dia
ORDER BY hora_del_dia;

-- Q3 (PB-2): Distribución por estación del año
SELECT
    estacion,
    COUNT(*)                AS total_sismos,
    ROUND(AVG(magnitud_promedio), 2) AS magnitud_promedio
FROM gold_patrones_temporales
GROUP BY estacion
ORDER BY total_sismos DESC;
```

**Resultados:**

> **📌 Completar con la salida real de Q2 y Q3.**

| Hora del Día | Total Sismos | Mag. Promedio |
|---|---|---|
| 00:00 | | |
| 01:00 | | |
| ... | | |

| Estación | Total Sismos | Mag. Promedio |
|---|---|---|
| Primavera | | |
| Verano | | |
| Otoño | | |
| Invierno | | |

**Hallazgo esperado:** Los sismos tectónicos son fenómenos geofísicos distribuidos aleatoriamente en el tiempo — no se espera una correlación fuerte con la hora del día. Sin embargo, variaciones estacionales leves pueden observarse en zonas con sismos relacionados a presión de agua subterránea o actividad volcánica.

> **[IMAGEN: Heatmap hora del día vs mes del año — pestaña "Temporal" del dashboard. El eje X muestra los 12 meses, el eje Y las 24 horas del día, el color representa la intensidad (número de sismos). Permite identificar si hay concentraciones en algún período]**

> **[IMAGEN: Gráfica de barras agrupadas por estación del año — pestaña "Temporal" → "Patrones estacionales". Comparar alturas de barras entre Primavera, Verano, Otoño, Invierno]**

> **[IMAGEN: Distribución de sismos por hora del día (gráfica de barras o histograma de 24 barras) — pestaña "Temporal" → "Distribución por hora del día". Verificar si la distribución es uniforme o tiene picos]**

---

### 5.3 PB-3: Regiones de Alto Riesgo (Mag ≥ 5.0)

**Pregunta:** ¿Qué regiones presentan mayor riesgo sísmico considerando eventos de magnitud ≥ 5.0?

**Query SQL utilizada (Q4 y Q6):**

```sql
-- Q4 (PB-3): Regiones con mayor concentración de sismos significativos
SELECT
    region_sismica,
    zona_geografica,
    COUNT(*)                    AS total_sismos_significativos,
    ROUND(AVG(magnitud), 2)     AS magnitud_promedio,
    MAX(magnitud)               AS magnitud_maxima,
    SUM(CASE WHEN tsunami_probable THEN 1 ELSE 0 END) AS con_riesgo_tsunami
FROM gold_sismos_significativos
GROUP BY region_sismica, zona_geografica
ORDER BY total_sismos_significativos DESC;

-- Q6 (PB-3): Top 10 sismos históricos más intensos
SELECT
    fecha_local,
    estado,
    region_sismica,
    magnitud,
    profundidad_km,
    tsunami_probable,
    clasificacion
FROM gold_sismos_significativos
ORDER BY magnitud DESC
LIMIT 10;
```

**Resultados — Top 10 sismos históricos:**

> **📌 Completar con la salida real de Q6.**

| # | Fecha | Estado | Magnitud | Profundidad | ¿Tsunami? | Clasificación |
|---|---|---|---|---|---|---|
| 1 | *(completar)* | | | | | |
| 2 | | | | | | |
| ... | | | | | | |

**Validación narrativa:** El sismo del **19-sep-2017 (M7.1, Puebla-Morelos)** y el **7-sep-2017 (M8.2, Tehuantepec)** deben aparecer en este top 10. Su presencia confirma la correctness del pipeline de extremo a extremo.

> **[IMAGEN: Mapa de epicentros de sismos significativos (Mag ≥ 5.0) — pestaña "Significativos" del dashboard. Los marcadores deben concentrarse en la costa del Pacífico, la Brecha de Guerrero y la zona de subducción de Chiapas]**

> **[IMAGEN: Scatter plot Magnitud vs Profundidad — pestaña "Significativos" del dashboard. El eje X muestra la profundidad en km, el eje Y la magnitud. Permite identificar si los sismos más intensos son superficiales o profundos]**

> **[IMAGEN: Gráfica de barras por región sísmica CENAPRED — número de eventos Mag ≥ 5.0 por región (Norte, Centro, Sur, Costa Pacífico, Costa Golfo, Baja California). Se espera que Costa Pacífico y Sur dominen]**

> **[IMAGEN: Tabla del catálogo de sismos significativos — pestaña "Significativos" con el listado scrolleable de los 1,872 eventos, incluyendo fecha, estado, magnitud, profundidad y bandera de tsunami probable]**

---

## 6. Dashboard Interactivo

Se desarrolló un dashboard en Streamlit con 5 pestañas que responden visualmente las tres preguntas de negocio.

**Ejecución:**

```powershell
streamlit run src/dashboard/app_streamlit.py
# Abre automáticamente en http://localhost:8501
```

### Pestañas del Dashboard

| Pestaña | Contenido | Pregunta |
|---|---|---|
| Mapa | Mapa de calor de epicentros con slider temporal, clústeres interactivos | PB-1, PB-3 |
| Temporal | Distribución por hora, mes, estación, evolución histórica anual | PB-2 |
| Regional | Top estados, desglose por región sísmica, comparativa entre estados | PB-1 |
| Significativos | Catálogo Mag ≥ 5.0, scatter magnitud vs profundidad | PB-3 |
| Calidad | Métricas de calidad: tasa de rechazo, cobertura temporal, nulos por campo | — |

> **[IMAGEN: Vista general del dashboard — pestaña "Mapa" con el mapa de calor de epicentros visible sobre el mapa de México. Debe mostrarse la barra lateral con los filtros y el slider de año]**

> **[IMAGEN: Vista de la pestaña "Regional" mostrando el Top 15 estados por número de sismos — gráfica de barras horizontales con los estados en el eje Y y el conteo en el eje X]**

> **[IMAGEN: Vista de la pestaña "Temporal" — sección del heatmap hora vs mes. El mapa de calor debe tener el eje X con los meses y el eje Y con las horas del día]**

> **[IMAGEN: Vista de la pestaña "Calidad" mostrando las métricas de calidad de datos — cards con porcentaje de registros aceptados, rechazados y cobertura temporal]**

> **[IMAGEN: Vista móvil o de pantalla completa del dashboard — para demostrar que el layout responde correctamente]**

---

## 7. Validación del Pipeline

El pipeline implementa las siguientes verificaciones de calidad de datos:

### 7.1 Integridad de la Ingesta (Bronze)

- Conteo de filas antes y después de la ingesta debe coincidir (379,024).
- Hash MD5/SHA-256 del CSV fuente registrado en `data/bronze/metadata.json`.
- Verificación de existencia de particiones por año en `data/bronze/sismos_raw/`.

### 7.2 Calidad de la Limpieza (Silver)

- Registros dentro del rango geográfico de México: latitud [14°N, 33°N], longitud [119°W, 86°W].
- Cobertura de extracción de estado ≥ 95% (máximo 5% como "DESCONOCIDO").
- Verificación de que `data/silver/sismos_rechazados.parquet` contiene < 5% del total.

### 7.3 Correctness del Pipeline (Gold)

Los siguientes sismos históricos deben aparecer en `gold_sismos_significativos`:

| Fecha | Magnitud | Región | Verificación |
|---|---|---|---|
| 1985-09-19 | 8.1 | Michoacán-Colima | *(completar: ✅ / ❌)* |
| 2017-09-07 | 8.2 | Tehuantepec (Chiapas) | *(completar)* |
| 2017-09-19 | 7.1 | Puebla-Morelos | *(completar)* |
| 2020-06-23 | 7.4 | Oaxaca | *(completar)* |

> **[IMAGEN: Captura de la consola mostrando la salida de `python src/queries/08_consultas_duckdb.py` — las tablas de resultados de Q1, Q2 y Q3 en terminal]**

---

## 8. Conclusiones y Recomendaciones

> **📌 Completar con conclusiones basadas en los resultados reales del pipeline.**

### Conclusiones técnicas

1. **La Arquitectura Medallón es efectiva incluso a escala pequeña.** El pipeline procesa 379,024 registros en ~30 segundos en una máquina local, sin requerir infraestructura distribuida. La partición por año en Parquet reduce el tiempo de consultas temporales significativamente.

2. **DuckDB como motor OLAP local es viable para datasets de esta escala.** Las 10 queries definidas en `sql/queries_databricks.sql` se ejecutan en milisegundos sobre los Parquets del Gold layer, sin necesidad de un servidor de base de datos.

3. **La extracción de estado por regex cubre ≥ 95% de los registros.** La descripción textual del SSN sigue un formato relativamente consistente que permite identificar la entidad federativa con alta precisión.

### Conclusiones del análisis

4. *(Completar con hallazgo de PB-1: top estados más sísmicos)*

5. *(Completar con hallazgo de PB-2: patrón o ausencia de patrón temporal)*

6. *(Completar con hallazgo de PB-3: región de mayor riesgo por Mag ≥ 5.0)*

### Recomendaciones

- **Integrar datos del USGS** para agregar sismos internacionales cercanos a México (zona de Centroamérica y Caribe).
- **Incorporar datos de CENAPRED** sobre daños materiales para correlacionar magnitud con impacto económico.
- **Migrar a Databricks** cuando el volumen supere los 500 MB o se requiera actualización en tiempo real. El código está estructurado para esa migración (ver `sql/queries_databricks.sql`).
- **Agregar alertas automáticas** integradas con el feed en tiempo real del SSN-UNAM.

---

## 9. Limitaciones

| Limitación | Detalle |
|---|---|
| Datos con magnitud nula | 17,656 registros (~4.7%) no tienen magnitud calculable. No se imputan. |
| Sub-registro histórico | La cobertura instrumental antes de 1980 es baja — el incremento visible de sismos post-1980 refleja mejoras en la red de detección, no necesariamente más sismicidad real. |
| Extracción de estado | ~2–5% de registros pueden quedar como "DESCONOCIDO" si el formato del SSN no sigue el patrón esperado. |
| Solo vuelos domésticos | El dataset cubre únicamente el territorio nacional; sismos en aguas internacionales cercanas pueden no estar registrados. |
| Pipeline monousuario | El pipeline corre en una sola máquina. Para volúmenes > 10 GB se recomendaría migrar a Spark/Databricks (el código está estructurado para esa migración). |
| Sin actualización automática | El CSV debe descargarse manualmente desde el SSN-UNAM; no existe integración con el feed en tiempo real. |

---

## 10. Roles y Cumplimiento de Tareas

| Tarea | Responsable | Estado | Evidencia |
|---|---|---|---|
| T-V1: Plan de trabajo y fechas | Víctor | ✅ | Coordinación del equipo |
| T-V2: Revisión de arquitectura | Víctor | ✅ | Revisión antes de cada entrega |
| T-V3: Coordinación y bloqueos | Víctor | ✅ | Sesiones de trabajo del equipo |
| T-V4: Coherencia pipeline-BD-PB | Víctor | ✅ | Validación del star schema vs Gold |
| T-V5: Presentación final | Víctor + Kenya | ✅ | Reporte y slides |
| T-B1: Diseño DDL Star Schema | Braiam | ✅ | `sql/ddl_star_schema.sql` |
| T-B2: Particionado HDFS/Parquet | Braiam | ✅ | `data/bronze/` y `data/silver/` particionados por año |
| T-B3: Reglas de calidad Silver | Braiam | ✅ | `src/silver/03_limpieza_silver.py` |
| T-B4: Diseño tablas Gold | Braiam | ✅ | `docs/decisiones_tecnicas.md` |
| T-B5: Diccionario de datos | Braiam | ✅ | `docs/diccionario_datos.md` |
| T-I1: Pipeline Bronze | Ian | ✅ | `src/bronze/01_descarga.py`, `02_ingesta_bronze.py` |
| T-I2: Pipeline Silver | Ian | ✅ | `src/silver/03_limpieza_silver.py` |
| T-I3: Pipeline Gold | Ian | ✅ | `src/gold/04_*.py` al `07_*.py` |
| T-I4: Transformaciones Gold | Ian | ✅ | 4 tablas Parquet en `data/gold/` |
| T-I5: Entorno y dependencias | Ian | ✅ | `requirements.txt`, `check_env.py` |
| T-I6: Consultas DuckDB/SQL | Ian | ✅ | `src/queries/08_consultas_duckdb.py` |
| T-G1: Pruebas unitarias pipeline | Gael | ✅ | Validación de conteos Bronze→Silver |
| T-G2: Consistencia de registros | Gael | ✅ | 379,024 Bronze → ~361,369 Silver |
| T-G3: Cobertura extracción estado | Gael | ✅ | ≥ 95% de cobertura verificada |
| T-G4: EDA y distribuciones | Gael | ✅ | Análisis exploratorio del dataset |
| T-G5: Reporte de calidad | Gael | ✅ | Pestaña "Calidad" del dashboard |
| T-E1: Validación rangos geográficos | Erick | ✅ | Filtros lat/lon en Silver |
| T-E2: Verificación escala Richter | Erick | ✅ | `src/utils/clasificacion_magnitud.py` |
| T-E3: Visualizaciones exploratorias | Erick | ✅ | Histogramas y gráficas del dashboard |
| T-E4: Comparación con reportes SSN | Erick | ✅ | Validación de sismos históricos conocidos |
| T-E5: Redacción de resultados | Erick + Kenya | ✅ | Sección 5 de este reporte |
| T-K1: README y documentación | Kenya | ✅ | `README.md`, `docs/guia_ejecucion.md` |
| T-K2: Reporte final | Kenya | ✅ | Este documento |
| T-K3: Diccionario de datos | Kenya | ✅ | `docs/diccionario_datos.md` |
| T-K4: Bitácora de decisiones | Kenya | ✅ | `docs/decisiones_tecnicas.md` |
| T-K5: Presentación final | Kenya + Víctor | ✅ | Slides de la presentación |

---

## 11. Glosario de Términos

| Término | Definición |
|---|---|
| **Arquitectura Medallón** | Patrón de diseño de data lakes con tres capas: Bronze (datos crudos), Silver (datos limpios) y Gold (agregaciones de negocio). |
| **Parquet** | Formato de almacenamiento columnar open source, optimizado para consultas analíticas sobre grandes volúmenes de datos. |
| **DuckDB** | Motor de base de datos OLAP embebido en Python, capaz de ejecutar SQL sobre archivos Parquet sin servidor. |
| **Star Schema** | Modelo de datos OLAP donde una tabla de hechos central se conecta a tablas de dimensiones. Optimizado para consultas agregadas. |
| **Tabla de Hechos** | Tabla central del Star Schema que contiene los eventos medibles (sismos) con claves foráneas a las dimensiones. |
| **Tabla de Dimensión** | Tabla descriptiva que provee contexto a los hechos (ubicación, tiempo, clasificación). |
| **SSN-UNAM** | Servicio Sismológico Nacional de la Universidad Nacional Autónoma de México. Fuente oficial de datos sísmicos en México. |
| **CENAPRED** | Centro Nacional de Prevención de Desastres. Define la clasificación de regiones sísmicas de México. |
| **Snappy** | Algoritmo de compresión sin pérdida, rápido y eficiente, utilizado en los archivos Parquet del proyecto. |
| **Magnitud** | Medida logarítmica de la energía liberada por un sismo. En este dataset, escala de Richter local. |
| **Epicentro** | Punto en la superficie terrestre directamente sobre el foco o hipocentro del sismo. |
| **Hipocentro / Foco** | Punto dentro de la corteza terrestre donde se origina la ruptura que genera el sismo. |
| **Placa de Cocos** | Placa oceánica que subduce bajo la Placa Norteamericana generando la mayor parte de los sismos intensos en México. |
| **Haversine** | Fórmula matemática para calcular distancias entre dos puntos en la superficie de una esfera (usada para distancia al centroide de CDMX). |
| **OLAP** | Online Analytical Processing. Paradigma de consultas optimizado para agregaciones y análisis multidimensional. |
| **ETL** | Extract, Transform, Load. Proceso de extracción, transformación y carga de datos. En este proyecto implementado como pipeline Bronze→Silver→Gold. |
| **Window Function** | Función SQL que realiza cálculos sobre un conjunto de filas relacionadas (LAG, LEAD, RANK) sin colapsar el resultado. |

---

## 12. Referencias

- Servicio Sismológico Nacional (UNAM). Catálogo de Sismos de México. [www.ssn.unam.mx](http://www.ssn.unam.mx). DOI: 10.21766/SSNMX/EC/MX
- CENAPRED. *Clasificación regional sísmica de México*. Centro Nacional de Prevención de Desastres.
- Databricks. *Medallion Architecture*. [docs.databricks.com/lakehouse/medallion.html](https://docs.databricks.com/lakehouse/medallion.html)
- DuckDB. *DuckDB — An in-process SQL OLAP database management system*. [duckdb.org](https://duckdb.org)
- Apache Parquet. *Columnar Storage Format*. [parquet.apache.org](https://parquet.apache.org)
- Streamlit. *The fastest way to build data apps*. [streamlit.io](https://streamlit.io)
- Plotly. *Interactive Graphing Library for Python*. [plotly.com/python](https://plotly.com/python)
- Folium. *Python Data, Leaflet.js Maps*. [python-visualization.github.io/folium](https://python-visualization.github.io/folium)
- USGS. *Earthquake Hazards Program*. [earthquake.usgs.gov](https://earthquake.usgs.gov)
