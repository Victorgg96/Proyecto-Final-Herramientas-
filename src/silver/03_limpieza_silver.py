"""S-1 a S-8: Limpieza, validacion y enriquecimiento de Silver con pandas."""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    BRONZE_PATH, SILVER_PATH, SILVER_REJECTED,
    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, PROF_MIN, PROF_MAX,
    CLASIFICACION_MAGNITUD,
)
from src.utils.regex_estados import extraer_estado, region_de, zona_de


def clasificar_mag(mag):
    if pd.isna(mag):
        return "Sin magnitud"
    for lo, hi, nombre, _ in CLASIFICACION_MAGNITUD:
        if lo <= mag < hi:
            return nombre
    return "Sin magnitud"


def estacion_de(mes):
    if pd.isna(mes):
        return "Desconocida"
    mes = int(mes)
    if mes in (3, 4, 5): return "Primavera"
    if mes in (6, 7, 8): return "Verano"
    if mes in (9, 10, 11): return "Otono"
    return "Invierno"


def main():
    print(f"[Silver] Leyendo Bronze desde {BRONZE_PATH}")
    df = pd.read_parquet(BRONZE_PATH, engine="pyarrow")
    df = df.drop(columns=[c for c in ["ingesta_ts", "capa"] if c in df.columns])
    print(f"[Silver] Registros Bronze: {len(df):,}")

    # S-2: Cast de tipos
    df["fecha_local"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["hora_local"] = df["Hora"]
    df["fecha_utc"] = pd.to_datetime(df["Fecha_UTC"], errors="coerce")
    df["hora_utc"] = df["Hora_UTC"]
    df["magnitud"] = pd.to_numeric(df["Magnitud"], errors="coerce")
    df["latitud"] = pd.to_numeric(df["Latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
    df["profundidad_km"] = pd.to_numeric(df["Profundidad"], errors="coerce")
    df["referencia"] = df["Referencia_de_localizacion"]
    df["estatus"] = df["Estatus"]

    # S-3: Flag magnitud (no imputamos)
    df["magnitud_disponible"] = df["magnitud"].notna()

    # S-4: Filtro geografico MX
    cond_geo = (
        df["latitud"].between(LAT_MIN, LAT_MAX) &
        df["longitud"].between(LON_MIN, LON_MAX) &
        df["profundidad_km"].between(PROF_MIN, PROF_MAX)
    )
    rechazados = df.loc[~cond_geo].copy()
    if len(rechazados) > 0:
        print(f"[Silver] Registros fuera de rango: {len(rechazados):,}")
        SILVER_REJECTED.parent.mkdir(parents=True, exist_ok=True)
        rechazados[["Fecha", "Hora", "latitud", "longitud", "profundidad_km", "referencia"]].to_parquet(
            SILVER_REJECTED, index=False, compression="snappy"
        )
    df = df.loc[cond_geo].copy()

    # S-5: Extraccion de estado, region, zona
    df["estado"] = df["referencia"].apply(extraer_estado)
    df["region_sismica"] = df["estado"].apply(region_de)
    df["zona_geografica"] = df["estado"].apply(zona_de)

    # S-6: Deduplicacion
    antes = len(df)
    df = df.drop_duplicates(subset=["fecha_local", "hora_local", "latitud", "longitud"])
    print(f"[Silver] Duplicados eliminados: {antes - len(df):,}")

    # S-7: Clasificacion de magnitud
    df["clasificacion_magnitud"] = df["magnitud"].apply(clasificar_mag)

    # S-8: Columnas temporales derivadas
    df["anio"] = df["fecha_local"].dt.year.astype("Int64")
    df["mes"] = df["fecha_local"].dt.month.astype("Int64")
    df["dia"] = df["fecha_local"].dt.day.astype("Int64")
    df["dia_semana"] = df["fecha_local"].dt.day_name()
    df["decada"] = (df["anio"] // 10 * 10).astype("Int64")
    df["estacion"] = df["mes"].apply(estacion_de)

    hora_ts = pd.to_datetime(df["hora_local"], format="%H:%M:%S", errors="coerce")
    df["hora_del_dia"] = hora_ts.dt.hour.astype("Int64")

    cols = [
        "fecha_local", "hora_local", "fecha_utc", "hora_utc",
        "magnitud", "magnitud_disponible", "clasificacion_magnitud",
        "latitud", "longitud", "profundidad_km",
        "referencia", "estado", "region_sismica", "zona_geografica",
        "estatus", "anio", "mes", "dia", "hora_del_dia", "dia_semana", "estacion", "decada",
    ]
    df = df[cols]
    df = df.dropna(subset=["anio"])
    # Cast a int normal (no Int64 nullable) para evitar problemas al re-leer Parquet particionado
    for c in ["anio", "mes", "dia", "hora_del_dia", "decada"]:
        df[c] = df[c].fillna(-1).astype("int32")

    print(f"[Silver] Total final: {len(df):,}  |  Con magnitud: {df['magnitud_disponible'].sum():,}")
    print(f"[Silver] Cobertura estado: {(df['estado']!='DESCONOCIDO').mean()*100:.1f}%")

    if SILVER_PATH.exists():
        for f in SILVER_PATH.rglob("*.parquet"):
            try: f.unlink()
            except PermissionError: pass
    SILVER_PATH.mkdir(parents=True, exist_ok=True)

    print(f"[S-8] Escribiendo Parquet+Snappy particionado por anio")
    df.to_parquet(
        SILVER_PATH,
        engine="pyarrow",
        partition_cols=["anio"],
        index=False,
        compression="snappy",
    )
    print("[OK] Silver listo.")


if __name__ == "__main__":
    main()
