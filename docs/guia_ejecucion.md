# Guía de Ejecución - Proyecto SSN-UNAM v2

Este archivo resume cómo correr el proyecto de punta a punta, qué hace cada carpeta y cómo usar los resultados para el reporte final.

## 1. Qué hace este repositorio

El proyecto implementa un pipeline de datos de sismos del SSN-UNAM con arquitectura Bronze → Silver → Gold.

- `Bronze`: copia cruda del CSV y registro de hashes.
- `Silver`: limpieza, validación, georreferenciación y clasificación.
- `Gold`: tablas agregadas listas para análisis y dashboard.
- `Streamlit`: dashboard interactivo local.
- `DuckDB / SQL`: consultas analíticas locales y portables a Databricks.
- `DuckDB / SQL`: consultas analíticas locales y portables a Databricks.

## 2. Requisitos mínimos

- Python 3.9 o superior.
- Activar la `venv` del proyecto.
- Instalar dependencias con `pip install -r requirements.txt`.
- Tener disponible el CSV fuente del SSN-UNAM.

## 3. Cómo correrlo en local

### 3.1 Preparar entorno

```powershell
cd "Ruta donde se tenga el Repositorio"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3.2 Verificar el entorno

```powershell
python check_env.py
```

Este script valida:
- versión de Python,
- dependencias instaladas,
- existencia del CSV de entrada.

### 3.3 Ejecutar todo el pipeline

```powershell
python run_all.py
```

Orden real de ejecución:
1. Verificación de entorno.
2. Copia del CSV a `data/raw/` y cálculo de hashes.
3. Ingesta Bronze a Parquet particionado.
4. Limpieza Silver.
5. Generación de tablas Gold.
6. Ejecución de consultas DuckDB.

## 4. Qué genera cada carpeta

### `config/`
Configuración central.

- Rutas base.
- Rango geográfico válido.
- Mapeo de estados y regiones.
- Clasificación de magnitud.

Variables útiles:
- `SSN_CSV_FUENTE`: permite apuntar al CSV fuente desde otra ruta.
- `SSN_PROJECT_ROOT`: útil si corres scripts desde una ruta distinta a la raíz del proyecto.

### `data/`
Salida real del pipeline.

- `data/raw/`: copia exacta del CSV fuente.
- `data/bronze/`: Parquet crudo particionado por año.
- `data/silver/`: Parquet limpio y validado.
- `data/gold/`: tablas analíticas pre-agregadas.

### `src/bronze/`

- `01_descarga.py`: copia el CSV y calcula MD5/SHA256.
- `02_ingesta_bronze.py`: lee el CSV crudo y escribe Bronze en Parquet.

### `src/silver/`

- `03_limpieza_silver.py`: limpia tipos, filtra geografía, extrae estado y clasifica magnitud.

### `src/gold/`

- `04_gold_sismicidad_regional.py`: estado, región, año.
- `05_gold_patrones_temporales.py`: hora, día, mes, estación.
- `06_gold_sismos_significativos.py`: sismos con magnitud mayor o igual a 5.0.
- `07_gold_evolucion_historica.py`: evolución anual y mensual.

### `src/queries/`

- `08_consultas_duckdb.py`: levanta vistas sobre Parquet y responde PB-1, PB-2 y PB-3.

### `src/dashboard/`

- `app_streamlit.py`: dashboard interactivo con mapas, gráficas y métricas.

### `sql/`

- `ddl_star_schema.sql`: modelo estrella teórico.
- `queries_databricks.sql`: queries SQL listas para Databricks o SQL compatible.

## 5. Cómo correr el dashboard

Primero corre el pipeline completo. Después:

```powershell
streamlit run src/dashboard/app_streamlit.py
```

Abre en el navegador:
- `http://localhost:8501`

Si el dashboard falla, normalmente significa que no existe la capa Gold o que Silver no fue generada.

### Dónde tocar el diseño

Si después quieres moverle al estilo del dashboard, el archivo principal es `src/dashboard/app_streamlit.py`.

- El bloque `CSS` controla colores, tipografía, tarjetas y pestañas.
- `PLOTLY_THEME` controla el estilo de las gráficas.
- `st.set_page_config(...)` controla layout, título e ícono.
- Las pestañas del dashboard están más abajo en el mismo archivo.

## 6. Qué hacer con `08_consultas_duckdb.py`

Ese script imprime resultados en consola. No genera archivo por defecto.

### Dónde ver el SQL

La salida aparece en la terminal donde ejecutas:

```powershell
python src/queries/08_consultas_duckdb.py
```

Ahí verás tablas ya resueltas con PB-1, PB-2, PB-3 y extras.

Si quieres guardar el resultado para el reporte, usa PowerShell y redirige la salida:

```powershell
python src/queries/08_consultas_duckdb.py > docs/resultados_sql.txt
```

O bien copia y pega las tablas directamente en `REPORTE_FINAL.md`.

### Qué significa el output

- PB-1: top estados por sismicidad reciente.
- PB-2: patrones por hora y estación.
- PB-3: regiones con más eventos significativos.

### Qué debes hacer con ese output

1. Copiar los valores clave al `REPORTE_FINAL.md`.
2. Tomar captura de la consola o pegar los resultados en una tabla del reporte.
3. Usar esos resultados como evidencia de que el pipeline sí respondió las preguntas de negocio.

### Qué no hacer

- No lo dejes solo en consola si tu entrega final es un reporte.
- No uses tablas Gold sin mencionar la query que las generó.

## 7. Cómo usar SQL / Databricks

La carpeta `sql/` no está pensada para Angular. Está pensada para análisis SQL.

### En local

Si quieres ejecutar las consultas con DuckDB, usa:

```powershell
python src/queries/08_consultas_duckdb.py
```

### En Databricks

1. Sube `data/gold/` a DBFS o a un storage accesible.
2. Crea vistas externas sobre los Parquet.
3. Ejecuta `sql/queries_databricks.sql`.

### Contrato mínimo de vistas

Las queries esperan estas tablas/vistas:
- `gold_sismicidad_regional`
- `gold_patrones_temporales`
- `gold_sismos_significativos`
- `gold_evolucion_historica_anual`
- `gold_evolucion_historica_mensual`

## 8. Cómo conectar Angular

En este repositorio no existe una app Angular todavía. Lo que sí existe es una base de datos analítica en Parquet y SQL.

### Recomendación práctica

Si quieres que Angular consuma el proyecto, la forma correcta es exponer un API REST intermedio. El contrato sugerido sería:

- `GET /api/gold/sismicidad-regional`
- `GET /api/gold/patrones-temporales`
- `GET /api/gold/sismos-significativos`
- `GET /api/gold/evolucion-anual`
- `GET /api/gold/evolucion-mensual`
- `GET /api/health`

Angular consumiría esos endpoints con `HttpClient`.

### Qué representa cada ruta

- Regional: top estados y regiones.
- Temporal: hora, mes y estación.
- Significativos: eventos con magnitud mayor o igual a 5.0.
- Evolución: series de tiempo anual y mensual.

## 9. Sobre Antigravity

No existe integración nativa con Antigravity dentro del repo.

### Para conectarlo de forma razonable

Necesitas una de estas dos opciones:

1. Consumir los Parquet de `data/gold/` directamente si la herramienta lo permite.
2. Pasar por un API intermedio que entregue JSON.

### Flujo recomendado para Antigravity

Si Antigravity no lee Parquet directo, el flujo práctico es este:

1. Corre `python run_all.py`.
2. Deja listas las tablas de `data/gold/`.
3. Expón un API simple que lea esos Parquet y regrese JSON.
4. Conecta Antigravity a ese API o importa los archivos resultantes.

### Qué conviene usar

- Si Antigravity acepta datasets locales, usa `data/gold/`.
- Si requiere endpoints, usa el contrato de API anterior.

## 10. Orden de trabajo recomendado para la entrega

### Fase 1: dejarlo corriendo

1. `python check_env.py`
2. `python run_all.py`
3. `streamlit run src/dashboard/app_streamlit.py`

### Fase 2: evidencias

1. Ejecuta `08_consultas_duckdb.py` y guarda el output.
2. Abre Streamlit y toma capturas de cada pestaña.
3. Guarda las capturas en `docs/diagramas/`.

### Fase 3: reporte

1. Llena `REPORTE_FINAL.md` con los resultados reales.
2. Inserta capturas del dashboard.
3. Resume PB-1, PB-2 y PB-3 con números concretos.

## 11. Problemas comunes

### El CSV no se encuentra

Solución:
- definir `SSN_CSV_FUENTE`, o
- copiar el CSV al directorio del proyecto.

### Streamlit no abre

Solución:
- revisar que la Gold exista,
- volver a correr `python run_all.py`,
- abrir `http://localhost:8501` manualmente.

### Databricks no ve las tablas

Solución:
- subir los Parquet de `data/gold/`,
- crear las vistas externas,
- revisar nombres exactos de las vistas.

## 12. Resumen corto del flujo correcto

```text
CSV fuente -> run_all.py -> Bronze -> Silver -> Gold -> DuckDB -> Streamlit -> Reporte
```

Si algo no aparece en el dashboard o en SQL, normalmente significa que el paso anterior no corrió.
