"""El conjunto tambien es un objeto: tres medidas, ninguna del orden.

`verify` juzga un area; aqui se juzga la poblacion de areas. Lo que se mide es
que el agregado publicado sea una funcion de los recibos, que sus dos digests se
rehagan sin nuestro codigo, que las tres manipulaciones obvias -- quitar un
area, reordenarlas, romper una -- muevan las medidas que dicen mover, y que la
procedencia no se pueda quitar, ni inventar, ni sobrevivir a un documento de
origen ausente o alterado.

Los dos niveles se prueban por separado a proposito: un cliente que recibio el
JSON y nada mas no puede ver una falsificacion autoconsistente, y el test lo
declara en vez de disimularlo.
"""
import dataclasses
import hashlib
import json
import shutil
import subprocess
import sys

import pytest

from conftest import RAIZ

from conservation_ledger.agregado import (
    CAMPOS,
    CAMPOS_FUENTE,
    agregar,
    comprobar,
    digest,
    leer_fuentes,
    proyeccion,
)
from conservation_ledger.verificador import verificar

CENSO = RAIZ / "receipts" / "censo.json"
AGREGADO = RAIZ / "aggregates" / "censo.json"


def _leer() -> tuple[list[tuple], list[dict]]:
    recibos, fuentes = leer_fuentes([CENSO])
    return [(r, verificar(r)) for r in recibos], fuentes


def _publicado() -> dict:
    return json.loads(AGREGADO.read_text(encoding="utf-8"))


def test_el_agregado_publicado_es_la_funcion_de_los_recibos():
    pares, fuentes = _leer()
    assert agregar(pares, fuentes) == _publicado()


def test_el_conjunto_cuadra_consigo_mismo():
    assert comprobar(_publicado()) == (0, ())


def test_el_conjunto_cuadra_contra_sus_fuentes():
    assert comprobar(_publicado(), base=CENSO.parent) == (0, ())


def test_la_procedencia_nombra_los_bytes_de_la_fuente():
    prov = _publicado()["procedencia"]
    assert [f["documento"] for f in prov] == ["censo.json"]
    assert prov[0]["sha256"] == hashlib.sha256(CENSO.read_bytes()).hexdigest()
    assert prov[0]["n_recibos"] == len(_leer()[0])


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


def test_el_digest_de_procedencia_se_rehace_sin_nuestro_codigo():
    jq = shutil.which("jq")
    if jq is None:
        pytest.skip("jq no esta instalado")
    campos = ",".join(f"(.{c} // \"\")" for c in CAMPOS_FUENTE)
    expr = f".procedencia[] | [{campos}] | @tsv"
    salida = subprocess.run(
        f"{jq} -r '{expr}' {AGREGADO} | LC_ALL=C sort | shasum -a 256",
        shell=True, capture_output=True, text=True, check=True,
    ).stdout.split()[0]
    assert salida == _publicado()["digest_procedencia"]


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
    pares, fuentes = _leer()
    (r0, v0) = pares[0]
    roto = dataclasses.replace(v0, clase="DISCREPANCIA", rc=4, motivos=("mutante",))
    doc = agregar([(r0, roto)] + pares[1:], fuentes)
    assert doc["cuenta"]["DISCREPANCIA"] == 1
    assert doc["defectuosos"] == 1
    assert doc["rc"] == 4, "un defecto no se diluye en once areas sanas"


def test_un_conjunto_sin_fuentes_no_se_construye():
    """La firma lo impide: el olvido es un error, no un campo vacio."""
    pares, fuentes = _leer()
    mentira = [dict(fuentes[0], n_recibos=len(pares) - 1)]
    with pytest.raises(ValueError, match="no cierra"):
        agregar(pares, mentira)


def test_quitar_la_procedencia_deja_el_certificado_sin_sujeto():
    doc = _publicado()
    del doc["procedencia"]
    del doc["digest_procedencia"]
    rc, motivos = comprobar(doc)
    assert rc == 1
    assert any("no declara procedencia" in m for m in motivos)


def test_inventar_un_sha_en_la_procedencia_rompe_su_digest():
    doc = _publicado()
    doc["procedencia"][0]["sha256"] = "0" * 64
    rc, motivos = comprobar(doc)
    assert rc == 1
    assert any("digest de procedencia" in m for m in motivos)


def test_una_fuente_ausente_no_se_puede_verificar(tmp_path):
    rc, motivos = comprobar(_publicado(), base=tmp_path)
    assert rc == 1
    assert any("falta la fuente" in m for m in motivos)


def test_un_documento_de_origen_alterado_rompe_los_bytes(tmp_path):
    copia = tmp_path / "censo.json"
    copia.write_bytes(CENSO.read_bytes() + b"\n")
    rc, motivos = comprobar(_publicado(), base=tmp_path)
    assert rc == 1
    assert any("los bytes no son los declarados" in m for m in motivos)


def test_una_falsificacion_autoconsistente_pasa_el_nivel_1_y_muere_en_el_2(tmp_path):
    """El defecto que este candado existe para cerrar.

    Un certificado construido con nuestro propio constructor, declarando una
    fuente a la que le falta un recibo, cuadra consigo mismo: conteo, digest,
    vector de clases y la identidad ``n_areas == suma de aportes``. Solo releyendo
    la fuente se ve que el conjunto declara doce areas y el documento tiene trece.
    """
    pares, fuentes = _leer()
    forjado = agregar(pares[:-1], [dict(fuentes[0], n_recibos=len(pares) - 1)])
    assert forjado["n_areas"] == 12
    assert comprobar(forjado) == (0, ()), "el nivel 1 no puede verlo: solo tiene el JSON"

    shutil.copyfile(CENSO, tmp_path / "censo.json")
    rc, motivos = comprobar(forjado, base=tmp_path)
    assert rc == 1
    assert any("no son la funcion de sus fuentes" in m for m in motivos)


def test_la_cli_propaga_el_rc_de_procedencia(tmp_path):
    """El cableado de --base tambien se mide: un argumento sin lector es prosa."""
    entorno = {"PYTHONPATH": str(RAIZ / "src"), "PATH": "/usr/bin:/bin"}
    ok = subprocess.run(
        [sys.executable, "-m", "conservation_ledger", "aggregate",
         "--check", str(AGREGADO), "--base", str(CENSO.parent)],
        capture_output=True, text=True, env=entorno, check=False,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "fuentes 1" in ok.stdout

    roto = subprocess.run(
        [sys.executable, "-m", "conservation_ledger", "aggregate",
         "--check", str(AGREGADO), "--base", str(tmp_path)],
        capture_output=True, text=True, env=entorno, check=False,
    )
    assert roto.returncode == 1, roto.stdout + roto.stderr
    assert "falta la fuente" in roto.stdout
