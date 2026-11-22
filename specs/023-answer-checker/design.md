# Spec 023 — Answer checker: design

Requirements: `requirements.md` (owner's decisions §§6–13). Revised after the reviews in
`specs/023-review.md`, `specs/023-review-followup.md`, `specs/023-design-proposal.md` and
`specs/023-review-claude.md`, `specs/023-review-reconciliation.md`, `specs/023-review-chatgpt-2.md` (requirements §13), and the textbook check (D11 revised, D12–D16). Builds on specs 005 (pack), 008/009 (board, expression grammar),
011/017/021 (course languages), 018 (stored tool entries), 020 (révision record). The
implementation branch must start from a branch that has spec 021's code (German rows): every
per-language table below has an `fr`, `en`, `nl` and `de` row.

## 1. Overview

**Review in progress:** The user has accepted the direction of `specs/023-design-proposal.md`.
This revision incorporates it; the remaining implementation contracts in §10 still need review
before planning.

Four pieces, all deterministic, no model call:

1. **Keys in the pack.** Each typical exercise (pack §6) whose material gives a solution carries
   one key line per answer: `**Schlüssel:** number 374`, optionally with the task the code can
   compute: `**Schlüssel a):** set {2; 3} | solve x^2 - 5x + 6 = 0`. `index_pack` validates keys
   with the readers that read student answers; a key with a task is recomputed once per content
   version and marked `agrees` or `needs_review`.
2. **`app/domain/answers/`**: readers per kind and course language, exact arithmetic
   (`Fraction`), a unit table with exact factors, an exact algebra for polynomials and rational
   expressions, the comparison, and variant keys computed by code.
3. **Bound exercises.** An `exercise` or `check_question` card on `display_board` may carry
   `check` (a pack reference or a variant task). The server validates it, shows what is checked
   (the pack's statement verbatim, or the task as the code reads it), and gives the card an
   `exercise_id`. Checking always goes through that id.
4. **Direct checking:** the server checks a learner-confirmed submission against its stored
   presentation and atomically records the submission, verdict and transcript entry. The card
   displays the verdict and its basis; the tutor reads committed context on a later turn. In
   révision `exercise_results` remains distinct from self-assessed `revision_results`.

### Design decisions for the owner's review

Kept from the first design:

- **D1. The key never appears in a tool output**, not even after a correct answer or a reveal.
- **D3. Equation classes** include one-variable polynomials of degree 1–4; D12 and D15 add exact
  surds, rational equations and pure powers. Verdicts require established completeness and
  unambiguous rounding (§9); the verification method remains for design review.
- **D4. One variable** per expression, relation or task.

Superseded: **D2** (« `check_question` unchanged ») → requirements §7.6, implemented by D9.

New, from the review decisions:

- **D5. Binding through the board.** `ExerciseCard` and `CheckQuestionCard` gain an optional
  `check`. For a pack reference, the server **replaces the card's statement with the pack's
  statement of that exercise** (the block under its heading, cut before its answer and key lines);
  if it cannot cut it reliably, the card is shown unbound. For a purely mathematical variant the
  server generates the whole checkable task from its checking data, with no contradictory model
  statement. A word problem whose agreement cannot be established remains unbound and is discussed
  without a verdict. The board declarations change.
- **D6. Exercise and submission identity.** The server issues a distinct opaque ID for each
  stored presentation, tied to its owner, course, chapter, section, mode, content version and
  originating transcript. Eligible parcours presentations survive capped rows and section return;
  changed/reset content, wrong owners or modes and replaced revision runs are refused. A signed
  payload or browser-held card alone does not prove it was stored.
- **D7. Recomputing a stored solution** needs the task on the key line, copied from the statement
  by the authoring agent. Agreement gives the basis « material, recomputed »; disagreement marks the
  key `needs_review`: no verdict, a notice on the card and in the pack view, nothing recorded, the
  stored solution untouched. Agreement is evidence, not proof, that the task was copied right: two
  independent lines of the material agree.
- **D8. Expression classes**: polynomials and rational expressions with rational coefficients in
  one variable, compared exactly (`n₁·d₂ = n₂·d₁` as polynomials) only after the relevant domains
  are established to be the same. Different or uncertain domains yield no equivalence verdict;
  original exclusions must survive simplification. The domain proof method needs design review.
  Unsupported expressions are « not reliably checkable ». Sample points are gone.
- **D9. Multiple choice**: `CheckQuestionCard` loses `correct_option_id` and `feedback`. Unbound, a
  pick is sent as today and shows no verdict. Bound (`check.exercise` to a `choice` key), the
  question is the pack's statement and the buttons are the key's option ids; the verdict comes
  from the submission service. Old stored cards replay without a model-derived verdict; the
  cahier does not reveal an unverified option.
- **D10. Révision results per exercise** in a new table `exercise_results`; `revision_results` and
  the section outcome logic of spec 020 are untouched.
- **D11. Rounding rule semantics** (revised after the textbook check, requirements §8.1): a key
  is `exact`, `±t`, `round d` (d may be negative: −1 tens, −2 hundreds) or `approx` (the material
  wrote `≈`, « rund », « ca. », or a concrete governing rule applies; `d` = the marked key's
  own decimals). A vague « Runde sinnvoll » without an unambiguous rule gives no rounding verdict.
  Under `round d` / `approx`: `correct` iff the answer, rounded to `d` (half away from
  zero, exact arithmetic), equals the key and has at least `d` decimals; `precision` iff it has
  fewer decimals and the key rounded to the answer's decimals equals it; else `incorrect`. With
  `±t`: `correct` iff `|a − k| ≤ t`. `exact`: equality only.

New, from the textbook check:

- **D12. Exact surds.** A number value is a `Fraction` or a `Surd` `a + b√c` (a, b rational, c a
  square-free integer ≥ 2), read from `2√2`, `−3 + √2`, `√11`, `(3 + √2) cm`, compared exactly. The
  real roots of a quadratic factor are returned in that form, so most grade 9 quadratics are
  checkable without a rounding rule. Roots that are not of that form (cubic, quartic, `x⁵ = 7`)
  still need a rounding rule.
- **D13. Required unit or form** (`form` on the key): `unit` (the answer's unit must be the key's
  written unit), `fraction`, `reduced` (lowest terms), `mixed`, `decimal`, `scientific`, `power`
  (a single power `aⁿ`). A right value in another unit or form gives `form_differs`. For
  `expression`, a form flag (`vertex`, `factored`, `expanded`) is not checked: a right value gives
  `form_unchecked`, which is shown and never recorded.
- **D14. Statement cut and figures.** The bound statement is the exercise's shared stem plus the
  one sub-item checked (other sub-items left out). An exercise whose pack text carries a figure
  mark (`[Abbildung: …]`, the transcription's mark) or a measuring operator (« Miss ») is not
  bindable: the card is shown unbound with the reason `figure`.
- **D15. More equation classes for tasks**: equations with the variable in a denominator (cleared
  by multiplying by the denominators' product; solutions that zero a denominator are removed, the
  Definitionsbereich) and pure powers `x^n = c` (integer `n ≠ 0`; exact when `c` is an exact n-th
  power or n = ±2 with a surd; otherwise only with a rounding rule).
- **D16. Textbook authoring.** Pack exercise headings carry the material's reference:
  `#### 6.1.2 (S. 128, Nr. 11)`; appendix solutions are joined to their exercise by page, number
  and sub-letter; answer pools are never keys and never copied into a statement; the `mapping` kind
  covers « Ordne zu »; a sub-answer with several quantities gets named key parts.
- **D17. Confirmed submission.** A card's answer field or option submits directly. Chat presents
  the learner's original message and the selected exercise for confirmation or correction (voice:
  a later spec, requirements §12.1). The server checks the confirmed value immediately; the model cannot submit or
  replace it (§3.10–3.11).
- **D18. Proven domains and roots.** Retain original domain guards; use exact rational polynomial
  arithmetic and certified real-root counting and isolation. When completeness, domain equality
  or requested rounding cannot be established within limits, return `undecided` (§3.6–3.7).
- **D19. Review labels.** An explicit material label is stored with the pack exercise, editable by
  the learner and carried to the revision overview; a missing or ambiguous label is not inferred.

## 2. Architecture

```
 material → pack and keys → server-bound exercise → card with answer field
                                     ▲                      │
                              shown in conversation         │ submit answer / choice
                                                            │ chat: confirm first
                                                            ▼
                                    server resolves presentation and checks immediately
                                                            │
                            atomic submission + transcript + verdict → card and replay
                                                            │
                             révision → per-exercise result; tutor reads it next turn
```

Layering: `domain/answers/` imports only `domain/` (`expression.py`, `language.py`,
`notation.py`, `pack.py` types). `services/tools/bind.py` and `check.py` are services. Nothing
imports `openai`.

## 3. Components and interfaces

### 3.1 `app/domain/notation.py` (moved, behaviour unchanged)

The number, interval and coordinate readers move out of `services/tools/figures.py` so `domain/`
can use them: `NUMBER`, `_decimal_comma`, `_thousands_comma`, `_german_number`, `INTERVAL`,
`COORDS` and their per-language patterns. `figures.py` and `plots.py` import them from here.
`notation_cases.json` (both copies) and every rule test stay green unchanged: a pure move.

### 3.2 `app/domain/answers/kinds.py`

```python
Kind = Literal["choice", "number", "expression", "interval", "set", "point", "word", "mapping"]

@dataclass(frozen=True) class Surd:        a: Fraction; b: Fraction; c: int   # a + b√c, c square-free ≥ 2
@dataclass(frozen=True) class PiLinear:    a: Fraction; b: Fraction           # a + bπ
Exact = Fraction | Surd | PiLinear        # zero radical/π coefficient normalises to Fraction
@dataclass(frozen=True) class Unit:        dimension: str; factor: Fraction; symbol: str
@dataclass(frozen=True) class Rule:        mode: Literal["exact", "tolerance", "round", "approx"] = "exact"
                                           tolerance: Fraction | None = None; round: int | None = None  # D11
Form = Literal["unit", "fraction", "reduced", "mixed", "decimal", "scientific", "power",
               "vertex", "factored", "expanded"]                                       # D13
@dataclass(frozen=True) class Quantity:    value: Exact; decimals: int; unit: Unit | None
                                           written: str   # the form it was written in (for D13)
@dataclass(frozen=True) class Bound:       value: Exact | None; closed: bool   # None = ±∞, never closed
@dataclass(frozen=True) class Interval:    low: Bound; high: Bound

@dataclass(frozen=True) class ChoiceKey:     option: str; options: tuple[str, ...]
@dataclass(frozen=True) class NumberKey:     quantity: Quantity; rule: Rule; form: Form | None
                                             remainder: Fraction | None = None   # « 4 Rest 7 »
@dataclass(frozen=True) class ExpressionKey: function: RationalFunction; variable: str; form: Form | None
@dataclass(frozen=True) class IntervalKey:   union: tuple[Interval, ...]; rule: Rule
@dataclass(frozen=True) class SetKey:        values: tuple[Exact, ...] | Literal["reals"]; rule: Rule
@dataclass(frozen=True) class PointKey:      coords: tuple[Exact, ...]; rule: Rule
@dataclass(frozen=True) class WordKey:       words: tuple[str, ...]; accents: bool
@dataclass(frozen=True) class MappingKey:    pairs: frozenset[tuple[str, str]]
Key = ChoiceKey | NumberKey | ExpressionKey | IntervalKey | SetKey | PointKey | WordKey | MappingKey

Basis = Literal["material", "computed", "both"]
Verdict = Literal["correct", "incorrect", "unreadable", "precision", "unit_differs",
                  "form_differs", "form_unchecked", "undecided"]   # undecided = not reliably checkable
@dataclass(frozen=True) class Checked:
    verdict: Verdict; kind: Kind; basis: Basis
    expected: str | None   # `unreadable`: an example of the expected form, course notation
    reason: str | None     # `undecided`: a reason code (`expression_class`, …)
```

Recorded verdicts (révision, spec 022): `correct`, `incorrect`, `precision`, `unit_differs`,
`form_differs`. `unreadable`, `form_unchecked` and `undecided` are never recorded.

### 3.3 `app/domain/answers/readers.py`

One reader per kind, per course language (`by_language` tables). The same reader parses a key and
a student's answer. Each returns a value or `None` (unreadable). Finite decimals become exact
`Fraction`s with their written decimals (`12,50` → 25/2, decimals 2); supported radical and π
forms retain their symbolic exact values.

| Kind | Accepts (de shown; fr/nl like de with `;`, en with `,` and `.`) | Notes |
| --- | --- | --- |
| number | `374`, `12,5`, `12.500`, `10 000`, `3/4`, `2 1/4`, `0,1̄` / `0,\overline{1}`, `−2`, `12,5 %`, `25 m/s`, `x = 3`, `2√2`, `(3 + √2) cm`, `2π`, `3 + 2π`, `1,15 · 10⁴` / `1,15 · 10^4`, `4 Rest 7`, « nicht definiert » | `NUMBER[lang]`; space grouping only for groups of exactly three digits, so `2 1/4` is a mixed number; trailing unit via `units.py`; leading `<name> =` stripped; the written form kept for D13 |
| expression | `2(x+1)`, `2x+2`, `f(x) = x^2`, `x+1 für x ≠ 1`, `x+1; D = ℝ \ {1}` | exact parse and `algebra.py`; optional supported domain restriction is intersected with the expression's intrinsic domain; unsupported or ambiguous restrictions → `undecided`, never silently stripped |
| interval | `]2; 5]`, `[3; 4]`, `]−∞; 3[ ∪ ]4; +∞[`, `x > 2` (one-sided only), `L = ]2; 5]` | `[−∞ …` refused (∞ never closed); `∞`, `inf`, `unendlich` |
| set | `{−1; 3}`, `L = {−1; 3}`, `L = {1 − √7; 1 + √7}`, `x = −1 oder x = 3`, `x₁ = −1; x₂ = 3`, `x₁ = −1,5, x₂ = 0,5` (anchored on the indexed names), `x = ±3`, `{}` / `∅` / `L = { }`, « keine Lösung », `L = ℝ` | `SET_SEPARATOR[lang]`, `JOINERS[lang]` (de `oder`/`und`; fr `ou`/`et`; nl `of`/`en`; en `or`/`and`), `NO_SOLUTION[lang]` |
| point | `P(2 \| −1,5)`, `(2 \| −1,5)`, `(2; −1,5)` (de); `(2, −1.5)` (en) | `COORDS[lang]` plus a value reader; leading name stripped |
| word | any text | NFKC, casefold, collapse spaces; accents stripped unless the key says `accents` |
| choice | `B`, `b)`, `Antwort B`, `(b)`, `richtig` / `falsch` | one option id among the key's `options`, case-insensitive; `TRUE_FALSE[lang]` words for a richtig/falsch item (a reason after it is ignored) |
| mapping | `A–2, B–1`, `A2 B1`, `A → 2; B → 1` | pairs of ids, any order |

Domain annotations accept the course-language equivalents of `für x ≠ 1` and `D = ℝ \ {1}`,
with finite exclusions parsed exactly and localized wording. The stated restriction intersects,
never expands, the original expression's intrinsic domain; other annotations are `undecided`.
For example, `x+1 für x≠1` can match `(x²−1)/(x−1)`; without the restriction their different
domains give no verdict.

Normalisation before every reader: NFKC (`ℓ` → `l`), `−`/`–` → `-`, `·`/`×`/`:`/`÷` kept for
expressions, surrounding `$…$` stripped (`text.MATH`), trailing `.` stripped. A leading `≈`, `~`,
« rund », « ca. », « etwa » (`APPROX_WORDS[lang]`) is stripped and noted; it changes nothing under
an `exact` key.

### 3.4 `app/domain/answers/units.py`

`UNITS: dict[str, Unit]`, aliases to `(dimension, exact factor to SI)`:

- length: mm, cm, dm, m, km; mass: mg, g, kg, t; time: s, min, h; speed: m/s, km/h (factor 5/18;
  aliases `m·s^-1`, `km·h^-1`); volume: mL/ml, cL/cl, dL/dl, L/l, cm³, dm³, m³ (`cm^3`); area: mm²,
  cm², dm², m², km², a, ha; percent: `%` (dimensionless, factor 1/100); money: €, ct (factor 1/100);
  time adds d (days); temperature: °C (no conversion; equal only to °C).
- Same dimension → the answer is converted **exactly into the key's unit**, then compared under
  the key's rule (a rounding rule applies in the key's unit).
- Different dimension, or a unit outside the table that differs from the key's written unit →
  `unit_differs`. Key with a physical unit, answer without → `unit_differs`; key without a unit,
  answer with a physical one → `unit_differs`.
- `%`: `12,5 %` and `0,125` are equal in either direction.
- A key with `form unit` (D13): the answer's unit must be the key's written unit; the right value
  in another unit of the same dimension is `form_differs`.

### 3.5 `app/domain/answers/check.py`

```python
def check(key: Key, answer: str, language: CourseLanguage, basis: Basis) -> Checked
```

- **number**: read; units (3.4); then the rule (D11); a right value whose unit or written form
  differs from a required `form` is `form_differs` (D13); `remainder` keys compare both parts.
  Surds compare exactly; rounding an approximate value requires a certified unambiguous result
  (§9), otherwise it is not reliably checkable.
- **expression**: both to `RationalFunction` (3.6); either outside the class → `undecided`
  (`expression_class`); then establish equal domains before comparing `n₁·d₂` and `n₂·d₁`.
  Different or uncertain domains → `undecided`; otherwise equal → correct (`form_unchecked`
  when required), unequal → incorrect. Preserve exclusions before cancellation.
- **interval**: unions normalised (sorted, merged); bounds compared under the rule (exact by
  default), closedness equal.
- **set**: same size, pairwise equal under the rule; duplicates in the answer ignored.
- **point**: same dimension, coordinates equal under the rule.
- **word**: normalised answer equals one of `words`.
- **choice**: the id is one of `options` (else unreadable), then equal ids.
- **mapping**: same set of pairs; an answer naming an unknown id is unreadable.

Never raises on student input (fuzz test).

### 3.6 `app/domain/answers/algebra.py`

- A `Polynomial` has rational coefficients. A `RationalFunction` carries its exact numerator and
  denominator **and the domain guards from its original parse tree**. Both operands'
  guards are retained; division and negative powers add nonzero guards. Simplifying the value
  never removes a guard. Unsupported expressions, an identically zero divisor or resource caps
  yield `undecided`.
- The existing plotting parser converts numeric literals to `float`; it cannot be used as the
  source of exact coefficients. Share its grammar and cases, but preserve numeric lexemes and parse
  them directly into `Fraction` in the checker. Plotting behavior and existing pins stay unchanged.
- Compare values by exact polynomial cross multiplication only after proving equal relevant
  domains. The default exercise domain is the reals; an explicit exercise domain is used only
  when its bounds and endpoints are supported exactly. Normalize guard products to square-free
  rational polynomials. Exact gcd plus certified real-root counts establish whether their excluded
  real points are equal within that domain; different polynomials alone do not establish different
  real domains. A failed proof yields `undecided`.
- Use exact polynomial operations and certified real-root counting and rational isolation (for
  example Sturm sequences), with explicit limits, to establish all distinct real roots. Preserve
  multiplicities for inequality signs. Rational roots and supported quadratic surds are exact;
  other roots use isolating intervals and are only turned into rounded keys when refinement proves
  the required rounding unambiguous. Do not use floating-point guesses or a sign change as proof.
- For rounding a uniquely isolated algebraic root, refine its rational interval away from the
  rounding boundary. If the boundary lies in that interval and exact substitution shows it is a
  root, handle that exact boundary with the specified tie rule. Resource exhaustion is undecided.
- Pythagorean surds are compared exactly as supported `Surd`s. For circle calculations support
  bounded `a + bπ` forms with rational coefficients, including `πr²` for rational `r`; compare
  symbolic coefficients exactly, and round only when certified rational upper and lower bounds
  on π imply the same result. Other functions and forms remain `NotCheckable`, not guessed. The
  bounds and supported operations require proof and bounded tests before planning.
- Propagate original denominator exclusions when solving rational equations. A root is removed only
  when exclusion can be established exactly. For inequalities, determine each interval's sign and
  endpoint inclusion from the original relation and domain. An unresolved boundary, repeated or
  close root, uncertain rounding, unsupported operation or exhausted limit returns `NotCheckable`.
- Degree, coefficient size, isolation work and timeout caps must be specified and verified before
  implementation; exceeding them is never an incorrect verdict. Constants and the zero polynomial,
  the empty set and all-real solutions have explicit cases. The exact isolation interface, bounded
  behavior and equality of algebraic roots remain design-review items (§10).

### 3.7 `app/domain/answers/variants.py`: tasks

One form for a pack key's task and for a variant:

```python
@dataclass(frozen=True) class Evaluate: expression: str; variable: str; at: str      # `at` in course notation
@dataclass(frozen=True) class Solve:    relation: str; variable: str                 # one of = < > ≤ ≥ (<=, >=)
Task = Evaluate | Solve

def task_key(task: Task, kind: Kind, rule: Rule, language) -> Key | NotCheckable
def task_text(task: Task, rule: Rule, language) -> str    # the line the card shows (3.9)
```

- `Evaluate`: supported rational expression and exact `at` → `NumberKey` exact. Outside that
  class, a rounded key is allowed only with a stated `round d` and a certified interval proving
  the rounding. A float and a fixed distance threshold do not provide that certificate. Otherwise
  → `NotCheckable("boundary")` or the appropriate unsupported reason.
  Division by zero → `NotCheckable("undefined")`.
- `Solve`: split on the single top-level relational operator; `left − right` as a
  guarded rational value `n/d`, retaining all original domain guards (§3.6):
  - `d` constant: a polynomial of degree 1–4 (D3), `real_roots(n)`;
  - `d` not constant (D15): `=` only: `real_roots(n)` minus roots excluded by any original guard;
    inequalities with the variable in a denominator → `NotCheckable("degree")`;
  - pure power `x^n = c` (D15): exact roots when `c` is an exact n-th power, or `n = ±2` (surds);
    otherwise approximate roots.
  - `=`: `SetKey(roots)`; `kind == "number"` only with exactly one real root.
  - `<`, `>`, `≤`, `≥`: `IntervalKey` from the sign of the polynomial on each piece (tested exactly
    at a rational point inside the piece).
  - Any non-exact root (or bound) requires `round d` and a certified unambiguous rounding;
    otherwise `NotCheckable`. Surd roots need no rule.
- Reasons: `not_polynomial`, `degree`, `variables`, `parse`, `kind_mismatch`,
  `no_unique_number`, `irrational`, `boundary`, `undefined`, `size`.

### 3.8 Keys in the pack: `app/domain/answers/keys.py`

Line form, under an exercise's `#### N.M.K` heading, after its answer line:

```
**<KEY_LABEL>[ <sub>]:** <kind> <key in the course's notation>[ <rule>][ | <task>]
```

- `KEY_LABEL = by_language(fr="Clé", en="Key", nl="Sleutel", de="Schlüssel")`.
- `<sub>`: a sub-question label, `a)`, `b)`, `1)`, …; absent for a single answer.
- `<kind>`: the fixed identifiers of `Kind` (language-neutral; never said aloud). `set` is the
  requirements' `solution_set`.
- `<key>` may start with `≈` (the material marked it rounded): rule `approx` (D11).
- `<rule>`: `round <d>` (d may be negative) or `±<tolerance>` (number, interval, set, point), when
  the exercise or a governing note states it; `form <form>` (D13); word: alternatives separated by
  ` / `, `accents` flag; choice: `of <ids>` lists the exercise's option ids (`of richtig falsch` for
  a true/false item).
- Named parts (D16): `**Schlüssel a) u:** number ≈ 51,05 mm` and `**Schlüssel a) A:** …` give the
  refs `6.1.2 a) u` and `6.1.2 a) A`.
- `<task>`: `solve <relation>` or `eval <expression> at <variable> = <value>`, copied from the
  statement; optional.
- Examples (de): `**Schlüssel:** number 374` · `**Schlüssel:** number 25 m/s` ·
  `**Schlüssel:** number 3,14 round 2` · `**Schlüssel a):** interval ]2; 5]` ·
  `**Schlüssel b):** set {2; 3} | solve x^2 - 5x + 6 = 0` · `**Schlüssel:** point P(2 | −1,5)` ·
  `**Schlüssel:** expression x 2(x+1)` · `**Schlüssel:** word Hypotenuse` ·
  `**Schlüssel:** choice B of A B C D` · `**Schlüssel c):** number ≈ 3,84 cm` ·
  `**Schlüssel:** number 300 dm² form unit` · `**Schlüssel b):** set {−3 + √2; −3 − √2}` ·
  `**Schlüssel:** number 2 1/4 form mixed` · `**Schlüssel:** mapping A–2, B–1, C–3`.

```python
ExerciseRef = str   # "6.1.2" or "6.1.2 a)"
@dataclass(frozen=True) class PackKey:
    key: Key; task: Task | None
    status: Literal["material", "agrees", "needs_review"]
def pack_keys(markdown: str, language) -> tuple[dict[ExerciseRef, PackKey], list[ContentIssue]]
def exercise_statement(markdown: str, ref: ExerciseRef, language) -> str | None
```

- Read in the same walk as `index_pack` (fences skipped, only under the exercises section). Issue
  codes: `pack.key_outside`, `pack.key_duplicate`, `pack.key_kind`, `pack.key_unreadable`,
  `pack.key_task` (malformed task), `pack.key_class` (an expression key outside the class of 3.6)
  (catalog keys in fr/en/nl/de, `render_issue`). A well-formed task that exceeds computation
  limits is not a malformed key and cannot by itself prove a discrepancy.
- With a task: `task_key` computed and compared with the stored key under the key's rule → status
  `agrees` (basis `both`) or `needs_review` (a proven disagreement, no verdict, D7). An
  inconclusive computation is not a proven disagreement and must not claim verification; it
  falls back to `material` only when the key and binding independently satisfy the material-only
  checks. No task → `material`.
- `exercise_statement(…, ref)`: the lines under the exercise's heading up to the first line
  starting with `ANSWER_LABEL[lang]` (the templates' answer label, `**Antwort:**` etc.) or
  `KEY_LABEL[lang]`; for a sub-question ref, the stem (lines before the first sub-item label) plus
  that sub-item's lines only (D14); `None` when the cut is not found, or when the text carries a
  figure mark or a measuring operator (`MEASURE_WORDS[lang]`: « Miss », « miss … nach »).
- `index_pack` calls `pack_keys` and returns its issues; `PackIndex` gains
  `keys: frozenset[ExerciseRef]`.

### 3.9 Presenting and binding an exercise

`ExerciseCard` and `CheckQuestionCard` may carry an optional `check` with exactly one pack
reference or variant task. The server validates the key and cuts the original pack stem and
requested sub-item before answer and key lines. For a pure mathematical variant it generates the
entire checkable statement from the task and checking data. If a cut is unreliable, a figure is
required or a word problem cannot be verified against the data, show it unbound: no answer field
or correctness verdict. A key whose stored and calculated solutions disagree is presented with a
review notice but is not checkable; an inconclusive calculation is not a proven disagreement.

The server assigns each eligible presentation an opaque ID and stores owner, course, chapter,
section, mode, content version, origin and immutable checking reference. Each presentation is a
particular card, not a hash of its task. The browser receives neither key nor authority to bind
arbitrary exercise data. The ID alone is not authorization.

- **Text:** Store presentations with their cards in the existing end-of-turn transcript transaction.
  A streamed card remains visibly pending and its answer control disabled until that write succeeds.
  A failed or cancelled turn creates no orphan eligible presentation. The existing stopped-parcours
  `seance/report` path may retain a partial turn, but only server-validated, stored cards become
  eligible; it cannot accept a forged binding from a client report.
- **Activation (requirements §13.2):** after the store succeeds, the server sends `turn.stored
  {exercise_ids}` (and `message_id`, §3.10); only this event enables an answer field. `turn.end`
  is sent even after a failed store (`api/sse.py`), so it never enables one. A failed store
  sends no `turn.stored`: the cards stay disabled. Reload restores from the stored transcript and
  its eligible presentations. Cards in a stopped turn reported later through `seance/report` are
  stored as reported but never bound.
- **Voice:** a card created in a voice session (`/api/voice/tool`) is shown unbound and a reported
  voice turn never creates a presentation (requirements §12.1, §13.5). The concept for the later
  voice spec is kept in Appendix A.

A parcours presentation stored in the same owner's course, chapter, section and content version can
remain usable across `capped` rows and return to the section; the source row need not remain live.
The student must select or confirm that actual card. A reset or chapter content-version change,
chapter/course/account deletion, ownership mismatch or wrong mode invalidates it. A revision
presentation belongs to its original revision scope and remains eligible only while that logical
run is current and the chapter version is unchanged; replacing or closing a revision invalidates
it. A future revision continuation must explicitly link the logical run and scope, not merely
accept any old presentation. The current implementation returns `RevisionFull`; it does not
provide automatic revision rollover, and this spec does not assume that it does.

### 3.10 Confirming and submitting an answer

A dedicated card field submits the entire answer, and a choice selection submits its option ID.
For chat (stage 023c), the tutor may call `propose_answer(exercise_id)` to open a confirmation,
but cannot submit the answer. The server assigns the turn's learner message a `message_id` when
the turn starts (today `LearnerEntry` has no ID and is stored only with the turn); the proposal
refers to that message, its candidate text is that message's text, never model-authored text or
a model-selected substring, and the confirmation chip is enabled only by the turn's
`turn.stored` (requirements §13.3). A cancelled or unstored turn leaves no proposal. The learner selects the
exercise and confirms or edits the text before submission. The UI makes both value and exercise
visible. If the original message, exercise or intent is ambiguous, ask for clarification; do not
prefill a solution from model prose or the key. Keyboard and screen-reader paths must work. Voice
is out of this spec (requirements §12.1).

`POST /api/answers/submissions` (route name to be finalized against the existing APIs) takes
`{exercise_id, answer, source, request_id}`. An authenticated learner's explicit field submit,
choice, or confirmation constitutes the submission. `source` is `card`, `choice` or `chat`
(`voice` is reserved for the later voice spec and refused with `422` in this one); it is informational and does not replace authorization. The server resolves the
presentation and its eligibility, reads the key server-side, checks the confirmed answer locally,
and commits the submission, result and transcript entry in one transaction. For révision this
transaction also records a recordable per-exercise result and its source. The response contains
`{submission_id, exercise_id, verdict, basis, expected_form?}` but no key, plus the canonical
transcript/event identifier needed for replay. The tutor receives the committed verdict and source
on its next turn; the presence or success of a later model call does not determine or undo it.

The client-generated `request_id` is scoped to the authenticated owner and presentation. The same
request and same payload returns the same committed response and creates no duplicate transcript or
result; reuse with a different payload is a conflict. Concurrent duplicate requests are enforced by
a database uniqueness constraint and transactional retry, not a process-local cache. An explicit
new attempt gets a new request ID. Authorization, reset/version and deletion rules apply even to
retries. If a transaction fails, show no committed verdict and permit retry with the same request
ID. If the response is lost after commit, retry or reload returns the recorded result. Invalid,
unconfirmed, unsupported or uncheckable answers never become correct/incorrect verdicts.

`undecided`, unreadable and `needs_review` produce no per-exercise correctness record. The
submission/response and transcript must still preserve enough status for idempotency and honest
replay; `needs_review` never exposes the key. Define exact retention and UI statuses in §10.

### 3.11 Checking service and tutor integration

`app/services/answers` resolves the stored presentation and delegates to the pure checker. The
confirmation route is the only entry point that creates a final learner submission and invokes the
checker; the model cannot directly submit, select a stored answer for checking or choose a verdict.
There is no `check_answer` model tool and no model-turn streaming buffer for checker results.
`propose_answer` only offers the confirmation UI with a valid exercise and source message: the
server supplies the original stored learner text, never model-generated answer text. The declaration is appended to the existing tool set where needed
and is not offered in discussion. A candidate must not reveal a key.

In révision, the submission service stores the submission, its canonical transcript entry and
`exercise_results` in one database transaction independently of the model turn. Spec 020's existing
`record_result` self-assessment continues to be stored with the model turn; its failure cannot erase
an already committed learner submission. Parcours stores the verdict with the séance transcript,
not as a revision result. Direct checking must serialize correctly with simultaneous conversation
turns and section changes, preserve the actual shown card and source, and return conflict rather
than interleave lost entries.

Output words by language and basis: material: « Stimmt mit der Lösung in deinem Material überein »
or « Stimmt nicht mit der Lösung in deinem Material überein »; computed: « Nachgerechnet: richtig »
or « Nachgerechnet: nicht richtig ». `both` names both sources. Unreadable provides an example of
expected form in course notation; precision and unit/form differences name the issue without showing
an answer. `undecided` explains that a reliable check was not possible; `needs_review` names the
conflict without revealing the key. The tutor sees the same committed verdict and basis as the UI.

### 3.12 Events, stored entries, history

The submission response carries the committed verdict and presentation ID; it is the immediate
source for the board. A canonical server-owned transcript entry carries the `submission_id`,
`exercise_id`, answer, outcome and basis and is persisted with the submission. Model-facing history
includes the learner's answer and committed outcome/basis, never a tool output key. On replay the
board restores the outcome for its original card and the student's confirmed answer. Retry and
reconnect never append it twice. Existing stored tool entries remain readable. New SSE event
`turn.stored {exercise_ids, message_id}` (§3.9). The exact schema and wire names require review.

### 3.13 Révision record: `exercise_results`

The submission transaction inserts at most one recordable `exercise_results` row per submission,
with unique `submission_id`, owner, course, chapter, section, revision scope/run, presentation
reference or generated task, answer kind, verdict, basis, and timestamp. It commits with the
canonical submission transcript entry. Unknown, unreadable, `undecided`, `form_unchecked` and
`needs_review` do not become correctness results. Existing `revision_results`, section outcomes,
and `record_result` self-assessments are unchanged. Read checked exercises per section with source,
date and exercise identity; a single verdict never marks a section as mastered. A new revision or
changed chapter cannot reuse an earlier run's presentation unless a later design explicitly links
that run and scope. Schema, migration and exact reset/deletion lifecycle are review items in §10.

**Stage boundary (requirements §13.1):** in 023a a révision submission commits the submission and
its transcript entry only; the card, replay and the tutor's next turn show the verdict, the Bilan
does not. 023b adds `exercise_results` and the Bilan list for submissions made from then on; no
backfill from earlier transcript entries.

### 3.14 Tutor prompt and mode layers

- `tutor.<lang>.md` (all four): set checkable cards using validated binding; use only committed
  server-supplied verdict and basis, and never call something correct or incorrect based on the
  model's own judgment. Guide without a verdict when checking is unavailable. This rule is measured
  behaviour (requirements §13.6): `scripts/probe.py --checker` counts verdict words in tutor prose
  outside a committed verdict per language, with a pass threshold set when the probes are written;
  the card's verdict line names its source so the learner knows which statement is authoritative.
- `propose_answer` may offer the confirmation of the original learner message;
  it cannot grade, send an answer, or select the key. Learner confirmation calls the normal route.
- `modes/revision.<lang>.md`: the tutor still displays the course's wording after the question is
  settled and asks for the student's own self-assessment (spec 020 D3).
- `modes/parcours.<lang>.md`: explain the checker for exercises with keys. Prompt and declaration
  pins change deliberately; prior stored cards remain readable.

### 3.15 Authoring

- Templates `templates/<subject>.pack.<lang>.md` (4 × 4): the §6 comment gains the key rule (one
  line per answer, from the solution only; a rule only when the exercise states one; a task only
  when the statement gives one of the two forms; not for « not corrected », §7, or other kinds)
  with the examples of 3.8.
- `prompts/authoring/pack.<lang>.md`: the same rule; « copy, never compute »; and for textbooks
  (D16): keep each exercise's reference in its heading (`#### 6.1.2 (S. 128, Nr. 11)`); join a
  solution printed elsewhere to its exercise by page, number and sub-letter; never turn an
  unordered answer pool into keys and never copy it into a statement; write `≈` on a key the
  material marks rounded and the rule of a governing note on each key it governs; keep the
  transcription's figure marks in the statement. Preserve an explicit review label with its
  exercise, without inferring it; the learner can correct the label in the pack (D19).
- Repair: key issues are repaired like other pack issues (bounded). If the last attempt still has
  only key issues, the runner drops those key lines and appends one §7 item per dropped key
  (`DROPPED_KEY[lang]`), then accepts the pack. `needs_review` is not an issue: the key stays, the
  material is not changed. `authoring_stage` logs `keys`, `keys_dropped`, `keys_needs_review`.
- Packs stored before this spec: no key lines; nothing re-authored.
- Pack editor (`PUT …/pack`): same `index_pack`; key issues are 422 `content_invalid`.

### 3.16 Chapters and révision scope

- `LessonChapter.keys: Mapping[ExerciseRef, PackKey]`, parsed by `CurriculumCache` per (chapter
  id, content version), task recomputation included.
- `RevisionChapter.keys`, from the same cache.
- Pack view API (`GET …/pack`): gains `keys: [{ref, status}]`.

### 3.17 Frontend

- `types.ts`: committed submission response, `Verdict`, `Basis`; card fields `exercise_id`, `status`,
  `task`, `check`; `CheckQuestionCard` without `correct_option_id` / `feedback` (old stored cards
  still parse: extra fields ignored). Stage 023a, every mode (requirements §13.4): the backend card
  model accepts the old fields as optional and drops them (the declaration no longer has them), and
  `CheckQuestionBoard` in parcours, discussion, révision and the notebook never colours a pick or
  shows `feedback` without a checker verdict.
- Reducer (`use-tutor-session.ts`): a committed submission response → transcript marker and the
  verdict of the card with that `exercise_id`; replay in `sessionFromEntries` the same way.
  `BoardStatus` of a board: `correct`/`wrong` from its exercise card's verdict.
- `ExerciseBoard`: show a dedicated answer field on a checkable card; for a pure mathematical
  variant show the server-generated statement. Show the verdict with its source, the
  `needs_review` notice or the `undecided` note as appropriate.
- `CheckQuestionBoard`: a selection on a bound card submits its option ID through the same
  learner submission path; display the verdict only when received from the checker. Unbound or
  old stored cards show no unverified correctness or model-authored automatic feedback. Replay a
  previously selected option only if it was recorded.
- Révision « Bilan » (`revision-bilan.tsx`): per section, the self-assessment chip as today and a
  list of checked exercises (ref or task, verdict mark, source, date), with explicitly labelled
  review exercises distinguishable. The learner corrects a label from the Bilan or the pack view;
  the correction is a per-exercise override stored outside the pack (requirements §13.7).
- For a candidate answer from chat, show the proposed exercise and answer for the learner to
  confirm or correct before submission. Preserve keyboard and screen-reader paths.
- Pack view: per exercise a « prüfbar » or « Lösung prüfen » badge, from `keys`.
- Voice bridge: unchanged in this spec; cards it shows are unbound (requirements §12.1).

## 4. Data models

| Where | Change |
| --- | --- |
| Presentation | Server-issued opaque card ID, owner, course, chapter, section, mode, content version, origin and immutable binding; created with the stored card. |
| Submission | Owner, presentation ID, client request ID, source, confirmed value, status and timestamp; uniqueness and retention enforce the idempotent submission contract. |
| Transcript | Canonical submission/result entry referring to the presentation and submission; learner entries gain a server `message_id` (023c). Old tool entries and cards remain readable. |
| `exercise_results` | Per-exercise revision result, unique by submission ID, written with submission and transcript; existing `revision_results` unchanged. Migration/schema names remain to be finalized. |
| `ExerciseCard`, `CheckQuestionCard` | Optional binding input, server presentation ID/status and generated task; no model-chosen `correct_option_id` or automatic feedback. |
| `PackIndex`, chapter scope | Parsed keys and the explicit review label from the material; current content version controls staleness. |
| Review-label override (023b) | Owner, chapter, exercise ref, label on/off, timestamp; outside the pack, so no new content version and no progress reset; deleted with the chapter; ignored when the ref no longer exists. |
| APIs and client events | Presentation, confirmed-submission response, transcript replay and revision result DTO; wire names are review items (voice report reconciliation: later voice spec). |

The presentation is scoped by its owner, course, chapter, section, version and mode, and by an
explicit logical revision run where relevant; the originating transcript row is evidence of the
card, not the sole eligibility key. Preserve learner data ownership, bounded storage and cascades
on account, course, chapter, content reset and session deletion. Define exact column shapes,
limits and migration in design review, without relying on browser-supplied authority.

## 5. Error handling

- A failed card-store operation leaves the card unbound or disabled; a learner can retry after a
  successful store (`turn.stored`). A reported or voice-created card never becomes bound.
- Unknown, stale, foreign, wrong-mode, unconfirmed or unpresented submissions are refused without
  a correctness verdict. Check owner and reset/content version on retries as well as initial calls.
- Malformed input is unreadable and gives an example; undecidable input gives no judgment. A
  conflict between the material and a computed solution produces `needs_review` without leaking a
  key. A checker exception or resource exhaustion must not produce a verdict or partial write.
- If the submission transaction fails, no result is committed and the same request can be retried.
  A retry after commit returns its original committed result. Simultaneous transcript or section
  changes must cause a safe retry/conflict rather than loss or duplication.
- Model/provider failures after a successful learner submission do not erase the committed result;
  before a card is stored they cannot make the uncommitted card checkable. Restore old stored cards
  without showing model-chosen correct options or invented historical selections.

## 6. Testing strategy

- Checker cases per kind and course language cover exact `5` versus `5,0` and `5,4`, explicit
  rounding/tolerance, exact unit conversion, fractions, supported surds and π forms, and unreadable
  or unsupported values. Boundaries include exact ties, close roots, repeated roots, excluded roots,
  no/all-real solutions, supported domain annotations and unequal domains; use independently
  calculated expected results, not only mirrored implementation examples.
- Exact parser and algebra: an exact mode of the `domain/expression.py` grammar keeps number
  lexemes (today `atom()` returns `float(t.text)`), so decimals remain rational; the plotting
  parser's behaviour and its tests are unchanged; guards survive cancellation; real-domain equality, gcd/root counts,
  isolations, resource caps and certified π rounding behave as specified. Unsupported cases and
  exhausted limits return inconclusive, never an invented verdict.
- Binding and authorization: a card that was not successfully stored, a forged voice report,
  another owner/course/mode, changed/reset content, or an unrelated revision run cannot be graded.
  A stored card continues working across parcours `capped` rollover and a later return to the same
  section; a replaced/closed revision or a content change invalidates it.
- Submission: card, choice and chat; no model-authored answer or key appears in the
  confirmation candidate. The learner can correct a proposed `2` when their answer was `12`.
  Identical retries and concurrent requests produce one submission and one result; request-ID reuse
  with different payload conflicts; lost responses, reload and failure before/after commit are
  covered. A failed later model turn leaves an already committed learner result intact.
- Transcript integration: `turn.stored` only after a successful store, never after a failed one
  (`turn.end` still follows); presentation and card are stored atomically before enabling a text
  card, including interruption and retry, section splits, caps and reset races. A card from a voice
  session or a reported voice turn is never checkable.
- Revision: submission, canonical entry and per-exercise result commit atomically; failed submission
  rolls all three back. `record_result` keeps spec 020 turn semantics, and self-assessment and
  checker results remain separate. Label, source and date survive replay without marking a section
  mastered. Practice-test aggregation stays deferred to spec 022.
- Frontend: field enabled only by `turn.stored`, choice, chat confirmation, cancellation,
  accessible keyboard/screen-reader interaction, failure and restore; old cards in every mode never
  gain an unverified verdict or feedback; dictated composer text behaves as typed text.
- Real-model probes are separately run and recorded: the tutor uses the committed outcome and
  basis, avoids inventing verdicts and does not disclose answer keys. No live-provider run is
  implied by this spec.

## 7. Performance

The checker makes no model call. Exact arithmetic, parsing, root isolation and certified π bounds
have explicit work, memory and time limits; exceeding a bound returns `undecided`. A blanket
sub-millisecond budget is not asserted. Reuse chapter-version key parsing where possible and bound
presentation/submission retention and quotas; latency and limits are design-review items.

## 8. Security and privacy

The user/course/chapter/section/mode/content-version and revision scope are checked server-side;
opaque IDs and a valid browser report alone do not establish ownership or presentation. The model
cannot submit a value, manufacture a stored card, choose a key or issue a checker verdict. Avoid
arbitrary evaluation of model or learner text; use the closed grammar and exact arithmetic with
resource caps. Store answers only where needed for the user's transcript and submission; logs and
usage metadata contain IDs and status, never answers or keys. The UI, candidate proposal and
checker outcome do not disclose a solution while the exercise is open. The existing tutor input
contains the course pack and can therefore contain material solutions; retaining that input does
not guarantee that free model prose cannot leak an answer. The existing application guardrails
and real-model probes remain necessary and their limits must be assessed.

## 9. Monitoring and observability

- `exercise_bound` / `exercise_unbound`: user, chapter, mode, status and reference/reason only.
- `answer_checked` / `answer_check_refused`: IDs, kind, verdict, source, duration or reason only.
- Authoring records counts of keys, dropped keys and keys needing review; revision logs result IDs
  and outcomes. Never log answer values, candidate text, keys or source material.

## 10. Open design work

The user requested reconciliation of `specs/023-review-claude.md`; requirements §11 records the
resulting direction. The revised specification remains in design review, not implementation planning:

1. Finalize exact presentation/submission/transcript schema, route contracts, concurrency, quota and
   migration; prove commit/retry/reload behavior against the current séance and revision stores;
   the `turn.stored` event and the server `message_id` (requirements §13.2–13.3).
2. Voice is out of this spec (requirements §12.1): specify only that voice cards stay unbound and
   that a reported voice turn cannot create a checkable presentation; the voice-session association
   and report reconciliation belong to the later voice spec.
3. Fix exact-parser interfaces, supported stated-domain grammar, certified root and π bounds, and
   concrete resource limits. Review examples and prove boundary handling before coding.
4. Specify review-label syntax in the pack, the override endpoint and the revision DTO (requirements
   §13.7). Defer the practice-test integration and aggregation contract to spec 022.
5. The plan follows the three stages of requirements §12.2 (023a checker and card submission in the
   parcours, 023b révision record and review labels, 023c chat confirmation); each stage ends in a
   shippable, tested state.

## Appendix A. Input for the later voice spec (not part of spec 023)

Kept from the design before requirements §12.1, for the spec that will check spoken answers:

- the trusted `/api/voice/tool` `display_board` path validates and persists
  the presentation and the authoritative card before returning a checkable card and ID. Associate
  it with the authenticated server-owned voice session and the applicable chapter, section,
  version and transcript ordering. The later `/api/seance/report` reconciles the same server-issued
  card/tool call ID, preserving spoken transcript ordering and partial stopped turns without
  duplicating or overwriting the authoritative card. A client-supplied report cannot create or
  alter a checkable presentation. If storage or association fails, the card is not checkable.
  The voice spec defines the exact voice-session association and report reconciliation.
