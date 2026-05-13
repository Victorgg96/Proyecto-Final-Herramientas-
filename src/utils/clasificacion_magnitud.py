"""Clasificacion de magnitud segun escala de Richter."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import CLASIFICACION_MAGNITUD


def clasificar(mag):
    if mag is None or (isinstance(mag, float) and mag != mag):  # NaN check
        return "Sin magnitud"
    for lo, hi, nombre, _ in CLASIFICACION_MAGNITUD:
        if lo <= mag < hi:
            return nombre
    return "Sin magnitud"
