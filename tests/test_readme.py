"""No published figure ages in silence.

The table in README.md is recomputed from ``receipts/`` on every run, and every
``wc -l`` figure quoted in prose is measured from the module it names; if a
receipt or a module changes and the README does not, this test fails.
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


CIFRA_EN_PROSA = re.compile(r"`([a-z_]+\.py)` \((\d+) lines\)")


def test_cada_recuento_de_lineas_citado_es_el_del_modulo():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    citados = {m.group(1): int(m.group(2)) for m in CIFRA_EN_PROSA.finditer(texto)}
    assert citados, "README.md no cita ningun recuento de lineas"
    for nombre, cifra in citados.items():
        fuente = RAIZ / "src" / "conservation_ledger" / nombre
        assert fuente.is_file(), f"README.md cita {nombre}, que no existe"
        # wc -l cuenta saltos de linea, no lineas logicas
        real = fuente.read_bytes().count(b"\n")
        assert cifra == real, f"{nombre}: README publica {cifra} lineas, mide {real}"
