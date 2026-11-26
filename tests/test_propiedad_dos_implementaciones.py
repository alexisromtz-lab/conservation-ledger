"""Las dos implementaciones de la ley tienen que decir lo mismo.

The published claim is one line: ``verify.sh`` exits ``0`` exactly when the
composer exits ``0`` **and** every act opened its artifact. Five fixtures fix the
cases we thought of; a seeded generator looks for the one we did not.

The generator also asserts its own sample. If a refactor stops producing an
uncovered chain, a broken seam or a self-contradicting receipt, this test fails
instead of passing vacuously.

The composer is called as a library: the ``chain`` verb is a thin wrapper over
``cadena()``, so what is crossed here is the algorithm, not an argument parser.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
from pathlib import Path

import pytest

from conftest import RAIZ
from conservation_ledger.adaptadores import desde_acta
from conservation_ledger.cadena import cadena

SEMILLA = 20261125
CASOS = 40

COBERTURA = re.compile(r"COBERTURA nivel2=(\d+)/(\d+)")
MODOS = ["ok", "ok", "ok", "bytes", "filas", "sin_archivo", "sin_digest", "ausente"]


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def _documento(*, caso: str, dominio: int, cubetas: dict[str, int],
               entrada_sha: str, salida: dict, conserva: bool, rc: int) -> dict:
    """An ``ingest-conservation-guard --receipt`` document, field for field."""
    return {
        "acta": "migracion",
        "caso": caso,
        "conserva": conserva,
        "cubetas": dict(cubetas),
        "ecuacion": {"dominio": dominio, **cubetas},
        "entrada": {"archivo": caso, "filas": dominio, "sha256": entrada_sha},
        "estado": "CONSERVADO" if conserva else "RUPTURA",
        "instrument": "ingest-conservation-guard",
        "instrument_version": "0.4.4",
        "perdidas_silenciosas": 0,
        "proyeccion": {"clave": "clave", "crudo": "clave", "validar": None},
        "rc": rc,
        "salida": dict(salida),
    }


def _un_caso(rng: random.Random, base: Path) -> tuple[list[Path], list[dict]]:
    n = rng.choice([2, 2, 3, 4])
    base.mkdir(parents=True, exist_ok=True)
    docs: list[dict] = []
    rutas: list[Path] = []
    prev_img = 0
    prev_sha: str | None = None

    for i in range(n):
        if i:
            if rng.random() < 0.85:
                dominio = prev_img
            else:
                dominio = max(0, prev_img + rng.choice([-1, 1]))
        else:
            dominio = rng.randint(1, 6)

        imagen = rng.randint(0, dominio)
        resto = dominio - imagen
        corte = rng.randint(0, resto)
        cubetas = {"imagen": imagen, "sin_clave": corte, "rechazos": resto - corte}
        if resto and rng.random() < 0.2:
            cubetas["colisiones"] = 1
            cubetas["sin_clave"] -= 1
        if rng.random() < 0.15:
            cubetas["sin_clave"] += 1  # la suma ya no cierra

        suma_cierra = sum(cubetas.values()) == dominio
        conserva = suma_cierra
        rc = 1 if cubetas.get("colisiones") else 0
        if suma_cierra and rng.random() < 0.15:
            conserva = False  # el recibo se contradice a si mismo
        if suma_cierra and rng.random() < 0.15:
            rc = 2  # declara ceguera sobre una ecuacion que cierra

        claves = rng.randint(0, 5)
        modo = rng.choice(MODOS)
        nombre = f"acto{i + 1}.csv"
        filas = [f"K{i}-{j}" for j in range(claves)]
        contenido = ("clave\n" + "".join(f"{f}\n" for f in filas)).encode()
        salida: dict[str, object] = {}

        if modo != "sin_archivo":
            salida["archivo"] = nombre
        if modo not in ("sin_archivo", "sin_digest"):
            salida["sha256_archivo"] = (
                _sha(contenido) if modo != "bytes" else _sha(b"otra cosa\n")
            )
        if modo != "sin_archivo":
            salida["claves"] = claves + 1 if modo == "filas" else claves
        salida["sha256"] = _sha(json.dumps(cubetas, sort_keys=True).encode())

        if modo not in ("sin_archivo", "ausente"):
            (base / nombre).write_bytes(contenido)

        doc = _documento(
            caso=nombre,
            dominio=dominio,
            cubetas=cubetas,
            entrada_sha=(
                "0" * 64 if i == 0
                else (prev_sha if prev_sha and rng.random() < 0.85 else "f" * 64)
            ),
            salida=salida,
            conserva=conserva,
            rc=rc,
        )
        ruta = base / f"recibo{i + 1}.json"
        ruta.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
        docs.append(doc)
        rutas.append(ruta)
        prev_img = imagen
        prev_sha = salida.get("sha256_archivo")  # type: ignore[assignment]

    return rutas, docs


def _medir(rutas: list[Path], docs: list[dict], base: Path) -> tuple[int, int, int, int, str]:
    proceso = subprocess.run(
        ["sh", str(RAIZ / "verify.sh"), "-d", str(base), *map(str, rutas)],
        capture_output=True, text=True,
    )
    match = COBERTURA.search(proceso.stdout)
    assert match, f"verify.sh no publico COBERTURA:\n{proceso.stdout}{proceso.stderr}"
    nivel2, n = (int(g) for g in match.groups())
    compuesta = cadena([desde_acta(d) for d in docs])
    return proceso.returncode, compuesta.rc, nivel2, n, proceso.stdout


def _cadena_limpia(base: Path, claves: int = 3) -> list[dict]:
    """Two acts that a certificate would call perfect, so a mutation is the only defect."""
    base.mkdir(parents=True, exist_ok=True)
    docs = []
    prev = "0" * 64
    for i in (1, 2):
        nombre = f"limpio{i}.csv"
        cuerpo = ("clave\n" + "".join(f"K{i}-{j}\n" for j in range(claves))).encode()
        (base / nombre).write_bytes(cuerpo)
        doc = _documento(
            caso=nombre, dominio=claves, cubetas={"imagen": claves, "sin_clave": 0},
            entrada_sha=prev, conserva=True, rc=0,
            salida={"archivo": nombre, "claves": claves, "sha256": _sha(cuerpo),
                    "sha256_archivo": _sha(cuerpo)},
        )
        docs.append(doc)
        prev = _sha(cuerpo)
    return docs


def _fusionar(docs: list[dict]) -> None:
    """A unit is merged into another and the receipt never says so: the bucket name is the evidence."""
    for clave in ("cubetas", "ecuacion"):
        docs[1][clave]["imagen"] -= 1
        docs[1][clave]["colisiones"] = 1


def _a_ceros(docs: list[dict]) -> None:
    """Both acts measure nothing, so every count closes and no unit was conserved either."""
    for doc in docs:
        doc["dominio"] = 0
        doc["cubetas"] = {"imagen": 0, "sin_clave": 0}
        doc["ecuacion"] = {"dominio": 0, "imagen": 0, "sin_clave": 0}


AGUJEROS = {
    # el acto se contradice: ninguna de las dos implementaciones debe firmarlo
    "conserva_false": (lambda b: _cadena_limpia(b), lambda d: d[1].__setitem__("conserva", False)),
    "rc_dos_sobre_cerrada": (lambda b: _cadena_limpia(b), lambda d: d[1].__setitem__("rc", 2)),
    "dominio_vacio": (lambda b: _cadena_limpia(b, claves=0), _a_ceros),
    "colision_sin_declarar": (lambda b: _cadena_limpia(b), _fusionar),
    "sin_archivo": (lambda b: _cadena_limpia(b), lambda d: d[1]["salida"].pop("archivo")),
}


@pytest.mark.parametrize("agujero", sorted(AGUJEROS))
def test_un_agujero_conocido_no_vuelve_a_firmarse(agujero, tmp_path):
    """The random sample does not have to be lucky: each known hole has its own case."""
    construir, mutar = AGUJEROS[agujero]
    docs = construir(tmp_path)
    mutar(docs)
    rutas = []
    for i, doc in enumerate(docs, 1):
        ruta = tmp_path / f"recibo{i}.json"
        ruta.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
        rutas.append(ruta)

    rc_v, rc_c, nivel2, n, salida = _medir(rutas, docs, tmp_path)
    assert (rc_v == 0) == (rc_c == 0 and nivel2 == n), (
        f"{agujero}: verify.sh={rc_v} chain={rc_c} cobertura={nivel2}/{n}\n{salida}"
    )
    assert rc_v != 0, f"{agujero}: verify.sh firmo un certificado defectuoso\n{salida}"


def test_verify_sh_sale_cero_si_y_solo_si_el_compositor_y_la_cobertura(tmp_path):
    rng = random.Random(SEMILLA)
    vistos = {"limpio": 0, "sin_cobertura": 0, "roto": 0, "contradicho": 0}

    for i in range(CASOS):
        base = tmp_path / f"caso{i:02d}"
        rutas, docs = _un_caso(rng, base)
        rc_v, rc_c, nivel2, n, salida = _medir(rutas, docs, base)

        if (rc_v == 0) != (rc_c == 0 and nivel2 == n):
            pytest.fail(
                f"caso {i} (semilla {SEMILLA}): verify.sh={rc_v} chain={rc_c} "
                f"cobertura={nivel2}/{n}\n{salida}"
            )

        if rc_c == 0 and nivel2 == n:
            vistos["limpio"] += 1
        elif rc_c == 0:
            vistos["sin_cobertura"] += 1
        elif any(d["conserva"] and sum(d["cubetas"].values()) != d["ecuacion"]["dominio"]
                 or not d["conserva"] and sum(d["cubetas"].values()) == d["ecuacion"]["dominio"]
                 or d["rc"] == 2 and sum(d["cubetas"].values()) == d["ecuacion"]["dominio"]
                 for d in docs):
            vistos["contradicho"] += 1
        else:
            vistos["roto"] += 1

    assert vistos["limpio"], f"la muestra no ejercito ninguna cadena limpia: {vistos}"
    assert vistos["sin_cobertura"], f"la muestra no ejercito la ceguera por cobertura: {vistos}"
    assert vistos["roto"], f"la muestra no ejercito ninguna cadena rota: {vistos}"
    assert vistos["contradicho"], f"la muestra no ejercito ningun recibo contradictorio: {vistos}"
