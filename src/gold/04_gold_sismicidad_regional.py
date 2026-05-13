"""Gold 1: Sismicidad regional - estado x anio."""
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import SILVER_PATH, GOLD_PATH


def main():
    df = pd.read_parquet(SILVER_PATH, engine="pyarrow")
    df["anio"] = df["anio"].astype("int32")
    g = (df.groupby(["estado", "region_sismica", "zona_geografica", "anio"], as_index=False, observed=True)
           .agg(
               total_sismos=("magnitud", "size"),
               magnitud_promedio=("magnitud", "mean"),
               magnitud_maxima=("magnitud", "max"),
               profundidad_promedio=("profundidad_km", "mean"),
               sismos_mag5_plus=("magnitud", lambda s: (s >= 5.0).sum()),
               sismos_mag7_plus=("magnitud", lambda s: (s >= 7.0).sum()),
           )
           .sort_values("total_sismos", ascending=False))

    out = GOLD_PATH / "gold_sismicidad_regional"
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    g.to_parquet(out / "data.parquet", index=False, compression="snappy")
    print(f"[OK] gold_sismicidad_regional  filas={len(g):,}")


if __name__ == "__main__":
    main()
