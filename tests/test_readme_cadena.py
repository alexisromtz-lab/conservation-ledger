"""Las dos corridas publicadas en README §Chains son las que produce el binario.

Los recibos de ``tests/fixtures/cadena/`` son los que escribió
``ingest-conservation-guard`` sobre el fixture de seis filas, no fixtures a mano:
si el formato de la costura cambia, estas dos líneas dejan de coincidir.
"""
import re

from conftest import RAIZ
from conservation_ledger import cli
from conservation_ledger.cadena import cadena
from conservation_ledger.cli import _leer

FIX = RAIZ / "tests" / "fixtures" / "cadena"


def _bloques() -> list[str]:
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    seccion = re.search(r"^## Chains.*?(?=^## )", texto, re.S | re.M)
    assert seccion, "README.md no tiene la sección Chains"
    bloques = re.findall(r"```console\n(.*?)```", seccion.group(0), re.S)
    assert len(bloques) == 3, f"se esperaban 3 corridas publicadas, hay {len(bloques)}"
    return [
        "\n".join(l for l in b.rstrip("\n").split("\n") if not l.startswith("$ "))
        for b in bloques
    ]


def _correr(capsys, *rutas) -> tuple[int, str]:
    capsys.readouterr()
    rc = cli.main(["chain", *[str(r) for r in rutas]])
    return rc, capsys.readouterr().out.rstrip("\n")


def test_la_cadena_sellada_publicada_es_la_que_corre(capsys):
    rc, salida = _correr(capsys, FIX / "paso1.json", FIX / "paso2.json")
    assert salida == _bloques()[0]
    assert rc == 1, "una cadena sellada no lava la colisión que el primer acto declaró"


def test_la_cadena_rota_publicada_es_la_que_corre(capsys):
    rc, salida = _correr(capsys, FIX / "paso1.json", FIX / "paso2-alterado.json")
    assert salida == _bloques()[1]
    assert rc == 4


def test_la_ruptura_publicada_dice_que_la_costura_es_por_bytes(capsys):
    _, salida = _correr(capsys, FIX / "paso1.json", FIX / "paso2-alterado.json")
    assert "filas 3 -> 3" in salida, "el conteo debe seguir coincidiendo: es el punto ciego"
    assert "bytes !" in salida
    assert "no es el que el acto anterior escribio" in salida


def test_la_cadena_de_tres_enlaces_publicada_es_la_que_corre(capsys):
    rc, salida = _correr(
        capsys, FIX / "paso1-censo.json", FIX / "paso2-censo.json", FIX / "paso3-censo.json"
    )
    assert salida == _bloques()[2]
    assert rc == 1
    assert salida.count("SELLADO") == 2, "tres actos dejan dos costuras, ni una más"
    assert "telescopia=si" in salida and "residuo=0" in salida


def test_el_residuo_compuesto_es_la_suma_de_los_residuos_de_los_enlaces():
    """La ruta del telescopio: d(1) = img(n) + Σ resto(i), con tres enlaces reales."""
    rutas = [FIX / "paso1-censo.json", FIX / "paso2-censo.json", FIX / "paso3-censo.json"]
    comp = cadena(_leer(rutas, None))
    assert comp.restos == 2024 + 32141 + 0 == 34165
    assert comp.residuo_de_los_enlaces == 0, "los tres residuos se suman sin faltar ni sobrar"
    assert comp.dominio == comp.imagen + comp.restos == 34195
    assert comp.residuo == 0 and comp.telescopia
