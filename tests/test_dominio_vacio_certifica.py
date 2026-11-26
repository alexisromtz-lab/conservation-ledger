"""Un acta sobre un dominio vacio: dos productores reales, dos veredictos.

Los recibos de ``fixtures/dominio-vacio`` los emitieron los binarios publicados,
no se escribieron a mano: ``0.4.4`` firmo ``conserva=true rc=0`` sobre un CSV con
solo cabecera y ``0.4.5`` declaro lo mismo como ``NO_MEDIDO``. El verificador no
cambio entre los dos; lo que cambia es que ahora distingue al productor que
certifica una poblacion vacia del que declara no haber medido nada. Las dos
implementaciones -- la biblioteca y ``verify.sh`` -- tienen que coincidir, porque
una ley con dos implementaciones sin comparador son dos leyes.
"""
import json
import subprocess

import pytest

from conftest import RAIZ
from conservation_ledger.adaptadores import adaptar
from conservation_ledger.verificador import RUPTURA, VACIO, verificar

FIX = RAIZ / "tests" / "fixtures" / "dominio-vacio"
V042 = FIX / "acta-0.4.4.json"
V045 = FIX / "acta-0.4.5.json"


def _veredictos(ruta):
    return [verificar(r) for r in adaptar("acta", json.loads(ruta.read_text(encoding="utf-8")))]


def test_el_productor_que_firmaba_un_dominio_vacio_es_una_discrepancia():
    (v,) = _veredictos(V042)
    assert (v.clase, v.rc) == ("DISCREPANCIA", RUPTURA)
    assert v.residuo == 0, "la ecuacion cerraba: el defecto no es aritmetico"
    texto = " · ".join(v.motivos)
    assert "conserva=true" in texto and "rc=0" in texto


def test_el_productor_que_declara_no_medido_pasa_sin_acusacion():
    (v,) = _veredictos(V045)
    assert (v.clase, v.rc) == ("VACIO", VACIO)
    assert not any("conserva" in m or "rc=" in m for m in v.motivos), v.motivos


@pytest.mark.parametrize("ruta,esperado", [(V042, 4), (V045, 2)])
def test_el_guion_del_raiz_llega_al_mismo_codigo(ruta, esperado):
    proceso = subprocess.run(["sh", str(RAIZ / "verify.sh"), str(ruta), str(ruta)],
                             capture_output=True, text=True)
    assert proceso.returncode == esperado, proceso.stdout + proceso.stderr
    contradice = "se contradice" in proceso.stdout
    assert contradice is (esperado == 4), proceso.stdout
