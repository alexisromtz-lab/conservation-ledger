"""One page for every area: the equation, the residual, and who said what.

The panel is static HTML with no scripts: it is meant to be attached to an
email or committed next to a release, and to render the same way in five years.
Every cell is produced by :func:`conservation_ledger.verificador.verificar`, so
the page cannot flatter an instrument the verifier disagrees with.
"""
from __future__ import annotations

from html import escape

from .verificador import Veredicto, rc_del_acto

_CLASE_COLOR = {
    "CONSERVADO": "#1a7f37",
    "VACIO": "#9a6700",
    "NO_VERIFICABLE": "#9a6700",
    "RUPTURA": "#cf222e",
    "DISCREPANCIA": "#cf222e",
}


def ecuacion(v: Veredicto) -> str:
    if not v.cubetas:
        return f"{v.dominio} = ?"
    terminos = " + ".join(f"{n} {c}" for n, c in v.cubetas.items())
    return f"{v.dominio} = {terminos}  (residuo {v.residuo})"


def declaracion(v: Veredicto) -> str:
    """What the producer claimed, next to what this page recomputed."""
    if v.declarado_rc is None and v.declarado_conserva is None:
        return "—"
    partes = []
    if v.declarado_conserva is not None:
        partes.append(f"conserva={str(v.declarado_conserva).lower()}")
    if v.declarado_rc is not None:
        partes.append(f"rc={v.declarado_rc}")
    return " ".join(partes)


def tabla(veredictos: list[Veredicto]) -> list[dict]:
    """Deterministic rows, sorted by area: the panel's own contract."""
    filas = []
    for v in sorted(veredictos, key=lambda x: (x.area, x.instrumento)):
        filas.append({
            "area": v.area,
            "instrumento": v.instrumento,
            "ecuacion": ecuacion(v),
            "residuo": v.residuo,
            "declara": declaracion(v),
            "recomputa": v.clase,
            "rc": v.rc,
        })
    return filas


def tabla_md(veredictos: list[Veredicto]) -> str:
    """The same rows as the HTML, as a markdown table a test can pin."""
    lineas = ["| Área | Instrumento | Ecuación | Residuo | Declara | Recomputa |",
              "|---|---|---|---:|---|---|"]
    for f in tabla(veredictos):
        lineas.append(f"| `{f['area']}` | {f['instrumento']} | `{f['ecuacion']}` "
                      f"| {f['residuo']} | `{f['declara']}` | **{f['recomputa']}** |")
    return "\n".join(lineas)


def _recuento(veredictos: list[Veredicto]) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for v in veredictos:
        cuenta[v.clase] = cuenta.get(v.clase, 0) + 1
    return dict(sorted(cuenta.items()))


def html(veredictos: list[Veredicto], titulo: str = "Libro mayor de conservación") -> str:
    filas = tabla(veredictos)
    cuenta = _recuento(veredictos)
    rc = rc_del_acto(list(veredictos))

    cuerpo = "\n".join(
        "      <tr>"
        f"<td><code>{escape(f['area'])}</code></td>"
        f"<td>{escape(f['instrumento'])}</td>"
        f"<td><code>{escape(f['ecuacion'])}</code></td>"
        f"<td class=\"n\">{f['residuo']}</td>"
        f"<td><code>{escape(f['declara'])}</code></td>"
        f"<td class=\"c\" style=\"color:{_CLASE_COLOR.get(f['recomputa'], '#57606a')}\">"
        f"{escape(f['recomputa'])}</td>"
        "</tr>"
        for f in filas
    )

    resumen = " · ".join(f"{k} {v}" for k, v in cuenta.items()) or "sin recibos"
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{escape(titulo)}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         margin: 2rem auto; max-width: 68rem; padding: 0 1rem; color: #1f2328; }}
  h1 {{ font-size: 1.35rem; margin: 0 0 .25rem; }}
  p.sub {{ margin: 0 0 1.25rem; color: #57606a; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #d8dee4;
            vertical-align: top; }}
  th {{ font-size: .78rem; text-transform: uppercase; letter-spacing: .04em;
        color: #57606a; border-bottom: 2px solid #d8dee4; }}
  td.n {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.c {{ font-weight: 600; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .92em; }}
  footer {{ margin-top: 1.5rem; color: #57606a; font-size: .85rem; }}
</style>
</head>
<body>
  <h1>{escape(titulo)}</h1>
  <p class="sub">RC del acto <strong>{rc}</strong> · {len(filas)} áreas · {escape(resumen)}</p>
  <table>
    <thead><tr><th>Área</th><th>Instrumento</th><th>Ecuación</th><th>Residuo</th><th>Declara</th><th>Recomputa</th></tr></thead>
    <tbody>
{cuerpo}
    </tbody>
  </table>
  <footer>
    El residuo, la clase y el RC se recomputan aquí: el recibo aporta el dominio y las
    cubetas, nunca su propio veredicto. Un recibo sin términos es
    <code>NO_VERIFICABLE</code>, jamás <code>0</code>.
  </footer>
</body>
</html>
"""
