import json
import subprocess
import sys

from conftest import RECIBOS, RAIZ
from conservation_ledger.cli import main


def test_verify_por_json_da_un_codigo_por_recibo(capsys):
    rc = main(["verify", "--json", *map(str, sorted(RECIBOS.glob("*.json")))])
    salida = json.loads(capsys.readouterr().out)
    assert rc == 4
    assert salida["rc"] == 4
    assert len(salida["recibos"]) == 16
    assert {r["clase"] for r in salida["recibos"]} == {"COLISION", "CONSERVADO", "DISCREPANCIA"}


def test_verify_imprime_una_linea_de_cierre(capsys):
    main(["verify", *map(str, sorted(RECIBOS.glob("*.json")))])
    texto = capsys.readouterr().out
    assert "LEDGER 16 recibos" in texto
    assert "RC=4" in texto


def test_un_recibo_mentiroso_puesto_en_disco_sale_con_ruptura(tmp_path, capsys):
    falso = tmp_path / "falso.json"
    falso.write_text(json.dumps({
        "schema": "conservation/1", "area": "falso", "instrumento": "x",
        "dominio": 10, "cubetas": {"imagen": 9},
        "declarado": {"conserva": True, "rc": 0}}), encoding="utf-8")
    assert main(["verify", str(falso)]) == 4
    assert "RUPTURA" in capsys.readouterr().out


def test_panel_escribe_el_fichero(tmp_path):
    destino = tmp_path / "panel.html"
    rc = main(["panel", "-o", str(destino), *map(str, sorted(RECIBOS.glob("*.json")))])
    assert rc == 4
    texto = destino.read_text(encoding="utf-8")
    assert texto.count("<tr>") == 20  # cabecera + 16 areas + cabecera y 2 unidades
    assert "DISCREPANCIA" in texto


def test_collect_ejecuta_un_instrumento_y_archiva_su_recibo(tmp_path, capsys):
    instrumento = tmp_path / "emitir.py"
    instrumento.write_text(
        "import json\n"
        "print(json.dumps({'schema':'conservation/1','area':'eco','instrumento':'e',\n"
        "                  'dominio':4,'cubetas':{'a':3,'b':1}}))\n",
        encoding="utf-8")
    manifiesto = tmp_path / "m.json"
    manifiesto.write_text(json.dumps({"areas": [{
        "area": "eco", "cmd": [sys.executable, str(instrumento)], "adapter": "raw"}]}),
        encoding="utf-8")
    salida = tmp_path / "receipts"
    assert main(["collect", str(manifiesto), "-o", str(salida)]) == 0
    (unico,) = list(salida.glob("*.json"))
    doc = json.loads(unico.read_text(encoding="utf-8"))
    assert (doc["area"], doc["dominio"], doc["cubetas"]) == ("eco", 4, {"a": 3, "b": 1})


def test_un_instrumento_que_revienta_no_se_archiva_como_exito(tmp_path):
    manifiesto = tmp_path / "m.json"
    manifiesto.write_text(json.dumps({"areas": [{
        "area": "malo", "cmd": [sys.executable, "-c", "import sys; sys.exit(9)"]}]}),
        encoding="utf-8")
    try:
        main(["collect", str(manifiesto), "-o", str(tmp_path / "r")])
    except SystemExit as exc:
        assert "fallo" in str(exc)
    else:
        raise AssertionError("un instrumento roto debe detener el acto")
