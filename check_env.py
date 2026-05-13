"""Verifica entorno antes de correr el pipeline."""
import sys
from pathlib import Path


def main():
    print("=" * 60)
    print(" Verificacion de entorno - Proyecto SSN-UNAM v2")
    print("=" * 60)
    ok = True

    py_ver = sys.version_info
    print(f"\nPython: {sys.version.split()[0]}  ({sys.executable})")
    if py_ver < (3, 9):
        print("  [FAIL] Se requiere Python 3.9+")
        ok = False
    else:
        print("  [OK]   Version Python compatible")

    print("\nDependencias:")
    for mod in ["pandas", "pyarrow", "duckdb", "streamlit", "plotly", "folium"]:
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "?")
            print(f"  [OK]   {mod} {ver}")
        except ImportError:
            print(f"  [FAIL] {mod} no instalado. Ejecuta: pip install -r requirements.txt")
            ok = False

    print("\nArchivos:")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config.settings import CSV_FUENTE
    if CSV_FUENTE.exists():
        print(f"  [OK]   CSV fuente: {CSV_FUENTE.name}")
    else:
        print(f"  [FAIL] No se encontro CSV en {CSV_FUENTE}")
        ok = False

    print("\n" + "=" * 60)
    if ok:
        print(" TODO OK -- puedes correr:  python run_all.py")
    else:
        print(" HAY ERRORES -- corrigelos antes de continuar")
    print("=" * 60)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
