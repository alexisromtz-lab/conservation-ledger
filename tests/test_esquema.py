import pytest

from conservation_ledger.esquema import (
    ESQUEMA, Recibo, ReciboInvalido, a_documento, desde_documento,
)


def doc(**cambios):
    base = {"schema": ESQUEMA, "area": "a", "instrumento": "i", "dominio": 3,
            "cubetas": {"x": 3}}
    base.update(cambios)
    return base


def test_un_recibo_toma_su_dominio_y_sus_cubetas():
    r = desde_documento(doc())
    assert (r.dominio, r.cubetas, r.area) == (3, {"x": 3}, "a")


def test_un_conteo_negativo_no_puede_existir():
    with pytest.raises(ReciboInvalido, match="negativo"):
        desde_documento(doc(cubetas={"x": -1}))


def test_un_booleano_no_es_un_entero():
    with pytest.raises(ReciboInvalido, match="entero"):
        desde_documento(doc(dominio=True))


def test_un_digest_que_no_mide_64_hex_no_es_un_digest():
    with pytest.raises(ReciboInvalido, match="sha256"):
        desde_documento(doc(digests={"entrada": "abc"}))


def test_un_esquema_ajeno_no_se_lee_como_si_fuera_este():
    with pytest.raises(ReciboInvalido, match="schema"):
        desde_documento(doc(schema="conservation/0"))


def test_sin_cubetas_se_lee_igual_y_el_verificador_decide():
    r = desde_documento({k: v for k, v in doc().items() if k != "cubetas"})
    assert r.cubetas == {}


def test_la_ida_y_vuelta_conserva_lo_declarado():
    r = Recibo(area="a", instrumento="i", version="1", dominio=5,
               cubetas={"b": 5}, digest_entrada="0" * 64,
               declarado_conserva=True, declarado_rc=1)
    vuelta = desde_documento(a_documento(r))
    assert vuelta == r
