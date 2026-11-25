"""A receipt is a closed accounting identity, not a report.

``conservation/1`` names only two things: how many units entered (``dominio``)
and the buckets they were split into (``cubetas``). The residual, the verdict
and the conservation flag are *derived by the reader*, never carried by the
writer.

That asymmetry is the whole point. A receipt that states its own verdict is a
receipt grading itself, and a producer that grades itself cannot be caught being
wrong -- which is the defect this package exists to find.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ESQUEMA = "conservation/1"

#: The unit a ``dominio`` is counted in. Two receipts with different units are
#: two different populations and are never added: `30 rows + 12 stores` is not
#: 42 of anything.
UNIDAD_POR_DEFECTO = "unidades"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReciboInvalido(ValueError):
    """The document cannot be read as a ``conservation/1`` receipt."""


@dataclass(frozen=True)
class Recibo:
    """The only facts the ledger trusts: the domain and its buckets."""

    area: str
    instrumento: str
    version: str | None
    dominio: int
    cubetas: dict[str, int]
    unidad: str = UNIDAD_POR_DEFECTO
    digest_entrada: str | None = None
    digest_salida: str | None = None
    #: The artifact this act wrote, and the digest of its bytes. Without the
    #: pair the act digests an abstraction and the next act cannot cite it, so
    #: the seam between two acts is NO_MEDIDO rather than sealed.
    artefacto: str | None = None
    digest_artefacto: str | None = None
    declarado_conserva: bool | None = None
    declarado_rc: int | None = None


def _entero(valor: Any, campo: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ReciboInvalido(f"{campo}: se esperaba un entero, llegó {type(valor).__name__}")
    if valor < 0:
        raise ReciboInvalido(f"{campo}: un conteo negativo ({valor}) no puede existir")
    return valor


def _digest(valor: Any, campo: str) -> str | None:
    if valor is None:
        return None
    if not isinstance(valor, str) or not _HEX64.match(valor):
        raise ReciboInvalido(f"{campo}: no es un sha256 hexadecimal de 64 caracteres")
    return valor


def desde_documento(doc: dict[str, Any]) -> Recibo:
    """Read a ``conservation/1`` document into a :class:`Recibo`.

    Missing buckets are not an error at this layer: a receipt without terms is a
    real state, and the verifier must be able to say ``NO_VERIFICABLE`` about it
    instead of refusing to look.
    """
    if not isinstance(doc, dict):
        raise ReciboInvalido("el recibo debe ser un objeto JSON")

    esquema = doc.get("schema", ESQUEMA)
    if esquema != ESQUEMA:
        raise ReciboInvalido(f"schema {esquema!r} no es {ESQUEMA!r}")

    crudo = doc.get("cubetas")
    if crudo is None:
        cubetas: dict[str, int] = {}
    elif isinstance(crudo, dict):
        cubetas = {str(k): _entero(v, f"cubetas.{k}") for k, v in crudo.items()}
    else:
        raise ReciboInvalido("cubetas debe ser un objeto")

    digests = doc.get("digests") or {}
    if not isinstance(digests, dict):
        raise ReciboInvalido("digests debe ser un objeto")

    declarado = doc.get("declarado") or {}
    if not isinstance(declarado, dict):
        raise ReciboInvalido("declarado debe ser un objeto")

    rc = declarado.get("rc")
    if rc is not None:
        rc = _entero(rc, "declarado.rc")
    conserva = declarado.get("conserva")
    if conserva is not None and not isinstance(conserva, bool):
        raise ReciboInvalido("declarado.conserva debe ser booleano")

    unidad = doc.get("unidad", UNIDAD_POR_DEFECTO)
    if not isinstance(unidad, str) or not unidad.strip():
        raise ReciboInvalido("unidad debe ser una cadena no vacia")

    return Recibo(
        area=str(doc.get("area") or "?"),
        instrumento=str(doc.get("instrumento") or "?"),
        version=doc.get("version"),
        dominio=_entero(doc.get("dominio"), "dominio"),
        cubetas=cubetas,
        unidad=unidad.strip(),
        digest_entrada=_digest(digests.get("entrada"), "digests.entrada"),
        digest_salida=_digest(digests.get("salida"), "digests.salida"),
        artefacto=str(doc["artefacto"]) if doc.get("artefacto") else None,
        digest_artefacto=_digest(digests.get("artefacto"), "digests.artefacto"),
        declarado_conserva=conserva,
        declarado_rc=rc,
    )


def cargar(ruta: Path) -> Recibo:
    return desde_documento(json.loads(Path(ruta).read_text(encoding="utf-8")))


def a_documento(r: Recibo) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "schema": ESQUEMA,
        "area": r.area,
        "instrumento": r.instrumento,
        "dominio": r.dominio,
        "unidad": r.unidad,
        "cubetas": dict(r.cubetas),
    }
    if r.version:
        doc["version"] = r.version
    digests = {k: v for k, v in
               (("entrada", r.digest_entrada), ("salida", r.digest_salida),
                ("artefacto", r.digest_artefacto)) if v}
    if digests:
        doc["digests"] = digests
    if r.artefacto:
        doc["artefacto"] = r.artefacto
    declarado = {k: v for k, v in
                 (("conserva", r.declarado_conserva), ("rc", r.declarado_rc))
                 if v is not None}
    if declarado:
        doc["declarado"] = declarado
    return doc
