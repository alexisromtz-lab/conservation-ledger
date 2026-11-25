import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

RECIBOS = RAIZ / "receipts"


def veredictos():
    """Every committed receipt, read exactly as the CLI would read it."""
    import json

    from conservation_ledger.adaptadores import adaptar
    from conservation_ledger.verificador import verificar

    salida = []
    for ruta in sorted(RECIBOS.glob("*.json")):
        doc = json.loads(ruta.read_text(encoding="utf-8"))
        salida.extend(verificar(r) for r in adaptar("raw", doc))
    return salida
