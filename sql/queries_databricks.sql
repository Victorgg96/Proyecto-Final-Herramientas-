-- ============================================================================
-- Queries Databricks SQL / DuckDB - Analisis Sismico SSN-UNAM
-- En Databricks: subir Gold a DBFS y crear vistas externas:
--   CREATE OR REPLACE TEMP VIEW gold_sismicidad_regional
--   USING parquet OPTIONS (path '/dbfs/ruta/gold_sismicidad_regional');
-- En DuckDB local: ya se crean automaticamente en 08_consultas_duckdb.py.
-- ============================================================================

-- Q1 (PB-1): Top 10 estados con mayor sismicidad - ultimos 10 anios
SELECT estado,
       SUM(total_sismos)              AS total_sismos,
       ROUND(AVG(magnitud_promedio),2) AS mag_prom,
       MAX(magnitud_maxima)           AS mag_max,
       SUM(sismos_mag5_plus)          AS eventos_mag5_plus
FROM gold_sismicidad_regional
WHERE anio >= 2016
GROUP BY estado
ORDER BY total_sismos DESC
LIMIT 10;

-- Q2 (PB-2): Patrones por hora del dia
SELECT hora_del_dia,
       SUM(total_sismos)              AS total,
       ROUND(AVG(magnitud_promedio),2) AS mag_prom
FROM gold_patrones_temporales
WHERE hora_del_dia IS NOT NULL
GROUP BY hora_del_dia
ORDER BY hora_del_dia;

-- Q3 (PB-2): Distribucion por estacion del anio
SELECT estacion,
       SUM(total_sismos) AS total,
       ROUND(AVG(magnitud_promedio),2) AS mag_prom
FROM gold_patrones_temporales
GROUP BY estacion
ORDER BY total DESC;

-- Q4 (PB-3): Region sismica con mayor riesgo (mag >= 5.0)
SELECT region_sismica,
       COUNT(*)              AS eventos_significativos,
       ROUND(AVG(magnitud),2) AS mag_prom,
       MAX(magnitud)          AS mag_max
FROM gold_sismos_significativos
GROUP BY region_sismica
ORDER BY eventos_significativos DESC;

-- Q5: Top 10 sismos historicos mas fuertes
SELECT fecha_local, magnitud, estado, region_sismica, profundidad_km, distancia_cdmx_km
FROM gold_sismos_significativos
ORDER BY magnitud DESC
LIMIT 10;

-- Q6: Evolucion por decada
SELECT decada,
       SUM(total_sismos)     AS total,
       SUM(sismos_mag5_plus) AS mag5_plus,
       SUM(sismos_mag7_plus) AS mag7_plus,
       MAX(magnitud_maxima)  AS mag_max
FROM gold_evolucion_historica_anual
GROUP BY decada
ORDER BY decada;

-- Q7: Profundidad promedio por zona geografica
SELECT zona_geografica,
       ROUND(AVG(profundidad_promedio),2) AS prof_prom_km,
       SUM(total_sismos) AS total
FROM gold_sismicidad_regional
GROUP BY zona_geografica
ORDER BY total DESC;

-- Q8: Heatmap anual de eventos >=5.0 por region
SELECT anio, region_sismica, COUNT(*) AS eventos
FROM gold_sismos_significativos
GROUP BY anio, region_sismica
ORDER BY anio DESC, eventos DESC;

-- Q9: Sismos con riesgo de tsunami (mag>=7 en costa/pacifico)
SELECT fecha_local, magnitud, estado, profundidad_km, latitud, longitud
FROM gold_sismos_significativos
WHERE tsunami_probable = TRUE
ORDER BY magnitud DESC;

-- Q10: Validacion de eventos historicos conocidos
SELECT fecha_local, magnitud, estado, region_sismica
FROM gold_sismos_significativos
WHERE fecha_local IN (DATE '2017-09-19', DATE '2017-09-07', DATE '1985-09-19')
ORDER BY fecha_local;
