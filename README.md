# conservation-ledger

**One verifier for every conservation receipt, blind to which instrument wrote it.**

Two auditors in this suite already measure the same law in two dialects:

```
ingest-conservation-guard   dominio == imagen + colisiones_por_proyeccion
                                     + colisiones_por_repetido + rechazos + sin_clave
fiber-ast-lint              almacenes == pierde + guardadas + acumulacion
                                       + posicional + sin_len
```

Both close with residual 0. The units differ — rows and projections in one,
stores and loops in the other — but the *shape* is the same: a declared total
equals the sum of the accounted destinations, and the residual is what leaked.

`conservation-ledger` reads receipts from either instrument, **recomputes the
equation from the published terms**, and refuses to take the producer's word
for it.

## The defect it closes

A receipt that states its own verdict grades itself.

`ingest-conservation-guard` computes `perdidas_silenciosas` and `conserva`
inside `acta.py` — the module that also measured the numbers. `fiber-ast-lint`
publishes `censo.json` with `"reconciles": true` and **not one of the terms**
that make it true. In both cases the entity being certified is the same entity
holding the pen.

So this ledger keeps the only two fields it can check:

| field | trust |
|---|---|
| `dominio` | declared — the size of the input population |
| `cubetas` | declared — how many units each destination accounts for |
| `declarado.conserva` | **ignored as evidence** — only used to flag `DISCREPANCIA` |
| `declarado.rc` | **ignored as evidence** — only used to flag `DISCREPANCIA` |

Everything else is arithmetic. `dominio - sum(cubetas) != 0` is a `RUPTURA`,
regardless of what the receipt claims about itself.

## Quickstart

```bash
pip install -e .
conservation-ledger verify receipts/*.json      # recompute every equation
conservation-ledger panel  receipts/*.json -o panel.html
conservation-ledger collect manifest.json -o receipts/
conservation-ledger chain  receipts/paso1.json receipts/paso2.json   # the seam
```

Exit code is the **recomputed** severity of the act, never the declared one.

## Receipts measured today

Sixteen receipts, sixteen recomputed equations: `CONSERVADO 12 · COLISION 2 · VACIO 2`, and **no
row refused for lack of terms** — which was thirteen rows out of sixteen before the census in the
sibling repo learned to publish them.

<!-- ledger-table:begin -->
| Área | Instrumento | Firma | Ecuación | Residuo | Declara | Recomputa |
|---|---|---|---|---:|---|---|
| `acta:migracion.csv` | ingest-conservation-guard | 0.4.2 | `6 = colisiones_por_proyeccion 2 + colisiones_por_repetido 1 + imagen 3 + rechazos 0 + sin_clave 0  (residuo 0)` | 0 | `conserva=true rc=1` | **COLISION** |
| `acta:pacientes` | ingest-conservation-guard | 0.4.2 | `8 = colisiones 2 + imagen 4 + rechazos 2 + sin_clave 0  (residuo 0)` | 0 | `conserva=true rc=1` | **COLISION** |
| `censo:astroid@4.3.4#.` | fiber-ast-lint | 0.4.4 | `37 = pierde 0 + guardadas 10 + acumulacion 0 + posicional 1 + sin_len 26  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:black@26.10.1#.` | fiber-ast-lint | 0.4.4 | `23 = pierde 2 + guardadas 1 + acumulacion 0 + posicional 1 + sin_len 19  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:dill@0.4.1#.` | fiber-ast-lint | 0.4.4 | `16 = pierde 4 + guardadas 1 + acumulacion 1 + posicional 1 + sin_len 9  (residuo 0)` | 0 | `conserva=true rc=0` | **CONSERVADO** |
| `censo:flake8@7.5.0#.` | fiber-ast-lint | 0.4.4 | `3 = pierde 0 + guardadas 0 + acumulacion 0 + posicional 0 + sin_len 3  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:isort@9.0.2#.` | fiber-ast-lint | 0.4.4 | `21 = pierde 0 + guardadas 2 + acumulacion 2 + posicional 3 + sin_len 14  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:jsonschema@4.26.0#.` | fiber-ast-lint | 0.4.4 | `2 = pierde 0 + guardadas 2 + acumulacion 0 + posicional 0 + sin_len 0  (residuo 0)` | 0 | `conserva=true rc=0` | **CONSERVADO** |
| `censo:mypy@2.4.1` | fiber-ast-lint | 0.4.4 | `173 = pierde 4 + guardadas 25 + acumulacion 7 + posicional 12 + sin_len 125  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:mypy@2.4.1#.` | fiber-ast-lint | 0.4.4 | `226 = pierde 4 + guardadas 34 + acumulacion 9 + posicional 16 + sin_len 163  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:platformdirs@4.14.8#.` | fiber-ast-lint | 0.4.4 | `0 = pierde 0 + guardadas 0 + acumulacion 0 + posicional 0 + sin_len 0  (residuo 0)` | 0 | `conserva=true rc=0` | **VACIO** |
| `censo:pydantic@2.14.4#.` | fiber-ast-lint | 0.4.4 | `143 = pierde 0 + guardadas 17 + acumulacion 6 + posicional 2 + sin_len 118  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:pyflakes@4.1.0#.` | fiber-ast-lint | 0.4.4 | `0 = pierde 0 + guardadas 0 + acumulacion 0 + posicional 0 + sin_len 0  (residuo 0)` | 0 | `conserva=true rc=0` | **VACIO** |
| `censo:pylint@4.1.4#.` | fiber-ast-lint | 0.4.4 | `55 = pierde 1 + guardadas 14 + acumulacion 4 + posicional 4 + sin_len 32  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `censo:tomlkit@0.15.3#.` | fiber-ast-lint | 0.4.4 | `6 = pierde 0 + guardadas 2 + acumulacion 1 + posicional 0 + sin_len 3  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
| `fiber:fixtures` | fiber-ast-lint | 0.4.4 | `9 = pierde 0 + guardadas 2 + acumulacion 1 + posicional 1 + sin_len 5  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
<!-- ledger-table:end -->

Read the two blocks separately.

**`CONSERVADO` and `COLISION` mean the equation closed.** `COLISION` is not a
failure of arithmetic — the merged units are accounted for in a named bucket, so
no unit vanished. It is a warning that a projection dropped information, and the
instrument said so itself.

**`VACIO` is the interesting column.** Two rows — `platformdirs` and
`pyflakes` — close over a domain of zero. The equation holds and proves
nothing: no store was measured, so no store can be shown accounted for.

### What this table looked like before the census published its terms

The first version of this ledger read `fiber-ast-lint`'s `censo.json` as it was
shipped in `v0.4.2`: thirteen rows, each declaring `"reconciles": true` and
publishing `stores` and `pierde` — and **not one of the four buckets**
(`guardadas`, `acumulacion`, `posicional`, `sin_len`) that make the sum close.
The honest verdict was `NO_VERIFICABLE` on all thirteen, and the ledger printed
`CONSERVADO 2 · COLISION 1 · NO_VERIFICABLE 13 · RC 1`.

The fix belonged to the producer, not here. `fiber-ast-lint v0.4.3` publishes
the buckets in every row, and `desde_censo` hands them over intact; rows written
before that change still yield no buckets and are still refused. The table
above is the same receipts, re-derived: nothing in this repository's verdict
logic changed to make them pass.

Closing the producer also exposed a defect *inside* the producer. The census keyed
its measurements by artifact alone, and the two `mypy` rows share one wheel
(`mypy-2.4.1-py3-none-any.whl`) with two scopes, so the wheel-root measurement
(226 stores) overwrote the package-scoped one (173) and produced an apparent
rupture that existed only in the producing script. Keyed by `(artifact, scope)`,
both rows reconcile. A duplicate label hid a subtraction — the same defect this
ledger exists to name.

### Two findings the ledger surfaced on real data

1. **`censo:mypy@2.4.1` named two subjects.** Two rows carried the same label —
   one measured 195 files scoped to the package, the other 336 files scoped to
   the wheel root. A label that fits two subjects is not an identifier, so
   `desde_censo` appends the scope when it differs from the package name, and
   the duplicate became `censo:mypy@2.4.1` and `censo:mypy@2.4.1#.`.
2. **Three shapes publish the size of the input under three different names.**
   `acta --json` puts `dominio` at the root, `acta --receipt` puts it in
   `entrada.filas`, and the summary publishes `suma`. An adapter that knows only
   one of them silently reads a domain of 0 and reports `RUPTURA` on a receipt
   that closes — measured, then fixed in `_dominio_acta`.
3. **`censo:platformdirs@4.14.8#.` and `censo:pyflakes@4.1.0#.` measure zero.**
   A zero domain is `VACIO`, not `CONSERVADO`: an equation over an empty
   population closes trivially and proves nothing about the instrument.
4. **A closed equation can still declare a loss.** Eleven census rows declare
   `rc=1` — the producer's code for "stores whose consumer was not found" — while
   their terms show `pierde` and nothing else missing. The ledger reports
   `CONSERVADO` and prints the disagreement as a non-fatal motivo: the arithmetic
   closed, and the producer's severity is a judgement this ledger cannot
   recompute from the terms alone.

5. **A stored receipt had aged and nothing could say so.** `receipts/acta-migracion.json`
   declared `imagen 4` with no repeat collisions and an output digest of
   `6e59cdf4…`; the instrument in the repository produced `imagen 3` and
   `colisiones_por_repetido 1` with an output digest of `8255a43e…`. The file was
   written by an older `ingest-conservation-guard` whose collision attribution
   changed, and the adapter recorded `version=None` because the acta document
   published no version at all — so neither a reader nor a test could tell an
   aged receipt from a tampered one. Both producers now stamp
   `instrument`/`instrument_version` (ingest `0.4.2`, fiber `0.4.4`) and the
   panel prints the firma in its own column. The stored receipts were
   regenerated with the instruments that reproduce them; the values moved,
   which is the point: the aging was invisible until the receipt said who
   wrote it.

## Contract `conservation/1`

```json
{
  "schema": "conservation/1",
  "area": "acta:migracion.csv",
  "instrumento": "ingest-conservation-guard",
  "version": "0.4.2",
  "dominio": 6,
  "unidad": "filas",
  "cubetas": {"imagen": 3, "colisiones_por_proyeccion": 2,
             "colisiones_por_repetido": 1, "rechazos": 0, "sin_clave": 0},
  "digests": {"entrada": "d706…5581", "salida": "8255…b9e2"},
  "declarado": {"conserva": true, "rc": 1}
}
```

`unidad` is the population a `dominio` is counted in — `filas` for an acta,
`almacenes` for a store census. Two receipts with different units are never
added: `30 rows + 12 stores` is not 42 of anything, and the panel keeps one
totals row per unit.

`version` is the **firma**: the version of the binary that produced the receipt,
as the binary stamped it on itself. It is `null` when the producer does not
publish one, and the panel prints `SIN_VERSION` rather than guessing — a receipt
that cannot name its author cannot be dated, and an aged receipt looks exactly
like an edited one.

Validation is strict on purpose: negative counts, booleans passed as integers,
non-64-hex digests or a foreign `schema` raise `ReciboInvalido`. A missing
`cubetas` is *accepted* — the verifier then says `NO_VERIFICABLE` instead of
inventing terms nobody published.

### Verdicts

| verdict | when | RC |
|---|---|---:|
| `CONSERVADO` | residual 0, domain > 0, no merge bucket | 0 |
| `COLISION` | residual 0, but a `colisiones*` bucket > 0 | 1 |
| `VACIO` | domain 0 — closes trivially, proves nothing | 2 |
| `NO_VERIFICABLE` | no buckets published | 2 |
| `RUPTURA` | residual != 0 | 4 |
| `DISCREPANCIA` | declared verdict contradicts the closed equation | 4 |

Precedence follows the corpus, not `max()`: an act with a collision and an
unmeasured area reports **1**, because `max(1, 2)` would let "not measured"
hide a real finding. Hence `PRECEDENCIA` in `verificador.py`, and hence the
per-class counts are always printed next to the code.

## Chains: a composition is only as conserved as its seams

Two receipts certify two acts. A pipeline needs the **seam** — the artifact the first act wrote
must be the artifact the second act read — and that is not one fact but two:

| seam | measurement | what it proves | blind to |
|---|---|---|---|
| count | `imagen(i) == dominio(i+1)` | the next act received as many units as this one kept | identity: rewrite a witness and the count still agrees |
| bytes | `digests.artefacto(i) == digests.entrada(i+1)` | the next act read the artifact this one wrote | nothing about the rows |

Measured on two `ingest-conservation-guard` acts over the six-row fixture — three rows kept, three
declared as collisions, nothing silently lost:

```console
$ ledger chain paso1.json paso2.json
SELLADO   acta:migracion.csv -> acta:paso1.csv  filas 3 -> 3  bytes =
COMPUESTO 6 = 3 + 3  residuo=0  telescopia=si  RC=1
```

Sellado, residual 0 — and `RC=1`, because the first act declared a collision. Composition cannot be
better than its worst link, so the pipeline does not launder an act that was already dirty.

Now rewrite one witness inside `paso1.csv`, keeping all three rows, and re-run the second act:

```console
$ ledger chain paso1.json paso2-alterado.json
RUPTURA   acta:migracion.csv -> acta:paso1-alterado.csv  filas 3 -> 3  bytes !
COMPUESTO 6 = 3 + 3  residuo=0  telescopia=si  RC=4
     - acta:migracion.csv -> acta:paso1-alterado.csv: el artefacto no es el que el acto anterior escribio
```

The counts still agree. A checker that only counted would call that pipeline conserved; the digests
say the artifact is not the one the previous act wrote. Both blocks above are recomputable —
`tests/test_readme_cadena.py` runs the verb over the receipts in `tests/fixtures/cadena/`, written
by the producer itself, and compares line by line.

`NO_MEDIDO` does not decay into zero here either: a receipt that published no artifact digest yields
`NO_MEDIDO` with `RC=2`, never a silent pass.

**Telescoping.** With `d(i) = img(i) + resto(i)` and `d(i+1) = img(i)`, induction gives
`d(1) = img(n) + Σ resto(i)`: the composite residual is the sum of the link residuals and no degree
of freedom survives once every seam is sealed. The identity is checked by two independent routes —
the composite and the sum — in `tests/test_cadena.py`, together with the count-blindness falsifier.

**Finding.** A chain of conserving acts is not a conserved pipeline. Verifying each act's own
equation cannot see the seam, because the seam lives in neither act.

## Adapters: the only instrument-aware code

`verificador.py` (162 lines) knows nothing about any instrument. Everything
specific to a dialect lives in `adaptadores.py` — 173 lines:

| adapter | reads | note |
|---|---|---|
| `acta` | `ingest-conservation-guard --receipt` | passes buckets through |
| `fiber` | `fiber-ast-lint --json` | keeps only the basename of the root |
| `censo` | `fiber-ast-lint/censo.json` | buckets only when the row publishes them |
| `raw` | a single `conservation/1` document | for `collect` |

`desde_censo` deliberately refuses to reconstruct terms from `pierde`: doing so
would be manufacturing the evidence that was withheld.

## Collect

`collect` runs each instrument and files its receipt, so the ledger never holds
a hand-made fixture:

```json
{"areas": [
  {"area": "acta:migracion.csv", "adapter": "acta",
    "cwd": "../ingest-conservation-guard",
    "cmd": ["python", "-m", "ingest_conservation_guard", "acta",
            "tests/fixtures/migracion.csv", "--receipt"]}
]}
```

A non-zero instrument exit stops the act — a broken producer must not be
archived as a success.

## Figures do not age alone

`tests/test_readme.py` recomputes the table above from `receipts/` and fails if
`README.md` disagrees by one cell, and fails again if a published area no longer
exists. The block between `ledger-table:begin` and `ledger-table:end` is the only
place the numbers live.

## As a pre-commit hook

```yaml
repos:
  - repo: https://github.com/alexisromtz-lab/conservation-ledger
    rev: v0.2.0
    hooks: [{id: conservation-ledger-verify}]
```

The hook reads `--json`-free output and blocks the commit when a receipt in
`receipts/` does not close, or closes over a merge the instrument did not
declare as benign.

## Limits

- It verifies **arithmetic**, not intent: an instrument that drains the input
  before counting passes with a clean equation.
- It cannot check a receipt whose terms were never published — it can only
  refuse to certify it, which is what `NO_VERIFICABLE` does.
- Severity is inferred from a **bucket-name convention**: a bucket whose name
  starts with `colisiones` raises `COLISION`. A dialect that names its loss
  something else — `fiber-ast-lint` calls it `pierde` — closes as `CONSERVADO`
  and the declared `rc=1` shows up only as a non-fatal motivo. Making that
  comparison honest needs the receipt to declare which buckets are defects,
  which no producer publishes yet.
- It certifies the equation over the population **the instrument declared**. If
  the input was drained before `dominio` was counted, every row still closes.

## License

MIT.
