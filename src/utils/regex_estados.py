"""Extraccion de estado mexicano desde 'Referencia de localizacion'."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import ESTADOS_MX, REGION_SISMICA, ZONA_GEOGRAFICA

PATRON = re.compile(r",\s*([A-ZÑ]{2,4})\s*$")


def extraer_estado(referencia):
    if not isinstance(referencia, str):
        return "DESCONOCIDO"
    m = PATRON.search(referencia.strip())
    if not m:
        return "DESCONOCIDO"
    return ESTADOS_MX.get(m.group(1).upper(), "DESCONOCIDO")


def region_de(estado):
    return REGION_SISMICA.get(estado, "Desconocida")


def zona_de(estado):
    return ZONA_GEOGRAFICA.get(region_de(estado), "Desconocida")
