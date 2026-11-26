"""El conjunto como un recibo: la auditoria entera, citable.

``verify`` juzga un area y ``chain`` juzga una costura entre dos; hasta aqui el
conjunto solo existia como la ultima linea de una terminal. Ese veredicto no
tenia documento, asi que no se podia entregar, ni anclar, ni volver a leer.

Dos medidas independientes lo cierran, y son las mismas dos de siempre: el
**recuento** de areas y el **digest** de una proyeccion canonica de cada una. Ni
la una ni la otra dependen del orden en que llegaron los recibos -- el conjunto
es un conjunto -- pero las dos se mueven si un area desaparece, si se cuela una
que no estaba o si cambia de clase. Un agregado que solo contara areas se
padearia con un area repetida; uno que solo guardara el digest no diria cuantas
son.
"""
from __future__ import annotations

import hashlib
import json
from typing import Iterable, Sequence

from .esquema import Recibo
from .verificador import Veredicto, rc_del_acto

ESQUEMA = "conservation/agregado/1"

#: Campos de una fila del conjunto, en el orden en que se proyectan.
CAMPOS = ("area", "instrumento", "version", "clase", "rc", "dominio", "residuo",
          "digest_entrada")


def _fila(r: Recibo, v: Veredicto) -> dict:
    return {
        "area": v.area,
        "instrumento": v.instrumento,
        "version": v.version,
        "clase": v.clase,
        "rc": v.rc,
        "dominio": v.dominio,
        "residuo": v.residuo,
        "digest_entrada": r.digest_entrada,
    }


def _clave(fila: dict) -> list[str]:
    return [str(fila.get(c) or "") for c in CAMPOS]


def proyeccion(filas: Sequence[dict]) -> str:
    """Una linea por area, tabulada y ordenada: lo que un tercero puede rehacer.

    ``@tsv`` de jq y ``sort`` con ``LC_ALL=C`` producen exactamente estas lineas,
    asi que el digest se comprueba sin instalar este paquete.
    """
    lineas = []
    for fila in sorted(filas, key=_clave):
        lineas.append("\t".join(
            "" if fila.get(c) is None else str(fila.get(c)) for c in CAMPOS))
    return "\n".join(lineas) + "\n" if lineas else ""


def digest(filas: Sequence[dict]) -> str:
    return hashlib.sha256(proyeccion(filas).encode("utf-8")).hexdigest()


def _cuenta(veredictos: Iterable[Veredicto]) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for v in veredictos:
        cuenta[v.clase] = cuenta.get(v.clase, 0) + 1
    return dict(sorted(cuenta.items()))


def agregar(pares: Iterable[tuple[Recibo, Veredicto]]) -> dict:
    lista = list(pares)
    filas = sorted((_fila(r, v) for r, v in lista), key=_clave)
    veredictos = [v for _, v in lista]
    return {
        "schema": ESQUEMA,
        "n_areas": len(filas),
        # Un solo booleano colapsaria "no habia nada que medir" con "se rompio",
        # que es justo la distincion que el contrato existe para hacer. El
        # conjunto publica el vector de clases; el veredicto se lee de ahi.
        "cuenta": _cuenta(veredictos),
        "defectuosos": sum(1 for v in veredictos if v.defectuoso),
        "rc": rc_del_acto(veredictos),
        # Suma de poblaciones distintas: es un digito de control del conjunto,
        # no una medida de codigo. Se publica con su nombre para que nadie la
        # lea como "tantos almacenes en el universo".
        "dominio_declarado_suma": sum(v.dominio for v in veredictos),
        "residuo_total": sum(v.residuo for v in veredictos),
        "instrumentos": sorted({f"{v.instrumento} {v.version}" for v in veredictos}),
        "areas": filas,
        "digest_conjunto": digest(filas),
    }


def comprobar(doc: dict) -> tuple[int, tuple[str, ...]]:
    """Re-deriva el conjunto desde sus propias filas. RC 0 = cuadra."""
    if doc.get("schema") != ESQUEMA:
        return 1, (f"schema {doc.get('schema')!r} no es {ESQUEMA}",)
    filas = doc.get("areas") or []
    if not isinstance(filas, list):
        return 1, ("'areas' debe ser una lista",)
    motivos: list[str] = []
    if len(filas) != doc.get("n_areas"):
        motivos.append(f"declara {doc.get('n_areas')} areas, lleva {len(filas)}")
    if digest(filas) != doc.get("digest_conjunto"):
        motivos.append(f"el digest declarado no es el de sus filas "
                       f"({doc.get('digest_conjunto')})")
    cuenta: dict[str, int] = {}
    for fila in filas:
        clase = str(fila.get("clase") or "")
        cuenta[clase] = cuenta.get(clase, 0) + 1
    if dict(sorted(cuenta.items())) != doc.get("cuenta"):
        motivos.append(f"el vector de clases declarado no es {dict(sorted(cuenta.items()))}")
    suma = sum(int(f.get("dominio") or 0) for f in filas)
    if suma != doc.get("dominio_declarado_suma"):
        motivos.append(f"la suma declarada no es {suma}")
    if sum(int(f.get("residuo") or 0) for f in filas) != doc.get("residuo_total"):
        motivos.append("el residuo declarado no es la suma de los residuos")
    return (0 if not motivos else 1), tuple(motivos)


def leer(ruta) -> dict:
    from pathlib import Path

    return json.loads(Path(ruta).read_text(encoding="utf-8"))
