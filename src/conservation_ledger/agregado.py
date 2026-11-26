"""El conjunto como un recibo: la auditoria entera, citable.

``verify`` juzga un area y ``chain`` juzga una costura entre dos; hasta aqui el
conjunto solo existia como la ultima linea de una terminal. Ese veredicto no
tenia documento, asi que no se podia entregar, ni anclar, ni volver a leer.

Tres medidas independientes lo cierran. Las dos primeras son las de siempre: el
**recuento** de areas y el **digest** de una proyeccion canonica de cada una; ni
la una ni la otra dependen del orden en que llegaron los recibos -- el conjunto
es un conjunto -- pero las dos se mueven si un area desaparece, si se cuela una
que no estaba o si cambia de clase. Un agregado que solo contara areas se
padearia con un area repetida; uno que solo guardara el digest no diria cuantas
son.

La tercera es la **procedencia**, y no es del mismo tipo que las otras dos: las
areas dicen *que* se midio, la procedencia dice *de donde salio*. Se publica como
una fila por documento de entrada -- nombre, sha256 de sus bytes y cuantos
recibos aporta -- ordenada y digerida aparte. Su identidad de cierre es
``n_areas == suma de aportes``: un agregado cuyas fuentes no suman las areas que
declara esta describiendo un conjunto que nadie produjo. Un certificado que no
puede nombrar sus fuentes no es certificable, y por eso la procedencia vacia es
un defecto, no una omision inocente.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from .adaptadores import adaptar, detectar
from .esquema import Recibo
from .verificador import Veredicto, rc_del_acto, verificar

ESQUEMA = "conservation/agregado/1"

#: Campos de una fila del conjunto, en el orden en que se proyectan.
CAMPOS = ("area", "instrumento", "version", "clase", "rc", "dominio", "residuo",
          "digest_entrada")

#: Campos de una fila de procedencia, en el orden en que se proyectan.
CAMPOS_FUENTE = ("documento", "sha256", "n_recibos")


def _fila(r: Recibo, v: Veredicto) -> dict:
    return {
        "area": v.area,
        "instrumento": v.instrumento,
        "version": v.version,
        "clase": v.clase,
        "rc": v.rc,
        "dominio": v.dominio,
        "residuo": v.residuo,
        "digest_entrada": r.digest_entrada,
    }


def _clave(fila: dict) -> list[str]:
    return [str(fila.get(c) or "") for c in CAMPOS]


def proyeccion(filas: Sequence[dict]) -> str:
    """Una linea por area, tabulada y ordenada: lo que un tercero puede rehacer.

    ``@tsv`` de jq y ``sort`` con ``LC_ALL=C`` producen exactamente estas lineas,
    asi que el digest se comprueba sin instalar este paquete.
    """
    lineas = []
    for fila in sorted(filas, key=_clave):
        lineas.append("\t".join(
            "" if fila.get(c) is None else str(fila.get(c)) for c in CAMPOS))
    return "\n".join(lineas) + "\n" if lineas else ""


def digest(filas: Sequence[dict]) -> str:
    return hashlib.sha256(proyeccion(filas).encode("utf-8")).hexdigest()


def leer_fuentes(
    rutas: Iterable[Path], adaptador: str | None = None
) -> tuple[list[Recibo], list[dict]]:
    """Lee los documentos de entrada y anota, por documento, sus bytes y su aporte.

    El sha256 es de los **bytes del fichero**, no de su sentido: es la unica de
    las tres medidas que un tercero comprueba con ``shasum`` sin leer el JSON.
    Reformatear una fuente es, por tanto, producir otro artefacto.
    """
    recibos: list[Recibo] = []
    fuentes: list[dict] = []
    for ruta in rutas:
        ruta = Path(ruta)
        doc = json.loads(ruta.read_text(encoding="utf-8"))
        suyos = adaptar(adaptador or detectar(doc), doc)
        recibos.extend(suyos)
        fuentes.append({
            "documento": ruta.name,
            "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(),
            "n_recibos": len(suyos),
        })
    return recibos, fuentes


def proyeccion_fuentes(fuentes: Sequence[dict]) -> str:
    lineas = []
    for fila in sorted(fuentes, key=lambda f: str(f.get("documento") or "")):
        lineas.append("\t".join(
            "" if fila.get(c) is None else str(fila.get(c)) for c in CAMPOS_FUENTE))
    return "\n".join(lineas) + "\n" if lineas else ""


def digest_procedencia(fuentes: Sequence[dict]) -> str:
    return hashlib.sha256(proyeccion_fuentes(fuentes).encode("utf-8")).hexdigest()


def _cuenta(veredictos: Iterable[Veredicto]) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for v in veredictos:
        cuenta[v.clase] = cuenta.get(v.clase, 0) + 1
    return dict(sorted(cuenta.items()))


def agregar(pares: Iterable[tuple[Recibo, Veredicto]],
            fuentes: Sequence[dict]) -> dict:
    """Construye el certificado. ``fuentes`` no tiene valor por defecto a proposito.

    Un agregado se puede escribir sin nombrar de donde salio; lo que no se puede
    es verificarlo despues. Al exigir la lista en la firma, el olvido es un error
    de tipo y no un campo ausente que alguien rellenara a mano.
    """
    lista = list(pares)
    prov = sorted((dict(f) for f in fuentes), key=lambda f: str(f["documento"]))
    aportes = sum(int(f["n_recibos"]) for f in prov)
    if aportes != len(lista):
        raise ValueError(f"las fuentes aportan {aportes} recibos y el conjunto "
                         f"declara {len(lista)}: la procedencia no cierra")
    filas = sorted((_fila(r, v) for r, v in lista), key=_clave)
    veredictos = [v for _, v in lista]
    return {
        "schema": ESQUEMA,
        "n_areas": len(filas),
        # Un solo booleano colapsaria "no habia nada que medir" con "se rompio",
        # que es justo la distincion que el contrato existe para hacer. El
        # conjunto publica el vector de clases; el veredicto se lee de ahi.
        "cuenta": _cuenta(veredictos),
        "defectuosos": sum(1 for v in veredictos if v.defectuoso),
        "rc": rc_del_acto(veredictos),
        # Suma de poblaciones distintas: es un digito de control del conjunto,
        # no una medida de codigo. Se publica con su nombre para que nadie la
        # lea como "tantos almacenes en el universo".
        "dominio_declarado_suma": sum(v.dominio for v in veredictos),
        "residuo_total": sum(v.residuo for v in veredictos),
        "instrumentos": sorted({f"{v.instrumento} {v.version}" for v in veredictos}),
        "procedencia": prov,
        "digest_procedencia": digest_procedencia(prov),
        "areas": filas,
        "digest_conjunto": digest(filas),
    }


def _comprobar_filas(doc: dict) -> list[str]:
    filas = doc.get("areas") or []
    if not isinstance(filas, list):
        return ["'areas' debe ser una lista"]
    motivos: list[str] = []
    if len(filas) != doc.get("n_areas"):
        motivos.append(f"declara {doc.get('n_areas')} areas, lleva {len(filas)}")
    if digest(filas) != doc.get("digest_conjunto"):
        motivos.append(f"el digest declarado no es el de sus filas "
                       f"({doc.get('digest_conjunto')})")
    cuenta: dict[str, int] = {}
    for fila in filas:
        clase = str(fila.get("clase") or "")
        cuenta[clase] = cuenta.get(clase, 0) + 1
    if dict(sorted(cuenta.items())) != doc.get("cuenta"):
        motivos.append(f"el vector de clases declarado no es {dict(sorted(cuenta.items()))}")
    suma = sum(int(f.get("dominio") or 0) for f in filas)
    if suma != doc.get("dominio_declarado_suma"):
        motivos.append(f"la suma declarada no es {suma}")
    if sum(int(f.get("residuo") or 0) for f in filas) != doc.get("residuo_total"):
        motivos.append("el residuo declarado no es la suma de los residuos")
    return motivos


def _comprobar_procedencia(doc: dict) -> list[str]:
    prov = doc.get("procedencia")
    if not isinstance(prov, list) or not prov:
        return ["no declara procedencia: un certificado que no puede nombrar "
                "sus fuentes no es certificable"]
    if digest_procedencia(prov) != doc.get("digest_procedencia"):
        return [f"el digest de procedencia declarado no es el de sus fuentes "
                f"({doc.get('digest_procedencia')})"]
    aportes = sum(int(f.get("n_recibos") or 0) for f in prov)
    if aportes != doc.get("n_areas"):
        return [f"las fuentes aportan {aportes} recibos y el conjunto declara "
                f"{doc.get('n_areas')} areas"]
    return []


def _comprobar_contra_fuentes(doc: dict, base) -> list[str]:
    """Re-corre el acto desde los documentos: bytes, y despues el certificado entero."""
    prov = doc.get("procedencia") or []
    motivos: list[str] = []
    rutas = []
    for fuente in prov:
        ruta = Path(base) / str(fuente.get("documento") or "")
        if not ruta.is_file():
            motivos.append(f"falta la fuente {ruta}")
            continue
        real = hashlib.sha256(ruta.read_bytes()).hexdigest()
        if real != fuente.get("sha256"):
            motivos.append(f"{ruta.name}: los bytes no son los declarados "
                           f"(mide {real[:12]}, declara {str(fuente.get('sha256'))[:12]})")
        rutas.append(ruta)
    if motivos:
        return motivos
    recibos, fuentes = leer_fuentes(rutas)
    esperado = agregar([(r, verificar(r)) for r in recibos], fuentes)
    if esperado["digest_conjunto"] != doc.get("digest_conjunto"):
        motivos.append("las areas declaradas no son la funcion de sus fuentes")
    if esperado["digest_procedencia"] != doc.get("digest_procedencia"):
        motivos.append("la procedencia declarada no es la de las fuentes releidas")
    return motivos


def comprobar(doc: dict, base=None) -> tuple[int, tuple[str, ...]]:
    """Re-deriva el conjunto desde sus propias filas. RC 0 = cuadra.

    Sin ``base`` el certificado se juzga a si mismo: es lo que necesita un
    cliente que recibio el JSON y nada mas. Con ``base`` se re-corre el acto
    desde los documentos de origen, que es lo que necesita quien lo emite.
    """
    if doc.get("schema") != ESQUEMA:
        return 1, (f"schema {doc.get('schema')!r} no es {ESQUEMA}",)
    motivos = _comprobar_filas(doc) + _comprobar_procedencia(doc)
    if not motivos and base is not None:
        motivos = _comprobar_contra_fuentes(doc, base)
    return (0 if not motivos else 1), tuple(motivos)


def leer(ruta) -> dict:
    from pathlib import Path

    return json.loads(Path(ruta).read_text(encoding="utf-8"))
