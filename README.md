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
```

Exit code is the **recomputed** severity of the act, never the declared one.

## Receipts measured today

<!-- ledger-table:begin -->
| Área | Instrumento | Ecuación | Residuo | Declara | Recomputa |
|---|---|---|---:|---|---|
| `acta:migracion.csv` | ingest-conservation-guard | `6 = colisiones_por_proyeccion 2 + colisiones_por_repetido 0 + imagen 4 + rechazos 0 + sin_clave 0  (residuo 0)` | 0 | `conserva=true rc=1` | **COLISION** |
| `acta:pacientes` | ingest-conservation-guard | `8 = colisiones 2 + imagen 4 + rechazos 2 + sin_clave 0  (residuo 0)` | 0 | `conserva=true rc=1` | **COLISION** |
| `censo:astroid@4.3.4#.` | fiber-ast-lint | `37 = ?` | 37 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:black@26.10.1#.` | fiber-ast-lint | `23 = ?` | 23 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:dill@0.4.1#.` | fiber-ast-lint | `16 = ?` | 16 | `conserva=true rc=0` | **NO_VERIFICABLE** |
| `censo:flake8@7.5.0#.` | fiber-ast-lint | `3 = ?` | 3 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:isort@9.0.2#.` | fiber-ast-lint | `21 = ?` | 21 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:jsonschema@4.26.0#.` | fiber-ast-lint | `2 = ?` | 2 | `conserva=true rc=0` | **NO_VERIFICABLE** |
| `censo:mypy@2.4.1` | fiber-ast-lint | `173 = ?` | 173 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:mypy@2.4.1#.` | fiber-ast-lint | `226 = ?` | 226 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:platformdirs@4.14.8#.` | fiber-ast-lint | `0 = ?` | 0 | `conserva=true rc=0` | **NO_VERIFICABLE** |
| `censo:pydantic@2.14.4#.` | fiber-ast-lint | `143 = ?` | 143 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:pyflakes@4.1.0#.` | fiber-ast-lint | `0 = ?` | 0 | `conserva=true rc=0` | **NO_VERIFICABLE** |
| `censo:pylint@4.1.4#.` | fiber-ast-lint | `55 = ?` | 55 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `censo:tomlkit@0.15.3#.` | fiber-ast-lint | `6 = ?` | 6 | `conserva=true rc=1` | **NO_VERIFICABLE** |
| `fiber:fixtures` | fiber-ast-lint | `9 = pierde 0 + guardadas 2 + acumulacion 1 + posicional 1 + sin_len 5  (residuo 0)` | 0 | `conserva=true rc=1` | **CONSERVADO** |
<!-- ledger-table:end -->

Read the two blocks separately.

**`CONSERVADO` and `COLISION` mean the equation closed.** `COLISION` is not a
failure of arithmetic — the merged units are accounted for in a named bucket, so
no unit vanished. It is a warning that a projection dropped information, and the
instrument said so itself.

**`NO_VERIFICABLE` is the interesting column.** Thirteen rows declare
`conserva=true` and publish no terms at all. The ledger does not believe them
and does not call them liars: it calls them *unmeasured*, which is the honest
reading. This is not a defect of the ledger — it is the ledger doing its job on
a corpus that was written before it existed.

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

## Contract `conservation/1`

```json
{
  "schema": "conservation/1",
  "area": "acta:migracion.csv",
  "instrumento": "ingest-conservation-guard",
  "version": "0.4.1",
  "dominio": 6,
  "cubetas": {"imagen": 4, "colisiones_por_proyeccion": 2,
             "colisiones_por_repetido": 0, "rechazos": 0, "sin_clave": 0},
  "digest_entrada": "0000…0000",
  "declarado": {"conserva": true, "rc": 1}
}
```

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

## Adapters: the only instrument-aware code

`verificador.py` (158 lines) knows nothing about any instrument. Everything
specific to a dialect lives in `adaptadores.py` — 6 functions, ~100 lines:

| adapter | reads | note |
|---|---|---|
| `acta` | `ingest-conservation-guard --receipt` | passes buckets through |
| `fiber` | `fiber-ast-lint --json` | keeps only the basename of the root |
| `censo` | `fiber-ast-lint/censo.json` | **yields no buckets on purpose** |
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
    rev: v0.1.0
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
- The census adapter cannot yet verify `fiber-ast-lint`; the fix belongs in that
  repo (publish per-row terms) and is the next act, not a patch here.

## License

MIT.
