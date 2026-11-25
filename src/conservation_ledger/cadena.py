"""Composition: what two conserving acts prove about the pipeline between them.

A panel verifies receipts one at a time, and that is exactly as far as it can
see. Two acts can each close their own equation and still lose rows at the seam
between them -- the file the first act wrote is not, byte for byte, the file the
second act read. Nothing in a per-receipt verdict can notice, because the seam
belongs to neither receipt.

The seam needs two independent measurements, and they answer different
questions:

* **count** -- ``imagen(i) == dominio(i+1)``: the next act received as many rows
  as the previous act says it kept. Counting is blind to identity: rewrite one
  witness in a three-row export and the count still says three.
* **bytes** -- ``digests.artefacto(i) == digests.entrada(i+1)``: the act read
  the artifact the previous act wrote. This needs the producer to digest what it
  wrote; an act that digests an in-memory map leaves the seam ``NO_MEDIDO``.

Under both, the composite closes by telescoping. With ``d(i)`` the domain and
``img(i)`` the image of act ``i`` and ``resto(i)`` everything that is not the
image::

    d(i) = img(i) + resto(i)          each receipt closes
    d(i+1) = img(i)                   the seam

so ``d(1) = img(n) + sum(resto)`` and the composite residual equals the sum of
the link residuals. That is computed here twice, by two routes that never share
a term: if the two sums disagree the thing is not a chain, whatever the links
say. No degrees of freedom survive: sealing the seams leaves nothing to choose.
"""
from __future__ import annotations

from dataclasses import dataclass

from .esquema import Recibo
from .verificador import CONSERVADO, RUPTURA, VACIO, combinar, verificar

CADENA_ESQUEMA = "conservation/cadena/1"

SELLADO = "SELLADO"
ROTO = "RUPTURA"
CIEGO = "NO_MEDIDO"

#: A seam is a receipt of its own; its codes enter the composite like any other.
RC_COSTURA = {SELLADO: CONSERVADO, CIEGO: VACIO, ROTO: RUPTURA}


@dataclass(frozen=True)
class Costura:
    izquierda: str
    derecha: str
    filas_declaradas: int | None
    filas_recibidas: int
    digest_declarado: str | None
    digest_recibido: str | None
    estado: str

    @property
    def motivos(self) -> tuple[str, ...]:
        if self.estado == SELLADO:
            return ()
        if self.estado == ROTO:
            razones = []
            if (self.digest_declarado and self.digest_recibido
                    and self.digest_declarado != self.digest_recibido):
                razones.append("el artefacto no es el que el acto anterior escribio")
            if self.filas_declaradas is not None and self.filas_declaradas != self.filas_recibidas:
                razones.append(f"declaro {self.filas_declaradas} filas y recibio "
                               f"{self.filas_recibidas}")
            return tuple(razones)
        falta = []
        if not self.digest_declarado:
            falta.append("el acto izquierdo no digiere su artefacto")
        if not self.digest_recibido:
            falta.append("el acto derecho no digiere su entrada")
        if self.filas_declaradas is None:
            falta.append("el acto izquierdo no publica su imagen")
        return tuple(falta) or ("la costura no se pudo medir",)

    def as_dict(self) -> dict[str, object]:
        return {
            "izquierda": self.izquierda,
            "derecha": self.derecha,
            "estado": self.estado,
            "filas_declaradas": self.filas_declaradas,
            "filas_recibidas": self.filas_recibidas,
            "digest_declarado": self.digest_declarado,
            "digest_recibido": self.digest_recibido,
            "motivos": list(self.motivos),
        }


@dataclass(frozen=True)
class Composicion:
    costuras: tuple[Costura, ...]
    dominio: int
    imagen: int | None
    restos: int
    residuo: int
    residuo_de_los_enlaces: int
    rc: int
    motivos: tuple[str, ...] = ()

    @property
    def conserva(self) -> bool:
        return self.rc == CONSERVADO

    @property
    def telescopia(self) -> bool:
        return self.residuo == self.residuo_de_los_enlaces

    def ecuacion(self) -> str:
        imagen = "?" if self.imagen is None else str(self.imagen)
        return f"{self.dominio} = {imagen} + {self.restos}"

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": CADENA_ESQUEMA,
            "costuras": [c.as_dict() for c in self.costuras],
            "compuesto": {
                "dominio": self.dominio,
                "imagen": self.imagen,
                "restos": self.restos,
                "residuo": self.residuo,
                "residuo_de_los_enlaces": self.residuo_de_los_enlaces,
                "telescopia": self.telescopia,
                "ecuacion": self.ecuacion(),
            },
            "rc": self.rc,
            "conserva": self.conserva,
            "motivos": list(self.motivos),
        }


def _costura(a: Recibo, b: Recibo) -> Costura:
    declaradas = a.cubetas.get("imagen")
    recibidas = b.dominio
    digest_a, digest_b = a.digest_artefacto, b.digest_entrada

    if digest_a and digest_b:
        bytes_iguales: bool | None = digest_a == digest_b
    else:
        bytes_iguales = None
    cuenta_igual: bool | None = None if declaradas is None else declaradas == recibidas

    if bytes_iguales is False or cuenta_igual is False:
        estado = ROTO
    elif bytes_iguales is True and cuenta_igual is True:
        estado = SELLADO
    else:
        estado = CIEGO

    return Costura(izquierda=a.area, derecha=b.area, filas_declaradas=declaradas,
                   filas_recibidas=recibidas, digest_declarado=digest_a,
                   digest_recibido=digest_b, estado=estado)


def cadena(recibos: list[Recibo]) -> Composicion:
    """Compose ordered receipts into the one verdict the pipeline deserves.

    The composite never improves on its worst link or its worst seam: a chain is
    as conserved as its least conserved step, and a seam nobody measured is not
    a seam that held.
    """
    if len(recibos) < 2:
        raise ValueError("una cadena exige al menos dos actos")

    unidades = {r.unidad for r in recibos}
    if len(unidades) > 1:
        # `30 rows + 12 stores` is not 42 of anything.
        return Composicion(costuras=(), dominio=0, imagen=None, restos=0, residuo=0,
                           residuo_de_los_enlaces=0, rc=VACIO,
                           motivos=(f"unidades distintas en la cadena: "
                                    f"{', '.join(sorted(unidades))}: no hay cadena "
                                    "que componer",))
    if any("imagen" not in r.cubetas for r in recibos):
        return Composicion(costuras=(), dominio=0, imagen=None, restos=0, residuo=0,
                           residuo_de_los_enlaces=0, rc=VACIO,
                           motivos=("algun acto no publica su imagen: sin imagen no "
                                    "hay salida que el siguiente pueda recibir",))

    costuras = [_costura(a, b) for a, b in zip(recibos, recibos[1:])]

    dominio = recibos[0].dominio
    imagen = recibos[-1].cubetas.get("imagen")
    restos = sum(sum(v for k, v in r.cubetas.items() if k != "imagen") for r in recibos)
    residuo = dominio - ((imagen or 0) + restos)
    residuo_enlaces = sum(r.dominio - sum(r.cubetas.values()) for r in recibos)

    motivos: list[str] = []
    if residuo != 0:
        motivos.append(f"el residuo compuesto es {residuo}: {abs(residuo)} unidades "
                       "entraron al primer acto y no llegan al ultimo")
    if residuo != residuo_enlaces:
        motivos.append(f"el telescopio no cierra: compuesto {residuo} contra "
                       f"enlaces {residuo_enlaces}: esto no es una cadena")
    for c in costuras:
        for m in c.motivos:
            motivos.append(f"{c.izquierda} -> {c.derecha}: {m}")

    rc = combinar(*(v.rc for v in (verificar(r) for r in recibos)),
                  *(RC_COSTURA[c.estado] for c in costuras),
                  RUPTURA if residuo != 0 or residuo != residuo_enlaces else CONSERVADO)

    return Composicion(costuras=tuple(costuras), dominio=dominio, imagen=imagen,
                       restos=restos, residuo=residuo,
                       residuo_de_los_enlaces=residuo_enlaces, rc=rc,
                       motivos=tuple(motivos))


__all__ = ["CADENA_ESQUEMA", "CIEGO", "ROTO", "SELLADO", "Composicion", "Costura",
           "cadena"]
