from conftest import veredictos
from conservation_ledger.esquema import Recibo
from conservation_ledger.panel import html, tabla, tabla_md
from conservation_ledger.verificador import verificar


def test_una_fila_por_area_y_ordenadas():
    vs = veredictos()
    filas = tabla(vs)
    assert len(filas) == len(vs) == 16
    assert [f["area"] for f in filas] == sorted(f["area"] for f in filas)


def test_el_panel_muestra_lo_declarado_junto_a_lo_recomputado():
    filas = {f["area"]: f for f in tabla(veredictos())}
    acta = filas["acta:migracion.csv"]
    assert acta["declara"] == "conserva=true rc=1"
    assert acta["recomputa"] == "COLISION"
    assert acta["residuo"] == 0


def test_el_panel_no_repite_el_veredicto_del_productor():
    """Un area que declara conserva y no cierra se pinta RUPTURA, no CONSERVADO."""
    mentiroso = verificar(Recibo(area="m", instrumento="i", version=None, dominio=6,
                                 cubetas={"imagen": 5}, declarado_conserva=True))
    f = tabla([mentiroso])[0]
    assert (f["recomputa"], f["residuo"]) == ("RUPTURA", 1)


def test_el_html_escapa_el_nombre_del_area():
    v = verificar(Recibo(area="<script>x</script>", instrumento="i", version=None,
                         dominio=1, cubetas={"a": 1}))
    salida = html([v])
    assert "<script>x</script>" not in salida
    assert "&lt;script&gt;" in salida


def test_el_html_lleva_el_rc_del_acto():
    assert "RC del acto <strong>1</strong>" in html(veredictos())
    assert "16 áreas" in html(veredictos())


def test_la_tabla_markdown_es_reproducible():
    a = tabla_md(veredictos())
    assert a == tabla_md(veredictos())
    assert a.startswith("| Área | Instrumento |")
    assert a.count("\n") == 1 + 16
