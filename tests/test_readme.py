"""No published figure ages in silence.

The table in README.md is recomputed from ``receipts/`` on every run; if a
receipt changes and the README does not, this test fails.
"""
import re

from conftest import RAIZ, veredictos
from conservation_ledger.panel import tabla_md

INICIO = "<!-- ledger-table:begin -->"
FIN = "<!-- ledger-table:end -->"


def _bloque_publicado() -> str:
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    match = re.search(re.escape(INICIO) + r"\n(.*?)\n" + re.escape(FIN), texto, re.S)
    assert match, "README.md no tiene el bloque ledger-table"
    return match.group(1)


def test_la_tabla_del_readme_es_la_que_sale_de_los_recibos():
    assert _bloque_publicado() == tabla_md(veredictos())


def test_el_readme_no_publica_areas_que_ya_no_existen():
    publicadas = set(re.findall(r"^\| `([^`]+)`", _bloque_publicado(), re.M))
    assert publicadas == {v.area for v in veredictos()}
