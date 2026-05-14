import duckdb, os

db_path = r'C:\Users\vican\OneDrive\Escritorio\Claude Code\proyecto_sismos_v2\sismos.duckdb'
base = r'C:\Users\vican\OneDrive\Escritorio\Claude Code\proyecto_sismos_v2\data\gold'

con = duckdb.connect(db_path)

views = [
    'gold_sismicidad_regional',
    'gold_sismos_significativos',
    'gold_patrones_temporales',
    'gold_evolucion_historica_anual',
    'gold_evolucion_historica_mensual',
]

for view_name in views:
    folder_path = os.path.join(base, view_name)
    if os.path.exists(folder_path):
        parquet_glob = folder_path.replace('\\', '/') + '/**/*.parquet'
        con.execute(f"CREATE VIEW {view_name} AS SELECT * FROM read_parquet('{parquet_glob}', hive_partitioning=true)")
        count = con.execute(f'SELECT COUNT(*) FROM {view_name}').fetchone()[0]
        print(f'  {view_name}: {count:,} registros')
    else:
        print(f'  SKIP {view_name}: carpeta no encontrada')

con.close()
print('\nsismos.duckdb listo!')
