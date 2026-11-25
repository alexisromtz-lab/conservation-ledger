"""Four verbs: ``verify``, ``chain``, ``panel``, ``collect``.

``verify``  re-derives each receipt's verdict and prints where it disagrees.
``chain``   composes an ordered pipeline and judges it on its seams: two acts
            that each close their equation can still lose rows between them.
``panel``   renders every area into one static page.
``collect`` runs a manifest of instruments and files their receipts, so the
            whole estate is refreshed by one command instead of by memory.

Exit codes are the supremum of the receipts' codes (``4 > 1 > 2 > 0``), so a
run that could not look is never reported as a run that found nothing.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from . import __version__
from .adaptadores import adaptar
from .cadena import cadena
from .esquema import ESQUEMA, Recibo, a_documento, desde_documento
from .panel import html
from .verificador import Veredicto, rc_del_acto, verificar


def _detectar(doc: Any) -> str:
    if isinstance(doc, list):
        return "raw"
    if not isinstance(doc, dict):
        raise ValueError("el recibo debe ser un objeto o una lista JSON")
    if doc.get("schema") == ESQUEMA:
        return "raw"
    if doc.get("acta"):
        return "acta"
    if "almacenes" in doc:
        return "fiber"
    if doc.get("rows") and doc.get("instrument"):
        return "censo"
    raise ValueError("no se reconoce la forma del documento: declara --adapter")


def _leer(rutas: Iterable[Path], adaptador: str | None) -> list[Recibo]:
    recibos: list[Recibo] = []
    for ruta in rutas:
        doc = json.loads(Path(ruta).read_text(encoding="utf-8"))
        recibos.extend(adaptar(adaptador or _detectar(doc), doc))
    return recibos


def _pares(recibos: list[Recibo]) -> list[tuple[Recibo, Veredicto]]:
    return [(r, verificar(r)) for r in recibos]


def _rc(pares: list[tuple[Recibo, Veredicto]]) -> int:
    return rc_del_acto([v for _, v in pares])


def _cmd_verify(args: argparse.Namespace) -> int:
    pares = _pares(_leer(args.recibos, args.adapter))
    if args.json:
        print(json.dumps({
            "schema": ESQUEMA,
            "ledger_version": __version__,
            "rc": _rc(pares),
            "recibos": [v.as_dict() for _, v in pares],
        }, indent=2, ensure_ascii=False, sort_keys=False))
        return _rc(pares)

    for r, v in pares:
        marca = "ok " if v.conserva else "!! "
        declara = "" if v.declarado_rc is None else f" (declara rc={v.declarado_rc})"
        print(f"{marca}{v.area:<34} {v.instrumento:<26} rc={v.rc} {v.clase}{declara}")
        if v.motivos:
            for m in v.motivos:
                print(f"     - {m}")
    cuenta = {}
    for _, v in pares:
        cuenta[v.clase] = cuenta.get(v.clase, 0) + 1
    resumen = " · ".join(f"{k} {n}" for k, n in sorted(cuenta.items())) or "sin recibos"
    print(f"LEDGER {len(pares)} recibos · {resumen} · RC={_rc(pares)}")
    return _rc(pares)


def _cmd_chain(args: argparse.Namespace) -> int:
    recibos = _leer(args.recibos, args.adapter)
    if len(recibos) < 2:
        print("CHAIN: una cadena exige al menos dos actos", file=sys.stderr)
        return 2
    comp = cadena(recibos)
    if args.json:
        print(json.dumps(comp.as_dict(), indent=2, ensure_ascii=False))
        return comp.rc

    for c in comp.costuras:
        if not c.digest_declarado or not c.digest_recibido:
            bytes_estado = "?"
        else:
            bytes_estado = "=" if c.digest_declarado == c.digest_recibido else "!"
        print(f"{c.estado:<9} {c.izquierda} -> {c.derecha}"
              f"  filas {c.filas_declaradas} -> {c.filas_recibidas}  bytes {bytes_estado}")
    print(f"COMPUESTO {comp.ecuacion()}  residuo={comp.residuo}"
          f"  telescopia={'si' if comp.telescopia else 'NO'}  RC={comp.rc}")
    for m in comp.motivos:
        print(f"     - {m}")
    return comp.rc


def _cmd_panel(args: argparse.Namespace) -> int:
    pares = _pares(_leer(args.recibos, args.adapter))
    texto = html([v for _, v in pares], titulo=args.titulo)
    if args.out:
        Path(args.out).write_text(texto, encoding="utf-8")
        print(f"PANEL {args.out} · {len(pares)} areas · RC={_rc(pares)}")
    else:
        sys.stdout.write(texto)
    return _rc(pares)


def _cmd_collect(args: argparse.Namespace) -> int:
    manifiesto = json.loads(Path(args.manifiesto).read_text(encoding="utf-8"))
    areas = manifiesto.get("areas") or []
    destino = Path(args.out)
    destino.mkdir(parents=True, exist_ok=True)
    veredictos: list[Veredicto] = []
    for area in areas:
        nombre = area.get("area") or ""
        cmd = area.get("cmd")
        if not isinstance(cmd, list) or not cmd:
            raise SystemExit(f"area {nombre!r}: 'cmd' debe ser una lista no vacia")
        proceso = subprocess.run(cmd, cwd=area.get("cwd"), capture_output=True,
                                 text=True, check=False)
        if proceso.returncode not in (0, 1):
            raise SystemExit(f"area {nombre!r}: el instrumento fallo "
                             f"(rc={proceso.returncode}): {proceso.stderr.strip()[:300]}")
        doc = json.loads(proceso.stdout)
        recibos = adaptar(area.get("adapter") or _detectar(doc), doc)
        for recibo in recibos:
            doc_recibo = a_documento(recibo)
            doc_recibo["area"] = nombre or recibo.area
            salida = destino / f"{area.get('archivo', recibo.area).replace(':', '-')}.json"
            salida.write_text(json.dumps(doc_recibo, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
            veredicto = verificar(recibo)
            veredictos.append(veredicto)
            print(f"COLLECT {salida} · rc={veredicto.rc} {veredicto.clase}")
    print(f"COLLECT {len(areas)} areas · {len(veredictos)} recibos")
    return rc_del_acto(veredictos)



def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="conservation-ledger", description=__doc__)
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="verbo", required=True)

    def comun(p: argparse.ArgumentParser) -> None:
        p.add_argument("recibos", nargs="+", type=Path)
        p.add_argument("--adapter", choices=["acta", "fiber", "censo", "raw"],
                       help="forzar el adaptador en vez de detectarlo")

    v = sub.add_parser("verify", help="re-derivar el veredicto de cada recibo")
    comun(v)
    v.add_argument("--json", action="store_true")
    v.set_defaults(fn=_cmd_verify)

    h = sub.add_parser("chain", help="componer actos encadenados y juzgar sus costuras")
    comun(h)
    h.add_argument("--json", action="store_true")
    h.set_defaults(fn=_cmd_chain)

    p = sub.add_parser("panel", help="una pagina estatica con todas las areas")
    comun(p)
    p.add_argument("-o", "--out", help="escribir aqui en vez de por stdout")
    p.add_argument("--titulo", default="Libro mayor de conservación")
    p.set_defaults(fn=_cmd_panel)

    c = sub.add_parser("collect", help="ejecutar un manifiesto de instrumentos")
    c.add_argument("manifiesto", type=Path)
    c.add_argument("-o", "--out", default="receipts")
    c.set_defaults(fn=_cmd_collect)

    args = ap.parse_args(argv)
    return args.fn(args)
