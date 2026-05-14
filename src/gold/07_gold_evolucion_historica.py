"""Gold 4: Evolucion historica anual y mensual."""
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import SILVER_PATH, GOLD_PATH


def main():
    df = pd.read_parquet(SILVER_PATH, engine="pyarrow")

    df["anio"] = df["anio"].astype("int32")
    anual = (df.groupby(["anio", "decada"], as_index=False, observed=True)
               .agg(
                   total_sismos=("magnitud", "size"),
                   magnitud_promedio=("magnitud", "mean"),
                   magnitud_maxima=("magnitud", "max"),
                   sismos_mag5_plus=("magnitud", lambda s: (s >= 5.0).sum()),
                   sismos_mag7_plus=("magnitud", lambda s: (s >= 7.0).sum()),
               ).sort_values("anio"))

    mensual = (df.groupby(["anio", "mes"], as_index=False, observed=True)
                 .agg(
                     total_sismos=("magnitud", "size"),
                     magnitud_promedio=("magnitud", "mean"),
                     magnitud_maxima=("magnitud", "max"),
                 ).sort_values(["anio", "mes"]))

    for nombre, dfx in [("gold_evolucion_historica_anual", anual),
                        ("gold_evolucion_historica_mensual", mensual)]:
        out = GOLD_PATH / nombre
        out.mkdir(parents=True, exist_ok=True)
        try: (out / "data.parquet").unlink(missing_ok=True)
        except PermissionError: pass
        dfx.to_parquet(out / "data.parquet", index=False, compression="snappy")
        print(f"[OK] {nombre}  filas={len(dfx):,}")


if __name__ == "__main__":
    main()
