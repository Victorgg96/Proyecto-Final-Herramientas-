"""B-3, B-4, B-5: Lee CSV crudo con pandas y escribe Parquet particionado por anio."""
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import RAW_CSV, BRONZE_PATH, SKIP_HEADER_LINES


def main():
    print(f"[B-3] Leyendo CSV crudo desde {RAW_CSV}")
    df = pd.read_csv(
        RAW_CSV,
        skiprows=SKIP_HEADER_LINES,
        encoding="latin1",
        dtype=str,
    )

    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df["anio_evento"] = (
        pd.to_datetime(df["Fecha"], errors="coerce").dt.year.fillna(-1).astype(int)
    )
    df["ingesta_ts"] = pd.Timestamp.now().isoformat()
    df["capa"] = "bronze"

    print(f"[B-3] Registros cargados: {len(df):,}")
    print(f"[B-4] Columnas: {list(df.columns)}")

    if BRONZE_PATH.exists():
        for f in BRONZE_PATH.rglob("*.parquet"):
            try: f.unlink()
            except PermissionError: pass
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)

    print(f"[B-5] Escribiendo Parquet particionado por anio_evento en {BRONZE_PATH}")
    df.to_parquet(
        BRONZE_PATH,
        engine="pyarrow",
        partition_cols=["anio_evento"],
        index=False,
        compression="snappy",
    )

    print(f"[OK] Bronze listo. Total: {len(df):,}")


if __name__ == "__main__":
    main()
