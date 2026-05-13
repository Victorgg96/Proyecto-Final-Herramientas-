"""B-1, B-2: Copia el CSV original a data/raw y registra hashes."""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import CSV_FUENTE, RAW_CSV, BRONZE_META


def hash_archivo(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not CSV_FUENTE.exists():
        raise FileNotFoundError(f"No se encontro CSV en {CSV_FUENTE}")

    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    BRONZE_META.parent.mkdir(parents=True, exist_ok=True)

    print(f"[B-1] Copiando CSV desde {CSV_FUENTE}")
    shutil.copy2(CSV_FUENTE, RAW_CSV)

    print("[B-2] Calculando hashes...")
    md5 = hash_archivo(RAW_CSV, "md5")
    sha256 = hash_archivo(RAW_CSV, "sha256")

    with open(RAW_CSV, "r", encoding="latin1") as f:
        total_lineas = sum(1 for _ in f)

    meta = {
        "archivo": RAW_CSV.name,
        "ruta": str(RAW_CSV),
        "tamano_bytes": RAW_CSV.stat().st_size,
        "hash_md5": md5,
        "hash_sha256": sha256,
        "fecha_ingesta": datetime.now().isoformat(),
        "total_lineas_archivo": total_lineas,
        "lineas_header_omitidas": 4,
        "registros_esperados": total_lineas - 5,
        "fuente": "Servicio Sismologico Nacional - UNAM",
        "doi": "10.21766/SSNMX/EC/MX",
    }
    with open(BRONZE_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[OK] Metadata escrita en {BRONZE_META}")
    print(f"     MD5:    {md5}")
    print(f"     SHA256: {sha256}")
    print(f"     Registros esperados: {meta['registros_esperados']:,}")


if __name__ == "__main__":
    main()
