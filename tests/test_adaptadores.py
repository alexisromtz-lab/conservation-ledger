import json

import pytest

from conftest import RECIBOS
from conservation_ledger.adaptadores import ADAPTADORES, adaptar
from conservation_ledger.verificador import fusiones, verificar


def test_el_acta_se_lee_con_la_ecuacion_completa():
    doc = {"acta": "migracion", "caso": "x.csv", "rc": 1, "conserva": True,
           "entrada": {"filas": 6, "sha256": "a" * 64},
           "salida": {"sha256": "b" * 64},
           "ecuacion": {"dominio": 6, "imagen": 4, "colisiones_por_proyeccion": 2,
                        "colisiones_por_repetido": 0, "rechazos": 0, "sin_clave": 0}}
    (r,) = adaptar("acta", doc)
    assert r.dominio == 6
    assert "dominio" not in r.cubetas
    v = verificar(r)
    assert (v.residuo, v.clase) == (0, "COLISION")
    assert fusiones(v.cubetas) == 2


def test_el_acta_sin_crudo_cierra_sobre_el_total():
    doc = {"acta": "migracion", "caso": "x.csv", "rc": 1, "conserva": True,
           "entrada": {"filas": 6}, "ecuacion": None,
           "cubetas": {"imagen": 4, "rechazos": 0, "sin_clave": 0, "colisiones": 2}}
    (r,) = adaptar("acta", doc)
    assert verificar(r).residuo == 0


def test_el_censo_por_fixture_conserva_y_su_etiqueta_es_el_ultimo_segmento():
    doc = json.loads((RECIBOS / "fiber-fixtures.json").read_text(encoding="utf-8"))
    (r,) = adaptar("raw", doc)
    assert r.area == "fiber:fixtures"
    assert verificar(r).residuo == 0


def test_el_censo_de_trece_filas_cierra_su_ecuacion_y_no_necesita_creerla():
    doc = json.loads((RECIBOS / "censo.json").read_text(encoding="utf-8"))
    recibos = adaptar("raw", doc)
    assert len(recibos) == 13
    assert len({r.area for r in recibos}) == 13
    assert all(verificar(r).residuo == 0 for r in recibos)
    assert {verificar(r).clase for r in recibos} == {"CONSERVADO", "VACIO"}


def test_una_fila_de_censo_sin_cubetas_sigue_siendo_no_verificable():
    """Lo escrito antes de v0.4.3 no se certifica por cortesia."""
    doc = {"rows": [{"package": "p", "version": "1", "scope": ".", "stores": 3,
                     "pierde": 1, "reconciles": True, "rc": 1}]}
    (r,) = adaptar("censo", doc)
    assert verificar(r).clase == "NO_VERIFICABLE"


def test_el_mismo_paquete_con_dos_sujetos_no_comparte_etiqueta():
    doc = {"instrument": "x", "rows": [
        {"package": "mypy", "version": "1", "scope": "mypy", "stores": 1},
        {"package": "mypy", "version": "1", "scope": ".", "stores": 2},
    ]}
    areas = [r.area for r in adaptar("censo", doc)]
    assert areas == ["censo:mypy@1", "censo:mypy@1#."]


def test_un_adaptador_inventado_es_un_error_no_un_cero():
    with pytest.raises(ValueError, match="adaptador desconocido"):
        adaptar("magia", {})
    assert set(ADAPTADORES) == {"acta", "fiber", "censo", "raw"}


def test_un_instrumento_puede_emitir_una_lista_de_casos():
    """`acta --json` sobre varios casos devuelve una lista, no un objeto."""
    doc = {"caso": "pacientes", "cubetas": {"imagen": 4, "rechazos": 2},
           "desconserva": True, "conserva": True, "rc": 1, "dominio": 6}
    dos = adaptar("acta", [doc, {**doc, "caso": "sku"}])
    assert [r.area for r in dos] == ["acta:pacientes", "acta:sku"]


def test_acta_lee_el_dominio_del_documento_crudo():
    """`acta --json` publica `dominio` en la raiz; `--receipt` lo pone en `entrada`."""
    crudo = {"caso": "pacientes", "dominio": 8,
             "cubetas": {"colisiones": 2, "imagen": 4, "rechazos": 2, "sin_clave": 0},
             "conserva": True, "rc": 1}
    r = adaptar("acta", crudo)[0]
    assert (r.dominio, sum(r.cubetas.values()), r.declarado_conserva) == (8, 8, True)
    assert verificar(r).clase == "COLISION"
