"""El conjunto tambien es un objeto: dos medidas, ninguna del orden.

`verify` juzga un area; aqui se juzga la poblacion de areas. Lo que se mide es
que el agregado publicado sea una funcion de los recibos, que su digest se rehaga
sin nuestro codigo, y que las tres manipulaciones obvias -- quitar un area,
reordenarlas, romper una -- muevan las medidas que dicen mover.
"""
import dataclasses
import json
import shutil
import subprocess

import pytest

from conftest import RAIZ

from conservation_ledger.adaptadores import adaptar
from conservation_ledger.agregado import CAMPOS, agregar, comprobar, digest, proyeccion
from conservation_ledger.verificador import verificar

CENSO = RAIZ / "receipts" / "censo.json"
AGREGADO = RAIZ / "aggregates" / "censo.json"


def _pares():
    doc = json.loads(CENSO.read_text(encoding="utf-8"))
    return [(r, verificar(r)) for r in adaptar("raw", doc)]


def _publicado() -> dict:
    return json.loads(AGREGADO.read_text(encoding="utf-8"))


def test_el_agregado_publicado_es_la_funcion_de_los_recibos():
    assert agregar(_pares()) == _publicado()


def test_el_conjunto_cuadra_consigo_mismo():
    assert comprobar(_publicado()) == (0, ())


def test_el_digest_se_rehace_sin_nuestro_codigo():
    """jq + sort + shasum, que no saben nada de este contrato."""
    jq = shutil.which("jq")
    if jq is None:
        pytest.skip("jq no esta instalado")
    campos = ",".join(f"(.{c} // \"\")" for c in CAMPOS)
    expr = f".areas[] | [{campos}] | @tsv"
    salida = subprocess.run(
        f"{jq} -r '{expr}' {AGREGADO} | LC_ALL=C sort | shasum -a 256",
        shell=True, capture_output=True, text=True, check=True,
    ).stdout.split()[0]
    assert salida == _publicado()["digest_conjunto"]


def test_el_orden_de_las_filas_no_mueve_el_digest():
    doc = _publicado()
    invertidas = list(reversed(doc["areas"]))
    assert invertidas != doc["areas"], "el fixture ya venia al reves"
    assert digest(invertidas) == doc["digest_conjunto"]
    assert proyeccion(invertidas) == proyeccion(doc["areas"])


def test_quitar_un_area_mueve_conteo_y_digest():
    doc = _publicado()
    doc["areas"].pop()
    rc, motivos = comprobar(doc)
    assert rc == 1
    assert any("areas" in m for m in motivos)
    assert any("digest" in m for m in motivos)


def test_una_area_rota_no_se_promedia():
    recibos, veredictos = zip(*_pares())
    roto = dataclasses.replace(veredictos[0], clase="DISCREPANCIA", rc=4, motivos=("mutante",))
    doc = agregar(list(zip(recibos, (roto,) + veredictos[1:])))
    assert doc["cuenta"]["DISCREPANCIA"] == 1
    assert doc["defectuosos"] == 1
    assert doc["rc"] == 4, "un defecto no se diluye en once areas sanas"
