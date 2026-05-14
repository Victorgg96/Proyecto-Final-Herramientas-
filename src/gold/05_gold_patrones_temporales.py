"""Gold 2: Patrones temporales - hora x dia_semana x mes x estacion."""
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import SILVER_PATH, GOLD_PATH


def main():
    df = pd.read_parquet(SILVER_PATH, engine="pyarrow")
    g = (df.groupby(["hora_del_dia", "dia_semana", "mes", "estacion"], as_index=False, dropna=False, observed=True)
           .agg(
               total_sismos=("magnitud", "size"),
               magnitud_promedio=("magnitud", "mean"),
               magnitud_maxima=("magnitud", "max"),
           ))

    out = GOLD_PATH / "gold_patrones_temporales"
    out.mkdir(parents=True, exist_ok=True)
    try: (out / "data.parquet").unlink(missing_ok=True)
    except PermissionError: pass
    g.to_parquet(out / "data.parquet", index=False, compression="snappy")
    print(f"[OK] gold_patrones_temporales  filas={len(g):,}")


if __name__ == "__main__":
    main()
