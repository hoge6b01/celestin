# Spec 023 — Answer checker: design

Requirements: `requirements.md` (owner's decisions §6, review decisions §7). Revised after the
review in `specs/023-review.md`. Builds on specs 005 (pack), 008/009 (board, expression grammar),
011/017/021 (course languages), 018 (stored tool entries), 020 (révision record). The
implementation branch must start from a branch that has spec 021's code (German rows): every
per-language table below has an `fr`, `en`, `nl` and `de` row.

## 1. Overview

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
4. **`check_answer`**, the eighth tool, declared last, offered in parcours and révision. It checks
   that the answer is in the student's latest message, resolves the bound exercise, settles the
   answer, returns verdict and basis (never the key), and emits `answer.checked`; the board marks
   the card with that `exercise_id`. In révision the result is written to a new table
   `exercise_results`, beside (not into) the self-assessed `revision_results`.

### Design decisions for the owner's review

Kept from the first design:

- **D1. The key never appears in a tool output**, not even after a correct answer or a reveal.
- **D3. Equations and inequalities are solved only as polynomials** in one variable of degree
  1–4. Rational roots are found exactly; an irrational root is checkable only when the task states
  a rounding rule (§7.1 of the requirements: exact by default).
- **D4. One variable** per expression, relation or task.

Superseded: **D2** (« `check_question` unchanged ») → requirements §7.6, implemented by D9.

New, from the review decisions:

- **D5. Binding through the board.** `ExerciseCard` and `CheckQuestionCard` gain an optional
  `check`. For a pack reference, the server **replaces the card's statement with the pack's
  statement of that exercise** (the block under its heading, cut before its answer and key lines);
  if it cannot cut it reliably, the card is shown unbound. For a variant, the server **adds the task
  as it parsed it** under the statement (« Aufgabe: x² − 5x + 6 = 0 lösen », plus the rounding rule
  if any); that line is the checked task. The board declarations change (pins regenerated).
- **D6. `exercise_id` is a short HMAC** over the checking data (user, chapter, content version,
  pack reference or canonical task). Text turns resolve it from the séance's stored entries; voice
  turns get the bound checking data back from the browser and verify it against the id, so no
  server state is added and the model cannot invent a binding.
- **D7. Recomputing a stored solution** needs the task on the key line, copied from the statement
  by the authoring agent. Agreement gives the basis « material, recomputed »; disagreement marks the
  key `needs_review`: no verdict, a notice on the card and in the pack view, nothing recorded, the
  stored solution untouched. Agreement is evidence, not proof, that the task was copied right: two
  independent lines of the material agree.
- **D8. Expression classes**: polynomials and rational expressions with rational coefficients in
  one variable, compared exactly (`n₁·d₂ = n₂·d₁` as polynomials). Rational expressions count as
  equal on their common domain (`(x²−1)/(x−1)` = `x+1`). Anything else (roots, powers with a
  non-integer exponent, functions) is « not reliably checkable ». Sample points are gone.
- **D9. Multiple choice**: `CheckQuestionCard` loses `correct_option_id` and `feedback`. Unbound, a
  pick is sent as today and shows no verdict. Bound (`check.exercise` to a `choice` key), the
  question is the pack's statement and the buttons are the key's option ids; the verdict comes
  from `check_answer`. Stored cards replay without a verdict; the cahier no longer reveals an option.
- **D10. Révision results per exercise** in a new table `exercise_results`; `revision_results` and
  the section outcome logic of spec 020 are untouched.
- **D11. Rounding rule semantics**: with `round d`, the key is the material's rounded value;
  `correct` iff the answer equals it exactly; `precision` iff the answer is the same value rounded
  differently (more decimals that round to the key, or fewer decimals the key rounds to); else
  `incorrect`. With `±t`: `correct` iff `|a − k| ≤ t`. Without either: exact equality only.

## 2. Architecture

```
 pack.md §6 exercise                         display_board (card with `check`)
  statement …                                   │ services/tools/board.py → bind.py
  **Antwort:** …                                │  pack ref → statement from pack, key
  **Schlüssel a):** set {2; 3} | solve …        │  variant  → task line, computed key
        │                                       │  exercise_id = HMAC(checking data)
        ▼                                       ▼
 domain/pack.py index_pack                stored ToolEntry (card + check data)
   └► domain/answers/keys.py pack_keys          │
        (parse, recompute task → agrees /       │       learner message / voice transcript
         needs_review)                          │                 │
        │                                       ▼                 ▼
 LessonChapter.keys / RevisionChapter.keys ─► services/tools/check.py check_answer(args, ctx)
   (cached per content version)                  │ answer ∈ learner_text?
                                                 │ exercise_id → bound exercise → key
                                                 ▼
                              domain/answers/check.py check(key, answer, lang) → Checked
                                (readers, units, algebra, variants; exact)
                                                 │ verdict + basis
                 ┌───────────────────────────────┼──────────────────────────┐
                 ▼                               ▼                          ▼
     tool output (course language,     SSE answer.checked            révision: turn_results
     verdict + source, never key)      {exercise_id, verdict,        → exercise_results
                                        basis, …}                     (per exercise)
                                                 │
                                   frontend: mark on the card with that exercise_id
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
Kind = Literal["choice", "number", "expression", "interval", "set", "point", "word"]
Rational = Fraction

@dataclass(frozen=True) class Unit:        dimension: str; factor: Fraction; symbol: str
@dataclass(frozen=True) class Rule:        round: int | None = None; tolerance: Fraction | None = None
                                           # at most one of them; none = exact
@dataclass(frozen=True) class Quantity:    value: Fraction; decimals: int; unit: Unit | None
@dataclass(frozen=True) class Bound:       value: Fraction | None; closed: bool   # None = ±∞, never closed
@dataclass(frozen=True) class Interval:    low: Bound; high: Bound

@dataclass(frozen=True) class ChoiceKey:     option: str; options: tuple[str, ...]
@dataclass(frozen=True) class NumberKey:     quantity: Quantity; rule: Rule
@dataclass(frozen=True) class ExpressionKey: function: RationalFunction; variable: str  # see 3.6
@dataclass(frozen=True) class IntervalKey:   union: tuple[Interval, ...]; rule: Rule
@dataclass(frozen=True) class SetKey:        values: tuple[Fraction, ...]; rule: Rule   # sorted, distinct
@dataclass(frozen=True) class PointKey:      coords: tuple[Fraction, ...]; rule: Rule
@dataclass(frozen=True) class WordKey:       words: tuple[str, ...]; accents: bool
Key = ChoiceKey | NumberKey | ExpressionKey | IntervalKey | SetKey | PointKey | WordKey

Basis = Literal["material", "computed", "both"]
Verdict = Literal["correct", "incorrect", "unreadable", "precision", "unit_differs",
                  "undecided"]                      # undecided = not reliably checkable
@dataclass(frozen=True) class Checked:
    verdict: Verdict; kind: Kind; basis: Basis
    expected: str | None   # `unreadable`: an example of the expected form, course notation
    reason: str | None     # `undecided`: a reason code (`expression_class`, …)
```

Recorded verdicts (révision, spec 022): `correct`, `incorrect`, `precision`, `unit_differs`.
`unreadable` and `undecided` are never recorded.

### 3.3 `app/domain/answers/readers.py`

One reader per kind, per course language (`by_language` tables). The same reader parses a key and
a student's answer. Each returns a value or `None` (unreadable). Every number is read to an exact
`Fraction` with its written decimals (`12,50` → 25/2, decimals 2).

| Kind | Accepts (de shown; fr/nl like de with `;`, en with `,` and `.`) | Notes |
| --- | --- | --- |
| number | `374`, `12,5`, `12.500`, `10 000`, `3/4`, `−2`, `12,5 %`, `25 m/s`, `x = 3` | `NUMBER[lang]`; trailing unit via `units.py`; leading `<name> =` stripped |
| expression | `2(x+1)`, `2x+2`, `f(x) = x^2` | `expression.parse(src, frozenset({variable}))`, then `algebra.py`; leading `f(x) =`/`y =` stripped; decimal comma → point in comma languages (`1,5x`) |
| interval | `]2 ; 5]`, `]−∞ ; 3[ ∪ ]4 ; +∞[`, `x > 2` (one-sided only), `L = ]2 ; 5]` | `[−∞ …` refused (∞ never closed); `∞`, `inf`, `unendlich` |
| set | `{−1; 3}`, `L = {−1; 3}`, `x = −1 oder x = 3`, `x₁ = −1; x₂ = 3`, `{}` / `∅` / `L = { }` | `SET_SEPARATOR[lang]`, `JOINERS[lang]` (de `oder`/`und`; fr `ou`/`et`; nl `of`/`en`; en `or`/`and`) |
| point | `P(2 \| −1,5)`, `(2 \| −1,5)`, `(2; −1,5)` (de); `(2, −1.5)` (en) | `COORDS[lang]` plus a value reader; leading name stripped |
| word | any text | NFKC, casefold, collapse spaces; accents stripped unless the key says `accents` |
| choice | `B`, `b)`, `Antwort B`, `(b)` | one option id among the key's `options`, case-insensitive |

Normalisation before every reader: NFKC, `−`/`–` → `-`, `·`/`×` kept for expressions, surrounding
`$…$` stripped (`text.MATH`), trailing `.` stripped.

### 3.4 `app/domain/answers/units.py`

`UNITS: dict[str, Unit]`, aliases to `(dimension, exact factor to SI)`:

- length: mm, cm, dm, m, km; mass: mg, g, kg, t; time: s, min, h; speed: m/s, km/h (factor 5/18;
  aliases `m·s^-1`, `km·h^-1`); volume: mL/ml, cL/cl, dL/dl, L/l, cm³, dm³, m³ (`cm^3`); area: mm²,
  cm², dm², m², km², a, ha; percent: `%` (dimensionless, factor 1/100).
- Same dimension → the answer is converted **exactly into the key's unit**, then compared under
  the key's rule (a rounding rule applies in the key's unit).
- Different dimension, or a unit outside the table that differs from the key's written unit →
  `unit_differs`. Key with a physical unit, answer without → `unit_differs`; key without a unit,
  answer with a physical one → `unit_differs`.
- `%`: `12,5 %` and `0,125` are equal in either direction.

### 3.5 `app/domain/answers/check.py`

```python
def check(key: Key, answer: str, language: CourseLanguage, basis: Basis) -> Checked
```

- **number**: read; units (3.4); then the rule (D11): exact `==`; `±t`; or `round d` with
  `precision`.
- **expression**: both to `RationalFunction` (3.6); either outside the class → `undecided`
  (`expression_class`); else `n₁·d₂ == n₂·d₁` → correct, else incorrect.
- **interval**: unions normalised (sorted, merged); bounds compared under the rule (exact by
  default), closedness equal.
- **set**: same size, pairwise equal under the rule; duplicates in the answer ignored.
- **point**: same dimension, coordinates equal under the rule.
- **word**: normalised answer equals one of `words`.
- **choice**: the id is one of `options` (else unreadable), then equal ids.

Never raises on student input (fuzz test).

### 3.6 `app/domain/answers/algebra.py`

- `Polynomial`: tuple of `Fraction` coefficients, normalised (no trailing zeros).
- `RationalFunction(num: Polynomial, den: Polynomial)`.
- `to_rational(node, variable) -> RationalFunction | None`: over the `expression.py` AST: number
  literals (exact), the variable, `+`, `−`, `×`, `÷`, unary minus, `^` with an integer literal
  exponent (negative allowed: `x^-2` = 1/x²). Any function, a non-integer or non-literal exponent,
  another variable → `None`. Caps: degree ≤ 24, numerator/denominator ≤ 64 coefficients, each
  coefficient's numerator and denominator ≤ 10¹² → else `None`.
- `evaluate_exact(rf, x: Fraction) -> Fraction | None` (`None` where the denominator is 0).
- `real_roots(p: Polynomial, degree 1–4) -> Roots(rational: tuple[Fraction, ...],
  irrational: tuple[float, ...])`: integer-scaled coefficients; rational root theorem on the
  divisors (coefficients ≤ 10⁶ in absolute value, else `None`), deflation by each rational root;
  the remaining factor (degree ≤ 4): closed form for degree ≤ 2, Durand–Kerner then Newton polish
  for 3–4, imaginary parts `< 1e−9` dropped, each irrational root verified by sign change. No numpy.

### 3.7 `app/domain/answers/variants.py`: tasks

One form for a pack key's task and for a variant:

```python
@dataclass(frozen=True) class Evaluate: expression: str; variable: str; at: str      # `at` in course notation
@dataclass(frozen=True) class Solve:    relation: str; variable: str                 # one of = < > ≤ ≥ (<=, >=)
Task = Evaluate | Solve

def task_key(task: Task, kind: Kind, rule: Rule, language) -> Key | NotCheckable
def task_text(task: Task, rule: Rule, language) -> str    # the line the card shows (3.9)
```

- `Evaluate`: `to_rational` and `at` exact → `NumberKey` exact. Outside the class (e.g. `√`) →
  only with `round d`: `expression.evaluate` in float, the key is the value rounded to `d`
  decimals; if the value is within `1e−9` of a rounding boundary → `NotCheckable("boundary")`.
  Division by zero → `NotCheckable("undefined")`.
- `Solve`: split on the single top-level relational operator; `left − right` must be a polynomial
  (rational function with constant denominator) of degree 1–4 (D3); `real_roots`.
  - `=`: `SetKey(roots)`; `kind == "number"` only with exactly one real root.
  - `<`, `>`, `≤`, `≥`: `IntervalKey` from the sign of the polynomial on each piece (tested exactly
    at a rational point inside the piece).
  - Any irrational root (or bound) requires `round d`, applied to it; otherwise
    `NotCheckable("irrational")`.
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
- `<rule>`: `round <d>` or `±<tolerance>` (number, interval, set, point), only when the exercise
  states it; word: alternatives separated by ` / `, `accents` flag; choice: `of <ids>` lists the
  exercise's option ids.
- `<task>`: `solve <relation>` or `eval <expression> at <variable> = <value>`, copied from the
  statement; optional.
- Examples (de): `**Schlüssel:** number 374` · `**Schlüssel:** number 25 m/s` ·
  `**Schlüssel:** number 3,14 round 2` · `**Schlüssel a):** interval ]2 ; 5]` ·
  `**Schlüssel b):** set {2; 3} | solve x^2 - 5x + 6 = 0` · `**Schlüssel:** point P(2 | −1,5)` ·
  `**Schlüssel:** expression x 2(x+1)` · `**Schlüssel:** word Hypotenuse` ·
  `**Schlüssel:** choice B of A B C D`.

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
  `pack.key_task` (task unreadable or not checkable), `pack.key_class` (an expression key outside
  the class of 3.6) (catalog keys in fr/en/nl/de, `render_issue`).
- With a task: `task_key` computed and compared with the stored key under the key's rule → status
  `agrees` (basis `both`) or `needs_review` (no verdict, D7). No task → `material`.
- `exercise_statement`: the lines under the exercise's heading up to the first line starting with
  `ANSWER_LABEL[lang]` (the templates' answer label, `**Antwort:**` etc.) or `KEY_LABEL[lang]`;
  `None` when neither line is found (the statement cannot be cut from its solution).
- `index_pack` calls `pack_keys` and returns its issues; `PackIndex` gains
  `keys: frozenset[ExerciseRef]`.

### 3.9 Binding: `app/services/tools/bind.py` and the board cards

```python
class CheckSpec(BaseModel):              # on ExerciseCard and CheckQuestionCard; strict, nullable fields
    exercise: Annotated[str, Field(max_length=16)] | None        # "6.1.2 a)"
    task: TaskArgs | None                                         # variant
class TaskArgs(BaseModel):
    kind: Kind
    solve: Annotated[str, Field(max_length=120)] | None
    evaluate: Annotated[str, Field(max_length=120)] | None
    at: Annotated[str, Field(max_length=24)] | None
    variable: Annotated[str, Field(pattern=r"^[a-z]$")]
    round: Annotated[int, Field(ge=0, le=6)] | None
```

`display_board` runs `bind(card, ctx)` for each card with `check`:

1. Exactly one of `exercise` / `task`; `check_question` only with `exercise`.
2. Pack: the ref is in the chapter's keys (révision: of the section's chapter); the statement cuts
   (`exercise_statement`); for `check_question` the key is `choice`. Variant: `task_key` succeeds.
3. On success the server rewrites the card: pack → `statement` (or `question`) := the pack's
   statement; `check_question` options := the key's ids (text = id); variant → a `task` line is set
   to `task_text`. Then `exercise_id := "x" + hex(HMAC_SHA256(k, canonical))[:10]`, where
   `canonical` is JSON of (user id, chapter id, content version, ref or task, rule) and `k` is
   derived from `SESSION_SECRET` (`hkdf`, label `celestin-exercise-v1`). The card carries
   `exercise_id`, `bound: {exercise | task}`, `status: material | agrees | needs_review |
   computed`.
4. On failure the card is shown unbound (no `exercise_id`), and the tool output says why, in the
   course language (« 6.1.2 a) ist nicht prüfbar: … Begleite ohne Urteil. »). Never a tool error:
   the board still shows.
5. `needs_review`: the card is bound (so a check can say why there is no verdict) and shows a notice
   (catalog `board_needs_review`: « Die Lösung in deinem Material sollte geprüft werden; hier gibt
   es keine automatische Bewertung. »), without the solution.

The board's tool output gains one line per bound card: « Prüfbar: x3f9a1c2d0 (6.1.2 a)) ».

Declarations: `ExerciseCard` gains `check: CheckSpec | None`; `CheckQuestionCard` loses
`correct_option_id` and `feedback`, gains `check`. The server-set fields (`exercise_id`, `bound`,
`status`, `task`) are not in the declaration (output-only model). `board_declarations.json` is
regenerated deliberately.

### 3.10 `TurnContext` additions

- `learner_text: str | None`: this turn's learner message (parcours chat route, révision turn
  route); `None` on an opening turn and in discussion.
- `bound: Mapping[str, BoundExercise]`: exercise id → checking data, loaded from the conversation's
  stored entries at turn start and extended by `display_board` in the turn.
- Voice: `VoiceToolRequest` gains `learner_text: str ≤ 2000 = ""` (latest user transcript) and
  `bound: list[BoundExercise] ≤ 20` (what the browser's board holds); `/api/voice/tool` verifies
  each against its id (recomputed HMAC) and drops the others.
- `answers/normalise.py: contains(learner_text, answer) -> bool`: both normalised (3.3), spaces
  removed, casefolded; substring test.

### 3.11 The tool: `app/services/tools/check.py`

```python
class CheckAnswerArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: Annotated[str, Field(min_length=1, max_length=200)]
    exercise_id: Annotated[str, Field(pattern=r"^x[0-9a-f]{10}$")]
    chapter: Annotated[int, Field(ge=1, le=999)] | None       # révision: required
    section_id: Annotated[str, Field(max_length=40)] | None   # révision: required

@dataclass(frozen=True)
class AnswerChecked:
    checked: Checked
    exercise_id: str
    exercise: str | None          # pack ref, or None for a variant
    task: str | None              # the variant's task text
    chapter_id: str | None
    section_id: str | None
    output: str                   # course language, never the key
    marker: Marker                # marker.answer_checked.<verdict>
```

Order of checks (each refusal a `ToolValidationError` in the course language):

1. révision: `chapter` and `section_id` present and valid (reuses `result.py`'s words);
2. `ctx.learner_text` present and `contains(learner_text, answer)` (`not_the_students`);
3. `exercise_id` in `ctx.bound` (`unknown_exercise`: « Diese Aufgabe ist nicht gebunden: begleite
   ohne Urteil. »);
4. status `needs_review` → no check: output « Keine Bewertung: Die Lösung im Material und die
   Nachrechnung weichen ab. Verrate nichts; begleite ohne Urteil. », event with verdict
   `undecided`, reason `needs_review`;
5. `check(key, answer, language, basis)`, basis from the status (`material`, `both`, `computed`).

Output words by language and basis, e.g. de: correct/material « Stimmt mit der Lösung in deinem
Material überein. »; correct/both « Stimmt mit der Lösung im Material überein, nachgerechnet. »;
correct/computed « Nachgerechnet: richtig. »; incorrect « Stimmt nicht mit der Lösung im Material
überein. » / « Nachgerechnet: nicht richtig. », then « Verrate die Lösung nicht; arbeite mit Fragen
und Hinweisen weiter. »; unreadable « Nicht als {kind_word} lesbar. Bitte um die Antwort in der
Form {expected}. »; precision « Der Wert stimmt, ist aber nicht so gerundet, wie die Aufgabe es
verlangt ({decimals} Nachkommastellen). »; unit_differs « Die Einheit passt nicht. »; undecided
« Das kann der Prüfer nicht sicher entscheiden: begleite ohne Urteil. »

Registry row: `name="check_answer"`, `strict=True`, declared **after `record_result`**;
`replay=replay_check` (output rebuilt from the stored entry), `shown=shown_check`, `check=None`.
`_MODE_TOOLS`: parcours += `check_answer`; révision += `check_answer`; discussion unchanged
(discussion boards may still carry `check`; binding is harmless there, nothing can check it).
Description (French, as all declarations): « Fais vérifier par le code la réponse finale de ton
élève à un exercice prüfbar… ».

### 3.12 Events, stored entries, history

- SSE `answer.checked`: `{exercise_id, verdict, basis, kind, exercise: str | null, chapter_id,
  section_id, marker}`. Added to `api/schemas` events, `tool_events.event_of`,
  `frontend/src/lib/tutor/types.ts` `TutorEvent`.
- `ToolEntry` gains `verdict`, `basis`, `exercise_id` (only on a `check_answer` entry; the
  validator `_recorded_on_their_tool_only` extended). The bound card fields live in the stored
  board entry's card JSON. Never sent to the model beyond the replayed outputs.
- `history.to_provider_input` replays the stored outputs (`replay_check`, the board's output with
  its « Prüfbar » lines).

### 3.13 Révision record: `exercise_results`

- Migration `0015_exercise_results`: table `exercise_results`
  `(id, user_id, course_id, chapter_id, section_id, conversation_id, exercise_ref String(16) NULL,
  task String(200) NULL, kind String(12), verdict String(12), basis String(8), created_at)`,
  check constraints on `verdict in ('correct','incorrect','precision','unit_differs')` and
  `basis`, exactly one of `exercise_ref` / `task`; FKs and cascades as `revision_results`
  (deleted with the account, course, chapter). Index `(user_id, course_id, chapter_id)`.
- `revision.turn_results` also collects `check_answer` entries with a recordable verdict; written
  in the same transaction as the transcript (spec 020 D6).
- Reads: latest per `(chapter_id, section_id, exercise_ref or task)`.
- `revision_results`, `record_result`'s tally and the section outcome logic of spec 020 are
  unchanged: a checker result never sets an outcome (requirements R5.2).
- Trailing state message (`curriculum_render`, by language), per section after the
  self-assessment: « geprüft: 6.1.2 a) richtig (12.11.), Variante x² − 5x + 6 = 0 nicht richtig
  (12.11.) », at most 5 per section, newest first.
- `GET/POST /api/courses/{c}/revision`: response gains `checked[]`:
  `{chapter_id, section_id, exercise, task, verdict, basis, at}`.
- Parcours: no write (decision §6.1).

### 3.14 Tutor prompt and mode layers

- `tutor.<lang>.md` (4 files): the paragraph « Tu ne corriges pas mécaniquement » becomes: to set
  a checkable exercise, put it on the board with `check` (a pack exercise that has a key, or a
  variant task); for the final answer, call `check_answer` with the card's `exercise_id` and the
  answer exactly as written, and say its verdict with its source; never say « juste » / « faux »
  without it; for anything else the previous rule holds. A `check_question` gives no verdict unless
  bound.
- `modes/revision.<lang>.md`: after `check_answer`, still show the course's wording and ask the
  student's own assessment (spec 020 D3).
- `modes/parcours.<lang>.md`: one line, the checker for exercises with keys.
- Pins regenerated deliberately: `system_text_sha*.txt`, `test_prompt_files_languages`.

### 3.15 Authoring

- Templates `templates/<subject>.pack.<lang>.md` (4 × 4): the §6 comment gains the key rule (one
  line per answer, from the solution only; a rule only when the exercise states one; a task only
  when the statement gives one of the two forms; not for « not corrected », §7, or other kinds)
  with the examples of 3.8.
- `prompts/authoring/pack.<lang>.md`: the same rule; « copy, never compute ».
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

- `types.ts`: `AnswerCheckedEvent`, `Verdict`, `Basis`; card fields `exercise_id`, `status`,
  `task`, `check`; `CheckQuestionCard` without `correct_option_id` / `feedback` (old stored cards
  still parse: extra fields ignored).
- Reducer (`use-tutor-session.ts`): `answer.checked` → transcript marker and the verdict of the
  card with that `exercise_id` (any board of the séance); replay in `sessionFromEntries` the same
  way. `BoardStatus` of a board: `correct`/`wrong` from its exercise card's verdict.
- `ExerciseBoard`: the task line for a variant; under the statement a verdict line with its source
  (catalog `board_verdict_<verdict>_<basis>`), the `needs_review` notice, the `undecided` note.
- `CheckQuestionBoard`: a pick sends the answer as today and shows no colour; a bound card shows the
  verdict from `answer.checked`. Cahier reread: no reveal.
- Révision « Bilan » (`revision-bilan.tsx`): per section, the self-assessment chip as today and a
  list of checked exercises (ref or task, verdict mark, source, date).
- Pack view: per exercise a « prüfbar » or « Lösung prüfen » badge, from `keys`.
- Voice bridge: sends `learner_text` and the board's bound exercises with every tool call.

## 4. Data models

| Where | Change |
| --- | --- |
| `exercise_results` | new table (migration 0015), 3.13 |
| `ExerciseCard`, `CheckQuestionCard` | `check` in; server fields `exercise_id`, `bound`, `status`, `task`; `CheckQuestionCard` − `correct_option_id`, − `feedback` |
| `ToolEntry` (stored JSON) | `verdict`, `basis`, `exercise_id` (check_answer only) |
| `PackIndex` | `keys: frozenset[str]` |
| `LessonChapter`, `RevisionChapter` | `keys: Mapping[str, PackKey]` |
| `TurnContext` | `learner_text`, `bound` |
| `VoiceToolRequest` | `learner_text` (≤ 2000), `bound` (≤ 20) |
| Révision DTO | `checked[]` |
| Pack DTO | `keys[]` |
| SSE | `answer.checked` |

## 5. Error handling

- Model errors are tool errors (3.11) or an unbound card (3.9), never HTTP errors; the model reads
  the reason and asks again (unreadable, not the student's) or guides without a verdict.
- `check_answer` in discussion is refused by `registry.execute` (not offered).
- Readers return `None`, `check` never raises on student input. An exception in the checker is a
  bug: logged `check_failed`, tool output « Prüfer nicht verfügbar: begleite ohne Urteil. », the
  turn continues.
- A forged or stale `exercise_id` (voice) fails the HMAC → `unknown_exercise`. A content version
  change makes old ids unknown: the card replays, a new check is refused.
- Authoring: unreadable keys → repair → drop with §7 item; `needs_review` never fails a run.
- Old stored `ToolEntry` and card JSON stay valid.

## 6. Testing strategy

- **Case tables** `tests/fixtures/answer_cases.json`: per kind × course language, rows
  `{key, answer, verdict}`: notation variants, exactness (`5` vs `5,0` vs `5,4`), rules (`round 2`:
  `3,14` / `3,1416` / `3,1`; `±0,01`), units exact (`90 km/h` vs `25 m/s`, `0,5 m` vs `50 cm`),
  fractions, empty set, unions, ∞, leading names, garbage → unreadable, expressions outside the
  class → undecided.
- `test_algebra.py`: expansion, rational normalisation, `n₁·d₂ = n₂·d₁`, caps, exact roots, rational
  root theorem, irrational roots, repeated roots, no real root.
- `test_variants.py`: every reason; `round` boundary guard; inequalities.
- `test_pack_keys.py`: key lines per language, rules, tasks, `agrees` / `needs_review`,
  `exercise_statement` cut (answer line never included), issue codes; `test_issue_messages.py`.
- `test_bind.py`: pack and variant binding, statement replaced, task line, unbound reasons, HMAC
  stable and user/chapter/version-bound, voice verification.
- `test_check_tool.py`: each refusal, outputs per language and basis never containing the key,
  learner-text check, `needs_review`, révision args.
- Registry: new `check_declaration.json`; `board_declarations.json` regenerated (the diff reviewed:
  only `check` added, `correct_option_id`/`feedback` removed); `path_declarations` unchanged;
  `test_mode_tools`.
- Révision: migration 0015 up/down; `turn_results` with checks; reads; DTO; render goldens of the
  state message per language; `revision_results` untouched.
- Authoring: fake completion with good, bad, unrepairable and disagreeing keys.
- `test_model_input_wall*.py`, `test_language_is_passed.py`, `test_by_language_tables.py`.
- Frontend: reducer (live, replay, verdict on a non-latest board), CheckQuestionBoard without
  colour, old stored card, ExerciseBoard verdict/source/notice, Bilan list, pack badges, voice
  bridge payload, language sweeps.
- Real-model probes (cost money, not in pytest): `scripts/probe.py --checker` per language: the
  tutor binds a keyed exercise, calls `check_answer` with its id and the answer verbatim, never
  states a verdict without it, never leaks the key.

## 7. Performance

- `check` is pure Python, sub-millisecond; caps bound the algebra (3.6).
- Keys and their recomputation once per chapter content version (cache), not per turn.
- `bound` loaded once per turn from the conversation's stored entries (already read for history).
- The declaration and prompt changes move the cached prefix once per mode and language.

## 8. Security

- No evaluation of model or student text: the expression grammar parser only; length caps
  everywhere (answer 200, task 120, voice `learner_text` 2000, `bound` 20).
- The answer must come from the student's message; the exercise must be bound by the server (HMAC):
  the model can neither check text the student did not write nor an exercise that was not shown.
- The key never leaves the server in a tool output or a card; the pack's statement shown on a card
  is cut before its answer and key lines.
- Routes unchanged except the `/api/voice/tool` body and the révision and pack DTOs.

## 9. Monitoring and observability

- `exercise_bound`: user, chapter, mode, source (`pack` | `variant`), status, ref; or
  `exercise_unbound` with the reason code.
- `answer_checked`: user, course, chapter, mode, kind, verdict, basis, exercise ref, ms. Never the
  answer or the key. `answer_check_refused`: reason code only.
- Authoring: `keys`, `keys_dropped`, `keys_needs_review` on `authoring_stage`.
- `exercise_result` log on write (ids, verdict, basis).

## 10. Open questions for the owner

1. **D8 domain rule**: count `(x²−1)/(x−1)` and `x+1` as equal (common domain, as a « vereinfache »
   exercise expects), or refuse a verdict when the domains differ?
2. **D9 old cards**: stored `check_question` cards replay without colour from now on (consistent),
   or keep their old display as history?
3. **D9 feedback**: the model's `feedback` text after a pick is removed (it could say « richtig »);
   Célestin says it in speech instead. Acceptable?
4. **Contract with spec 022**: proposed: 022 sets its items as bound exercises (3.9), checks them
   with `check()` directly (no tool call), records them in `exercise_results` with the test's id,
   and treats `undecided` and unbound items as self-assessed. To be settled when 022 is designed.
