"""One ledger for every conservation instrument.

The suite audits different things -- tabular ingests, Python store censuses,
git histories -- but they all close the same identity: what entered equals what
landed in a bucket that someone named. This package reads those receipts and
recomputes the identity from the terms alone, so a producer cannot certify
itself.

    dominio == sum(cubetas)          # recomputed here, never trusted
"""
from __future__ import annotations

__version__ = "0.1.0"

from .esquema import ESQUEMA, Recibo, ReciboInvalido, cargar, desde_documento
from .verificador import Veredicto, verificar

__all__ = ["ESQUEMA", "Recibo", "ReciboInvalido", "Veredicto", "cargar",
           "desde_documento", "verificar", "__version__"]
