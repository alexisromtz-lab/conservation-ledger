"""The only instrument-aware code in the package, and it is deliberately dumb.

An adapter renames keys. It never computes a residual, never decides a verdict,
never invents a bucket that the producer did not publish. Everything an adapter
produces is handed to :mod:`conservation_ledger.verificador`, which cannot see
which adapter ran.

Adding an adapter is cheap; adding a branch in the verifier is not.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .esquema import Recibo, desde_documento


def _nombre(valor: Any, defecto: str) -> str:
    if not valor:
        return defecto
    return Path(str(valor)).name or defecto


def _dominio_acta(doc: dict[str, Any]) -> int:
    """Three shapes publish the size of the input, and none of them agrees on a name."""
    for candidato in (doc.get("dominio"),
                      (doc.get("entrada") or {}).get("filas"),
                      doc.get("suma")):
        if isinstance(candidato, int) and not isinstance(candidato, bool):
            return candidato
    return 0


def _version(doc: dict[str, Any]) -> str | None:
    """The version the producer stamps on itself, if it stamps one.

    A receipt that cannot name its author cannot be dated; the panel says
    ``SIN_VERSION`` rather than inventing one.
    """
    v = doc.get("instrument_version")
    return str(v) if v else None


def desde_acta(doc: dict[str, Any]) -> Recibo:
    """``ingest-conservation-guard --receipt``.

    With ``--crudo`` the equation splits collisions into projection and repeat;
    without it the split is absent and the receipt closes over the total. Both
    forms are the same identity, so both are accepted.
    """
    ecuacion = doc.get("ecuacion")
    if isinstance(ecuacion, dict):
        cubetas = {k: v for k, v in ecuacion.items() if k != "dominio"}
        dominio = ecuacion.get("dominio", _dominio_acta(doc))
    else:
        cubetas = dict(doc.get("cubetas") or {})
        dominio = _dominio_acta(doc)
    entrada = doc.get("entrada") or {}
    salida = doc.get("salida") or {}
    declarado = doc.get("declarado") or {}
    return Recibo(
        area=f"acta:{_nombre(doc.get('caso'), '?')}",
        instrumento=str(doc.get("instrument") or "ingest-conservation-guard"),
        version=_version(doc),
        dominio=int(dominio),
        cubetas={str(k): int(v) for k, v in cubetas.items()},
        unidad="filas",
        digest_entrada=entrada.get("sha256"),
        digest_salida=salida.get("sha256"),
        artefacto=salida.get("archivo"),
        digest_artefacto=salida.get("sha256_archivo"),
        declarado_conserva=declarado.get("conserva", doc.get("conserva")),
        declarado_rc=declarado.get("rc", doc.get("rc")),
    )


def desde_fiber(doc: dict[str, Any]) -> Recibo:
    """``fiber-ast-lint --json``: the store census of one tree.

    ``raiz`` is an absolute path, so only its last segment is kept: a receipt
    that names the machine that produced it is not portable, and the ledger is
    meant to be handed to somebody else.
    """
    cubetas = {k: int(doc.get(k, 0) or 0) for k in
               ("pierde", "guardadas", "acumulacion", "posicional", "sin_len")}
    return Recibo(
        area=f"fiber:{_nombre(doc.get('raiz'), '?')}",
        instrumento=str(doc.get("instrument") or "fiber-ast-lint"),
        version=_version(doc),
        dominio=int(doc.get("almacenes", 0) or 0),
        cubetas=cubetas,
        unidad="almacenes",
        declarado_conserva=doc.get("reconcilia"),
        declarado_rc=doc.get("rc"),
    )


CUBETAS_CENSO = ("pierde", "guardadas", "acumulacion", "posicional", "sin_len")


def desde_censo(doc: dict[str, Any]) -> list[Recibo]:
    """``fiber-ast-lint/censo.json``.

    Until the census published its buckets, each row stated ``reconciles: true``
    with nothing to prove it and the only honest reading was
    ``NO_VERIFICABLE``. The adapter did not reconstruct the terms from
    ``pierde`` -- that would be inventing the evidence that was withheld. Now
    that the rows carry them, the equation is handed over intact; rows written
    before that change still yield no buckets and are still not certified.
    """
    recibos: list[Recibo] = []
    for fila in doc.get("rows") or []:
        version = fila.get("version")
        paquete = fila.get("package", "?")
        # ``mypy 2.4.1`` names two subjects (195 files scoped to the package,
        # 336 scoped to the wheel root). A label that fits two subjects is not
        # an identifier, so the scope joins the name when it differs.
        scope = str(fila.get("scope") or "")
        etiqueta = f"{paquete}@{version or '?'}"
        if scope and scope != paquete:
            etiqueta += f"#{scope}"
        recibos.append(Recibo(
            area=f"censo:{etiqueta}",
            instrumento="fiber-ast-lint",
            # ``version`` es la firma del instrumento; la version del paquete
            # auditado ya viaja en el area (``censo:mypy@2.4.1#mypy/``).
            version=_version(doc),
            dominio=int(fila.get("stores", 0) or 0),
            cubetas=({k: int(fila[k]) for k in CUBETAS_CENSO}
                     if all(k in fila for k in CUBETAS_CENSO) else {}),
            unidad="almacenes",
            digest_entrada=fila.get("sha256"),
            # Dos superficies con dos nombres. `certifica` es la firma y desde
            # 0.4.6 viaja como booleano propio; las filas anteriores lo plegaban
            # en `reconciles`. El entero es el problema: `rc` significa "encontre
            # candidatos" para el linter y "declare una colision" para este
            # contrato, asi que no vota -- se publica como evidencia bajo su
            # nombre (`rc`) y el codigo del acta no se lee de aqui.
            declarado_conserva=(fila["certifica"] if "certifica" in fila
                                else fila.get("reconciles")),
            declarado_rc=None,
            declarado_rc_escaneo=fila.get("rc"),
        ))
    return recibos


def desde_crudo(doc: dict[str, Any]) -> list[Recibo]:
    """A ``conservation/1`` document, or a list of them."""
    if isinstance(doc, list):
        return [desde_documento(d) for d in doc]
    return [desde_documento(doc)]


def _uno_o_varios(
    fn: Callable[[dict[str, Any]], Recibo],
) -> Callable[[Any], list[Recibo]]:
    """An instrument may emit one record or a list of them; the ledger sees a list."""

    def aplicar(doc: Any) -> list[Recibo]:
        if isinstance(doc, list):
            return [fn(d) for d in doc]
        return [fn(doc)]

    return aplicar


ADAPTADORES: dict[str, Callable[[Any], list[Recibo]]] = {
    "acta": _uno_o_varios(desde_acta),
    "fiber": _uno_o_varios(desde_fiber),
    "censo": desde_censo,
    "raw": desde_crudo,
}


def adaptar(nombre: str, doc: Any) -> list[Recibo]:
    try:
        fn = ADAPTADORES[nombre]
    except KeyError:
        raise ValueError(f"adaptador desconocido: {nombre!r} "
                         f"(validos: {', '.join(sorted(ADAPTADORES))})") from None
    return fn(doc)
