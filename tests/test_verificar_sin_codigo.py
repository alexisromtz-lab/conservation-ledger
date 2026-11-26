"""El certificado se confirma sin nuestro código: ``verify.sh`` y la ley tienen que cuadrar.

El script del raíz no importa nada de este paquete. Si sus números coinciden con
los de ``cadena()`` término a término, la ley no es un artefacto de nuestra
implementación; si discreparan en una celda, lo sería.
"""
import os
import re
import subprocess

from conftest import RAIZ
from conservation_ledger.cadena import cadena
from conservation_ledger.cli import _leer

FIX = RAIZ / "tests" / "fixtures" / "cadena"
ART = FIX / "artefactos"
GUION = RAIZ / "verify.sh"
CENSO = (FIX / "paso1-censo.json", FIX / "paso2-censo.json", FIX / "paso3-censo.json")
COMPUESTO = re.compile(
    r"^COMPUESTO (\d+) = (\d+) \+ (\d+) residuo (-?\d+) (\S+) telescopia (\S+)$", re.M
)


def _bloques() -> list[str]:
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    seccion = re.search(r"^## Verifying without our code.*?(?=^## )", texto, re.S | re.M)
    assert seccion, "README.md no tiene la sección 'Verifying without our code'"
    bloques = re.findall(r"```console\n(.*?)```", seccion.group(0), re.S)
    assert len(bloques) == 5, f"se esperaban 5 corridas publicadas, hay {len(bloques)}"
    return [
        "\n".join(l for l in b.rstrip("\n").split("\n") if not l.startswith("$ "))
        for b in bloques
    ]


def _correr(*args: object) -> tuple[int, str]:
    proceso = subprocess.run([str(GUION), *map(str, args)], cwd=RAIZ,
                             capture_output=True, text=True, check=False)
    return proceso.returncode, proceso.stdout.rstrip("\n")


def _numeros(salida: str) -> tuple[int, int, int, int, str, str]:
    hallado = COMPUESTO.search(salida)
    assert hallado, f"el script no publicó su compuesto:\n{salida}"
    dominio, imagen, restos, residuo, estado, tele = hallado.groups()
    return int(dominio), int(imagen), int(restos), int(residuo), estado, tele


def test_el_script_es_ejecutable():
    assert os.access(GUION, os.X_OK), "verify.sh tiene que viajar con el bit de ejecución"


def test_la_cadena_sellada_sin_nuestro_codigo():
    rc, salida = _correr("-d", ART, FIX / "paso1.json", FIX / "paso2.json")
    assert salida == _bloques()[0]
    assert rc == 1, "una cadena sellada no lava la colisión que el primer acto declaró"


def test_la_ruptura_sin_nuestro_codigo():
    rc, salida = _correr("-d", ART, FIX / "paso1.json", FIX / "paso2-alterado.json")
    assert salida == _bloques()[1]
    assert rc == 4
    assert "filas 3 -> 3 ok" in salida, "el conteo sigue ciego: ése es el hallazgo"
    assert "bytes !" in salida


def test_la_cadena_de_tres_enlaces_sin_nuestro_codigo():
    rc, salida = _correr(*CENSO)
    assert salida == _bloques()[2]
    assert rc == 1
    assert "NO_MEDIDO" in salida, "lo que no pudo abrir lo declara, no lo aprueba"


def test_las_dos_implementaciones_cuadran_termino_a_termino():
    for rutas in ((FIX / "paso1.json", FIX / "paso2.json"),
                  (FIX / "paso1.json", FIX / "paso2-alterado.json"),
                  CENSO):
        rc, salida = _correr(*rutas)
        comp = cadena(_leer(rutas, None))
        dominio, imagen, restos, residuo, estado, tele = _numeros(salida)
        assert (dominio, imagen, restos, residuo) == (
            comp.dominio, comp.imagen, comp.restos, comp.residuo)
        assert tele == ("si" if comp.telescopia else "NO")
        assert estado == ("ok" if comp.residuo == 0 else "!")
        assert rc == comp.rc, f"el script y la ley discrepan en el RC de {rutas}"


def test_el_veredicto_no_colapsa_dos_poblaciones():
    """Misma aritmetica, media cadena sin medir: `chain` dice 0, el script dice 2.

    El compositor lee recibos y un recibo sin `salida.archivo` le parece completo:
    la particion de una sola poblacion cierra siempre. El unico que puede abrir el
    fichero es el script, y por eso su RC es un refinamiento del del compositor.
    """
    rutas = (FIX / "paso2-completo.json", FIX / "paso2.json")
    rc, salida = _correr("-d", ART, *rutas)
    assert salida == _bloques()[3]
    assert "COBERTURA nivel2=1/2" in salida
    assert "nivel 1 (el recibo no publica archivo" in salida
    assert rc == 2, "un acto que no midio su fichero no deja la cadena conservada"

    comp = cadena(_leer(rutas, None))
    dominio, imagen, restos, residuo, _, _ = _numeros(salida)
    assert (dominio, imagen, restos, residuo) == (
        comp.dominio, comp.imagen, comp.restos, comp.residuo), "la aritmetica coincide"
    assert comp.rc == 0, "el compositor, ciego al fichero, aprueba la misma cadena"
    assert rc != comp.rc, "si ambos veredictos coincidieran, la cobertura no mediria nada"


def test_la_cobertura_completa_sigue_dando_cero():
    """La regla de cobertura no puede hacer el cero inalcanzable."""
    rc, salida = _correr("-d", ART, FIX / "paso2-completo.json", FIX / "paso3.json")
    assert salida == _bloques()[4]
    assert "COBERTURA nivel2=2/2" in salida
    assert rc == 0

    # Entre las dos corridas sólo cambian la cobertura y el RC: misma ecuacion.
    _, sin_medir = _correr("-d", ART, FIX / "paso2-completo.json", FIX / "paso2.json")
    assert _numeros(salida)[:4] == _numeros(sin_medir)[:4]


def test_las_tres_ordenas_del_auditor():
    """Las tres celdas de la tabla se miden con shasum y wc, sin Python."""
    artefacto = ART / "paso1.csv"
    digest = subprocess.run(["shasum", "-a", "256", str(artefacto)], capture_output=True,
                            text=True, check=True).stdout.split()[0]
    lineas = subprocess.run(["wc", "-l"], stdin=artefacto.open("rb"),
                            capture_output=True, text=True, check=True)
    assert digest.startswith("ede784ce0813c547")
    assert int(lineas.stdout.split()[0]) == 4
    # el commit be9b01d publico «62 bytes»: el fichero mide 59 (medido 25-Nov-2026)
    assert artefacto.stat().st_size == 59
    recibo = (FIX / "paso1.json").read_text(encoding="utf-8")
    assert digest in recibo, "el digest medido tiene que ser el que el recibo publica"


def test_el_fichero_aporta_lo_que_los_digests_no_dicen(tmp_path):
    """Mismo recibo, fichero manipulado: la costura sigue 'ok' y el artefacto no."""
    falso = tmp_path / "paso1.csv"
    falso.write_text((ART / "paso1.csv").read_text(encoding="utf-8").replace(
        "7771234567,A-1", "7771234567,A-9"), encoding="utf-8")
    rc, salida = _correr("-d", tmp_path, FIX / "paso1.json", FIX / "paso2.json")
    assert "ARTEFACTO paso1.csv sha256 !" in salida
    assert "bytes ok" in salida, "los digests declarados no cambian: por eso hay que abrir el fichero"
    assert rc == 4
