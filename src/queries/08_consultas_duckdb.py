"""Consultas analiticas con DuckDB sobre la capa Gold. Responde PB-1, PB-2, PB-3."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import GOLD_PATH, SILVER_PATH


def main():
    con = duckdb.connect()

    con.execute(f"""
        CREATE VIEW fact_sismos AS
        SELECT * FROM read_parquet('{SILVER_PATH}/**/*.parquet', hive_partitioning=1)
    """)
    for nombre in ["gold_sismicidad_regional", "gold_patrones_temporales",
                   "gold_sismos_significativos", "gold_evolucion_historica_anual"]:
        con.execute(f"""
            CREATE VIEW {nombre} AS
            SELECT * FROM read_parquet('{GOLD_PATH / nombre}/*.parquet')
        """)

    def show(titulo, sql, limit=20):
        print(f"\n=== {titulo} ===")
        print(con.execute(sql).fetch_df().head(limit).to_string(index=False))

    show("PB-1: Top 10 estados con mayor sismicidad (ultimos 10 anios)", """
        SELECT estado,
               SUM(total_sismos) AS total_sismos,
               ROUND(AVG(magnitud_promedio), 2) AS mag_prom,
               MAX(magnitud_maxima) AS mag_max,
               SUM(sismos_mag5_plus) AS eventos_fuertes
        FROM gold_sismicidad_regional
        WHERE anio >= 2016
        GROUP BY estado
        ORDER BY total_sismos DESC
        LIMIT 10
    """)

    show("PB-2: Sismos por hora del dia", """
        SELECT hora_del_dia,
               SUM(total_sismos) AS total,
               ROUND(AVG(magnitud_promedio), 2) AS mag_prom
        FROM gold_patrones_temporales
        WHERE hora_del_dia IS NOT NULL
        GROUP BY hora_del_dia
        ORDER BY hora_del_dia
    """, limit=24)

    show("PB-2b: Distribucion por estacion del anio", """
        SELECT estacion, SUM(total_sismos) AS total
        FROM gold_patrones_temporales
        GROUP BY estacion
        ORDER BY total DESC
    """)

    show("PB-3: Region sismica con mayor riesgo (mag >= 5.0)", """
        SELECT region_sismica,
               COUNT(*) AS eventos_significativos,
               ROUND(AVG(magnitud), 2) AS mag_prom,
               MAX(magnitud) AS mag_max
        FROM gold_sismos_significativos
        GROUP BY region_sismica
        ORDER BY eventos_significativos DESC
    """)

    show("Extra: Top 10 sismos mas fuertes de la historia", """
        SELECT fecha_local, magnitud, estado, region_sismica, profundidad_km
        FROM gold_sismos_significativos
        ORDER BY magnitud DESC
        LIMIT 10
    """)

    show("Extra: Evolucion por decada", """
        SELECT decada,
               SUM(total_sismos) AS total,
               SUM(sismos_mag5_plus) AS mag5_plus,
               SUM(sismos_mag7_plus) AS mag7_plus,
               MAX(magnitud_maxima) AS mag_max
        FROM gold_evolucion_historica_anual
        GROUP BY decada
        ORDER BY decada
    """)

    con.close()


if __name__ == "__main__":
    main()
