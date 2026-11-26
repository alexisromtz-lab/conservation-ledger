"""The verifier knows the identity, not the instrument.

It reads ``dominio`` and ``cubetas`` and derives everything else. There is no
branch, table or registry keyed by instrument name in this module: if a future
instrument cannot be verified here, the receipt is wrong, not the verifier.

Rule set (the whole contract):

* ``residuo = dominio - sum(cubetas)`` -- recomputed, never read.
* ``conserva`` is ``True`` when the residual is zero: the units are accounted
  for. It says nothing about whether merging them was desirable, only that no
  unit vanished.
* A bucket named ``colisiones_*`` holding more than zero means entries were
  merged into another; that is ``RC 1``. The name is part of the schema, not a
  per-instrument convention, so the verifier still needs no registry.
* A receipt with no buckets is ``NO_VERIFICABLE`` (``RC 2``), never ``0``: not
  having published the terms is not the same as having conserved.
* A receipt over an empty domain may not certify. There ``0 = 0`` closes
  because there was nothing to hold, so a declared ``conserva=true`` or a
  declared ``RC 0/1`` claims a conservation the population cannot support: that
  is ``DISCREPANCIA`` (``RC 4``), not ``VACIO``. Silence about the emptiness is
  still ``VACIO`` (``RC 2``), because an act that measured nothing is not a lie.
* A declared ``conserva``/``rc`` that contradicts the identity is
  ``DISCREPANCIA`` (``RC 4``). A producer that misreports its own equation is
  worse than one that admits a rupture.

Precedence is the corpus table (``4 > 1 > 2 > 0``), deliberately identical to
``ingest_conservation_guard.rc``: two packages that combine the same four names
under different orders are worse than one package with a coarse code.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .esquema import UNIDAD_POR_DEFECTO, Recibo

CONSERVADO, COLISION, VACIO, RUPTURA = 0, 1, 2, 4

CONSERVADO_CLASE = "CONSERVADO"
COLISION_CLASE = "COLISION"
NO_VERIFICABLE = "NO_VERIFICABLE"
VACIO_CLASE = "VACIO"
RUPTURA_CLASE = "RUPTURA"
DISCREPANCIA = "DISCREPANCIA"

#: Verdicts that mean "the producer's own claim was contradicted", not merely
#: "the producer found something".
DEFECTOS = (RUPTURA_CLASE, DISCREPANCIA)

#: The corpus order. ``max`` is not this operator: ``max(1, 2) == 2``.
PRECEDENCIA = {CONSERVADO: 0, VACIO: 1, COLISION: 2, RUPTURA: 3}


@dataclass(frozen=True)
class Veredicto:
    area: str
    instrumento: str
    dominio: int
    cubetas: dict[str, int]
    residuo: int
    rc: int
    clase: str
    unidad: str = UNIDAD_POR_DEFECTO
    version: str | None = None
    motivos: tuple[str, ...] = field(default=())
    declarado_rc: int | None = None
    declarado_conserva: bool | None = None
    declarado_rc_escaneo: int | None = None

    @property
    def conserva(self) -> bool:
        """No unit vanished. A merged entry that is accounted for still conserves."""
        return self.clase in (CONSERVADO_CLASE, COLISION_CLASE)

    @property
    def defectuoso(self) -> bool:
        return self.clase in DEFECTOS

    def as_dict(self) -> dict:
        return {
            "area": self.area,
            "instrumento": self.instrumento,
            "version": self.version,
            "dominio": self.dominio,
            "unidad": self.unidad,
            "cubetas": dict(self.cubetas),
            "residuo": self.residuo,
            "rc": self.rc,
            "clase": self.clase,
            "conserva": self.conserva,
            "motivos": list(self.motivos),
            "declarado_rc": self.declarado_rc,
            "declarado_conserva": self.declarado_conserva,
            "declarado_rc_escaneo": self.declarado_rc_escaneo,
        }


def _veredicto(r: Recibo, *, residuo: int, rc: int, clase: str,
               motivos: tuple[str, ...] = ()) -> Veredicto:
    return Veredicto(area=r.area, instrumento=r.instrumento, dominio=r.dominio,
                     cubetas=dict(r.cubetas), residuo=residuo, rc=rc, clase=clase,
                     unidad=r.unidad, version=r.version, motivos=motivos, declarado_rc=r.declarado_rc,
                     declarado_conserva=r.declarado_conserva,
                     declarado_rc_escaneo=r.declarado_rc_escaneo)


def fusiones(cubetas: dict[str, int]) -> int:
    """Entries that landed inside another entry, read off the bucket names."""
    return sum(v for k, v in cubetas.items() if k.startswith("colisiones"))


def verificar(r: Recibo) -> Veredicto:
    if not r.cubetas:
        return _veredicto(r, residuo=r.dominio, rc=VACIO, clase=NO_VERIFICABLE,
                          motivos=("el recibo no publica sus terminos: "
                                   "la identidad no se puede rehacer",))

    residuo = r.dominio - sum(r.cubetas.values())
    if residuo != 0:
        motivos = [f"el residuo es {residuo}: {abs(residuo)} unidades sin cubeta"]
        if r.declarado_conserva:
            motivos.append("el recibo declaraba conserva=true")
        return _veredicto(r, residuo=residuo, rc=RUPTURA, clase=RUPTURA_CLASE,
                          motivos=tuple(motivos))

    if r.dominio == 0:
        certifica = r.declarado_conserva is True or r.declarado_rc in (CONSERVADO, COLISION)
        if certifica:
            motivos = ["dominio vacio: 0 = 0 cierra porque no habia nada que conservar"]
            if r.declarado_conserva is True:
                motivos.append("el recibo declaraba conserva=true")
            if r.declarado_rc in (CONSERVADO, COLISION):
                motivos.append(f"el recibo declaraba rc={r.declarado_rc}")
            return _veredicto(r, residuo=0, rc=RUPTURA, clase=DISCREPANCIA,
                              motivos=tuple(motivos))
        return _veredicto(r, residuo=0, rc=VACIO, clase=VACIO_CLASE,
                          motivos=("dominio vacio: no se midio nada",))

    contradicciones: list[str] = []
    if r.declarado_conserva is False:
        contradicciones.append("declaraba conserva=false sobre una ecuacion cerrada")
    if r.declarado_rc in (VACIO, RUPTURA):
        contradicciones.append(
            f"declaraba rc={r.declarado_rc} sobre una ecuacion que cierra en 0")
    if contradicciones:
        return _veredicto(r, residuo=0, rc=RUPTURA, clase=DISCREPANCIA,
                          motivos=tuple(contradicciones))

    if fusiones(r.cubetas) > 0:
        return _veredicto(r, residuo=0, rc=COLISION, clase=COLISION_CLASE,
                          motivos=(f"{fusiones(r.cubetas)} entradas se fusionaron "
                                   "en otra y quedan contadas en su cubeta",))
    pendientes: tuple[str, ...] = ()
    if r.declarado_rc == COLISION:
        pendientes = ("declaraba una colision que los terminos no muestran",)
    return _veredicto(r, residuo=0, rc=CONSERVADO, clase=CONSERVADO_CLASE,
                      motivos=pendientes)


def normalizar(rc: int) -> int:
    """Fail-closed: an unknown code is a rupture, never a clean act."""
    return rc if rc in PRECEDENCIA else RUPTURA


def combinar(*rcs: int) -> int:
    """Supremum under the corpus order; an empty act is ``0``."""
    if not rcs:
        return CONSERVADO
    return max((normalizar(r) for r in rcs), key=lambda r: PRECEDENCIA[r])


def rc_del_acto(veredictos: list[Veredicto]) -> int:
    """Only recomputed codes enter the act: a receipt cannot vote for itself.

    A single unverifiable area neither covers the rest nor is covered by them --
    under ``4 > 1 > 2 > 0`` a collision outranks blindness, which is the corpus
    rule, so the counts are printed alongside the code, not encoded in it.
    """
    return combinar(*(v.rc for v in veredictos))
