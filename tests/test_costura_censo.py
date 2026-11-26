"""La costura entre actos: los recibos publicados son una funcion del censo anclado.

`receipts/censo.json` no se escribe a mano: sale de `adaptar` + `a_documento`
sobre el censo del productor. Ese producto se puede rehacer sin red y sin el
binario, porque el censo fuente viaja como fixture con su digest anclado; si el
adapter o la fuente cambian y los recibos no, esta costura cae.
"""
import hashlib
import json

from conftest import RAIZ
from conservation_ledger.adaptadores import adaptar
from conservation_ledger.esquema import a_documento

# blob 47c6bc46dc2b085b6fde363ae4991b63481a5eb3 de fiber-ast-lint @ ebb5d3a (v0.4.5)
FUENTE = RAIZ / "tests" / "fixtures" / "fuente" / "fiber-censo-0.4.5.json"
SHA256_FUENTE = "50efa55118414433b20f66b8ec8c816ccafaf316905df82893b25d67e23b3f7e"
RECIBOS = RAIZ / "receipts" / "censo.json"


def _fuente() -> dict:
    return json.loads(FUENTE.read_text(encoding="utf-8"))


def _derivar(doc: dict) -> list[dict]:
    return [a_documento(r) for r in adaptar("censo", doc)]


def test_la_fuente_anclada_es_el_blob_que_dice_ser():
    real = hashlib.sha256(FUENTE.read_bytes()).hexdigest()
    assert real == SHA256_FUENTE, f"la fuente mide {real}"


def test_los_recibos_publicados_son_la_derivacion_de_la_fuente():
    publicados = json.loads(RECIBOS.read_text(encoding="utf-8"))
    assert _derivar(_fuente()) == publicados


def test_una_fila_que_cambia_en_la_fuente_mueve_el_recibo():
    """El test de arriba pasaria con una fuente copiada del recibo; este no."""
    doc = _fuente()
    fila = next(f for f in doc["rows"] if f["stores"] == 0)
    fila["rc"] = 0
    fila["reconciles"] = True
    assert _derivar(doc) != json.loads(RECIBOS.read_text(encoding="utf-8"))
