"""Configuracion global del proyecto SSN-UNAM v2 (pandas + DuckDB)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CSV_FUENTE = Path(r"C:\Users\vican\OneDrive\Escritorio\Claude Code\SSNMX_catalogo_19000101_20260407.csv")

RAW_CSV = DATA / "raw" / "SSNMX_catalogo_19000101_20260407.csv"
BRONZE_PATH = DATA / "bronze" / "sismos_raw"
BRONZE_META = DATA / "bronze" / "metadata.json"
SILVER_PATH = DATA / "silver" / "sismos_clean"
SILVER_REJECTED = DATA / "silver" / "sismos_rechazados.parquet"
GOLD_PATH = DATA / "gold"

SKIP_HEADER_LINES = 4

LAT_MIN, LAT_MAX = 14.0, 33.0
LON_MIN, LON_MAX = -119.0, -86.0
PROF_MIN, PROF_MAX = 0.0, 700.0

CDMX_LAT, CDMX_LON = 19.4326, -99.1332

ESTADOS_MX = {
    "AGS": "AGUASCALIENTES", "BC": "BAJA CALIFORNIA", "BCS": "BAJA CALIFORNIA SUR",
    "CAMP": "CAMPECHE", "CHIS": "CHIAPAS", "CHIH": "CHIHUAHUA", "COAH": "COAHUILA",
    "COL": "COLIMA", "CDMX": "CIUDAD DE MEXICO", "DF": "CIUDAD DE MEXICO",
    "DGO": "DURANGO", "GTO": "GUANAJUATO", "GRO": "GUERRERO", "HGO": "HIDALGO",
    "JAL": "JALISCO", "MEX": "ESTADO DE MEXICO", "MICH": "MICHOACAN",
    "MOR": "MORELOS", "NAY": "NAYARIT", "NL": "NUEVO LEON", "OAX": "OAXACA",
    "PUE": "PUEBLA", "QRO": "QUERETARO", "QROO": "QUINTANA ROO", "SLP": "SAN LUIS POTOSI",
    "SIN": "SINALOA", "SON": "SONORA", "TAB": "TABASCO", "TAMS": "TAMAULIPAS",
    "TLAX": "TLAXCALA", "VER": "VERACRUZ", "YUC": "YUCATAN", "ZAC": "ZACATECAS",
}

REGION_SISMICA = {
    "BAJA CALIFORNIA": "Norte", "BAJA CALIFORNIA SUR": "Norte", "SONORA": "Norte",
    "CHIHUAHUA": "Norte", "COAHUILA": "Norte", "NUEVO LEON": "Norte", "TAMAULIPAS": "Norte",
    "SINALOA": "Pacifico", "NAYARIT": "Pacifico", "JALISCO": "Pacifico",
    "COLIMA": "Pacifico", "MICHOACAN": "Pacifico",
    "GUERRERO": "Costa", "OAXACA": "Costa", "CHIAPAS": "Costa",
    "CIUDAD DE MEXICO": "Centro", "ESTADO DE MEXICO": "Centro", "MORELOS": "Centro",
    "PUEBLA": "Centro", "TLAXCALA": "Centro", "HIDALGO": "Centro",
    "QUERETARO": "Centro", "GUANAJUATO": "Centro", "AGUASCALIENTES": "Centro",
    "ZACATECAS": "Centro", "SAN LUIS POTOSI": "Centro", "DURANGO": "Centro",
    "VERACRUZ": "Golfo", "TABASCO": "Golfo", "CAMPECHE": "Sureste",
    "YUCATAN": "Sureste", "QUINTANA ROO": "Sureste",
}

ZONA_GEOGRAFICA = {
    "Norte": "Frontera Norte", "Pacifico": "Pacifico", "Costa": "Pacifico Sur",
    "Centro": "Altiplano Central", "Golfo": "Golfo de Mexico", "Sureste": "Peninsula de Yucatan",
}

CLASIFICACION_MAGNITUD = [
    (0.0, 2.0, "Micro", "Generalmente no se siente"),
    (2.0, 4.0, "Menor", "Se siente ligeramente"),
    (4.0, 5.0, "Ligero", "Sacudida notable"),
    (5.0, 6.0, "Moderado", "Puede causar danos menores"),
    (6.0, 7.0, "Fuerte", "Danos en zonas pobladas"),
    (7.0, 8.0, "Mayor", "Danos graves en areas extensas"),
    (8.0, 10.0, "Gran sismo", "Devastacion en cientos de km"),
]
