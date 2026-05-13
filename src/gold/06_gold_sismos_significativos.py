"""Gold 3: Catalogo enriquecido de sismos con mag >= 5.0."""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import SILVER_PATH, GOLD_PATH, CDMX_LAT, CDMX_LON


def haversine(lat, lon, lat0=CDMX_LAT, lon0=CDMX_LON):
    R = 6371.0
    lat_r = np.radians(lat); lat0_r = np.radians(lat0)
    dlat = lat_r - lat0_r
    dlon = np.radians(lon - lon0)
    a = np.sin(dlat / 2) ** 2 + np.cos(lat0_r) * np.cos(lat_r) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def main():
    df = pd.read_parquet(SILVER_PATH, engine="pyarrow")
    g = df[df["magnitud"] >= 5.0].copy()
    g["distancia_cdmx_km"] = haversine(g["latitud"].values, g["longitud"].values).round(2)
    g["tsunami_probable"] = (g["magnitud"] >= 7.0) & (g["region_sismica"].isin(["Costa", "Pacifico"]))
    g = g[[
        "fecha_local", "hora_local", "magnitud", "clasificacion_magnitud",
        "latitud", "longitud", "profundidad_km",
        "estado", "region_sismica", "zona_geografica",
        "distancia_cdmx_km", "tsunami_probable", "estatus", "anio",
    ]].sort_values("magnitud", ascending=False)

    out = GOLD_PATH / "gold_sismos_significativos"
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    g.to_parquet(out / "data.parquet", index=False, compression="snappy")
    print(f"[OK] gold_sismos_significativos  filas={len(g):,}")


if __name__ == "__main__":
    main()
