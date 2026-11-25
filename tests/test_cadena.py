"""Composition: the seam belongs to neither receipt, so only a chain can judge it."""
from __future__ import annotations

import pytest

from conservation_ledger.cadena import CIEGO, ROTO, SELLADO, cadena
from conservation_ledger.esquema import desde_documento
from conservation_ledger.verificador import CONSERVADO, COLISION, RUPTURA, VACIO, verificar

A = "a" * 64
B = "b" * 64
C = "c" * 64


def _acta(area: str, dominio: int, imagen: int, *, proy: int = 0, repe: int = 0,
          entrada: str | None = None, artefacto: str | None = None,
          digest_artefacto: str | None = None, unidad: str = "filas"):
    doc: dict[str, object] = {
        "schema": "conservation/1",
        "area": area,
        "instrumento": "ingest-conservation-guard",
        "dominio": dominio,
        "unidad": unidad,
        "cubetas": {"imagen": imagen, "colisiones_por_proyeccion": proy,
                    "colisiones_por_repetido": repe, "rechazos": 0, "sin_clave": 0},
    }
    digests = {k: v for k, v in (("entrada", entrada), ("artefacto", digest_artefacto)) if v}
    if digests:
        doc["digests"] = digests
    if artefacto:
        doc["artefacto"] = artefacto
    return desde_documento(doc)


def _dos_eslabones(segundo_entrada: str | None = B, primer_artefacto: str | None = B):
    primero = _acta("acta:entrada.csv", 6, 3, proy=2, repe=1,
                    entrada=A, artefacto="paso1.csv", digest_artefacto=primer_artefacto)
    segundo = _acta("acta:paso1.csv", 3, 3, entrada=segundo_entrada)
    return primero, segundo


def test_dos_actos_sellados_componen_en_una_sola_ecuacion():
    comp = cadena(list(_dos_eslabones()))
    assert [c.estado for c in comp.costuras] == [SELLADO]
    assert comp.ecuacion() == "6 = 3 + 3"
    assert comp.residuo == 0
    assert comp.telescopia
    assert comp.conserva is False, "el primer eslabon declaro una colision: no se lava"
    assert comp.rc == COLISION


def test_el_conteo_es_ciego_a_la_identidad():
    """Mismas filas, otros bytes: un contador dice conservado, la costura no."""
    primero, segundo = _dos_eslabones(segundo_entrada=C)
    assert verificar(primero).rc == COLISION
    assert verificar(segundo).rc == CONSERVADO, "por separado, los dos pasan"
    comp = cadena([primero, segundo])
    assert comp.costuras[0].estado == ROTO
    assert comp.costuras[0].filas_declaradas == comp.costuras[0].filas_recibidas == 3
    assert comp.rc == RUPTURA
    assert any("no es el que el acto anterior escribio" in m for m in comp.motivos)


def test_sin_digest_de_artefacto_la_costura_no_se_mide():
    """Un acto que digiere un mapa no deja nada que el siguiente pueda citar."""
    limpio = _acta("acta:entrada.csv", 3, 3, entrada=A, artefacto="paso1.csv")
    segundo = _acta("acta:paso1.csv", 3, 3, entrada=B)
    comp = cadena([limpio, segundo])
    assert comp.costuras[0].estado == CIEGO
    assert comp.rc == VACIO, "no medido no es cero"
    assert any("no digiere su artefacto" in m for m in comp.motivos)


def test_unidades_distintas_no_componen():
    primero, _ = _dos_eslabones()
    otro = _acta("fiber:x", 12, 12, unidad="almacenes")
    comp = cadena([primero, otro])
    assert comp.rc == VACIO
    assert comp.costuras == ()
    assert any("unidades distintas" in m for m in comp.motivos)


def test_el_telescopio_cuenta_el_residuo_por_dos_rutas():
    """d(1) = img(n) + sum(restos) sale igual que la suma de los residuos."""
    primero = _acta("acta:entrada.csv", 6, 3, proy=2, entrada=A,
                    artefacto="p.csv", digest_artefacto=B)
    segundo = _acta("acta:p.csv", 3, 2, entrada=B)
    comp = cadena([primero, segundo])
    assert comp.residuo == 2, "1 que pierde el enlace 1 + 1 que pierde el enlace 2"
    assert comp.residuo_de_los_enlaces == 2
    assert comp.telescopia
    assert comp.ecuacion() == "6 = 2 + 2"
    assert comp.rc == RUPTURA


def test_una_cadena_de_un_solo_acto_es_un_error_de_uso():
    with pytest.raises(ValueError, match="al menos dos actos"):
        cadena([_acta("acta:x.csv", 1, 1)])
