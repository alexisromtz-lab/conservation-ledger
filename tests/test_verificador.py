import pytest

from conservation_ledger.esquema import Recibo
from conservation_ledger.verificador import (
    COLISION, CONSERVADO, RUPTURA, VACIO, combinar, fusiones, normalizar,
    rc_del_acto, verificar,
)


def recibo(dominio=10, cubetas=None, **kw):
    return Recibo(area="a", instrumento="i", version=None, dominio=dominio,
                  cubetas={"uno": 7, "dos": 3} if cubetas is None else cubetas, **kw)


def test_una_ecuacion_cerrada_conserva():
    v = verificar(recibo())
    assert (v.clase, v.rc, v.residuo, v.conserva) == ("CONSERVADO", 0, 0, True)


def test_un_residuo_distinto_de_cero_es_ruptura():
    v = verificar(recibo(cubetas={"uno": 7, "dos": 2}))
    assert (v.clase, v.rc, v.residuo) == ("RUPTURA", RUPTURA, 1)


def test_un_recibo_mentiroso_no_puede_salir_limpio():
    """H_ledger: cubetas que suman dominio-1 y declarado conserva=True -> nunca 0."""
    v = verificar(recibo(dominio=6, cubetas={"imagen": 5},
                         declarado_conserva=True, declarado_rc=0))
    assert (v.rc, v.clase) == (RUPTURA, "RUPTURA")
    assert any("conserva=true" in m for m in v.motivos)


def test_sin_terminos_no_es_un_cero_sino_lo_que_no_se_pudo_medir():
    v = verificar(recibo(dominio=40, cubetas={}))
    assert (v.clase, v.rc, v.conserva) == ("NO_VERIFICABLE", VACIO, False)


def test_un_dominio_vacio_no_se_lee_como_conservado():
    assert verificar(recibo(dominio=0, cubetas={})).clase == "NO_VERIFICABLE"
    v = verificar(recibo(dominio=0, cubetas={"uno": 0}))
    assert (v.rc, v.clase, v.conserva) == (VACIO, "VACIO", False)


def test_declarar_ruptura_sobre_una_ecuacion_cerrada_es_discrepancia():
    v = verificar(recibo(declarado_conserva=False))
    assert (v.clase, v.rc) == ("DISCREPANCIA", RUPTURA)


def test_declarar_no_medido_sobre_algo_medido_es_discrepancia():
    v = verificar(recibo(declarado_rc=VACIO))
    assert (v.clase, v.rc) == ("DISCREPANCIA", RUPTURA)


def test_una_colision_se_deriva_de_los_terminos_no_del_veredicto():
    """Severidad desde el dato publicado: cubeta ``colisiones_*`` con valor."""
    v = verificar(recibo(dominio=10, cubetas={"imagen": 8, "colisiones_por_x": 2},
                         declarado_rc=0))
    assert (v.clase, v.rc, v.conserva) == ("COLISION", COLISION, True)
    assert fusiones({"colisiones_por_x": 2, "otra": 1}) == 2


def test_declarar_colision_sin_terminos_que_la_muestren_no_es_un_defecto():
    v = verificar(recibo(declarado_rc=COLISION))
    assert (v.clase, v.rc) == ("CONSERVADO", 0)
    assert any("declaraba una colision" in m for m in v.motivos)


def test_declarar_limpio_sobre_algo_que_no_cierra_es_ruptura():
    v = verificar(recibo(cubetas={"uno": 9}, declarado_rc=0, declarado_conserva=True))
    assert v.rc == RUPTURA


@pytest.mark.parametrize("rcs,esperado", [
    ((), 0), ((0,), 0), ((1,), 1), ((2,), 2), ((4,), 4),
    ((1, 2), 1),   # max() daria 2 y dejaria que la ceguera tape la colision
    ((0, 2), 2), ((1, 4), 4), ((9,), 4),
])
def test_el_supremo_no_es_el_maximo(rcs, esperado):
    assert combinar(*rcs) == esperado


def test_un_codigo_desconocido_no_es_limpio():
    assert normalizar(7) == RUPTURA


def test_el_acto_solo_suma_codigos_recomputados():
    veredictos = [verificar(recibo()),
                  verificar(recibo(dominio=40, cubetas={}))]
    assert rc_del_acto(veredictos) == VACIO
    assert rc_del_acto([verificar(recibo())]) == CONSERVADO
    assert rc_del_acto([]) == CONSERVADO


def test_certificar_sobre_un_dominio_vacio_es_discrepancia():
    """0 = 0 cierra porque no habia nada que conservar: no es una firma."""
    v = verificar(recibo(dominio=0, cubetas={"uno": 0},
                         declarado_conserva=True, declarado_rc=CONSERVADO))
    assert (v.clase, v.rc, v.residuo) == ("DISCREPANCIA", RUPTURA, 0)
    sin_conserva = verificar(recibo(dominio=0, cubetas={"uno": 0}, declarado_rc=COLISION))
    assert (sin_conserva.clase, sin_conserva.rc) == ("DISCREPANCIA", RUPTURA)
    callado = verificar(recibo(dominio=0, cubetas={"uno": 0}))
    assert (callado.clase, callado.rc) == ("VACIO", VACIO)
