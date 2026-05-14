# Guía de Ejecución - Proyecto SSN-UNAM

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