# Spec 023 — Answer checker: design

Consolidated on 22 November 2026 from the reviewed design (history: `decisions.md`,
`specs/023-review*.md`, `specs/023-design-proposal.md`, git). Requirements: `requirements.md`.
Every part names its stage: **023a** (keys, checker, bound cards, direct submission, choice cards
in every mode), **023b** (révision record per exercise, review labels), **023c** (chat
candidates). Builds on specs 005 (pack), 008/009 (board, expression grammar), 011/017/021
(course languages), 018 (stored séances), 020 (révision). The implementation branch starts from
a branch with spec 021's code: every per-language table has `fr`, `en`, `nl` and `de` rows.

## 1. Overview

1. **Keys in the pack** (023a). Each typical exercise with a solution in the material carries
   key lines: `**Schlüssel:** number 374`, `**Schlüssel a):** set {2; 3} | solve x^2 - 5x + 6 = 0`.
   `index_pack` validates them with the readers that read student answers; a key with a task is
   recomputed once per content version and marked `agrees` or `needs_review`.
2. **`app/domain/answers/`** (023a): readers per kind and language, exact numbers (`Fraction`,
   surds, `a + bπ`), exact units, an exact algebra with domain guards and certified root
   isolation, the comparison, keys computed for variants.
3. **Presentations** (023a): a card on `display_board` may carry `check` (pack reference or variant
   task). The server binds it, shows exactly what is checked, and stores a **presentation** with the
   turn; the answer field becomes active on `turn.stored`.
4. **Submissions** (023a): `POST /api/answers` takes the student's whole field value or pick, checks
   it at once and stores submission, verdict and a transcript entry together. Célestin reads the
   verdict on its next turn. No model tool runs a check.
5. **Révision record and labels** (023b); **chat candidates** with `propose_answer` (023c).

### Decisions

| | Decision |
| --- | --- |
| D1 | The key never leaves the server: not in a tool output, a card, an event or a response. |
| D3 | Equations: one-variable polynomials of degree 1–4, the variable in a denominator (`=` only), pure powers `x^n = c`. A verdict needs a proven complete solution and, for approximate roots, a certified rounding. |
| D4 | One variable per expression, relation or task. |
| D5 | Binding through the board: the server replaces a pack-bound card's statement with the pack's statement (stem + the one sub-item), or generates a variant's whole statement from its task. Anything it cannot bind reliably is shown unbound. |
| D6 | Presentations are stored records (opaque id, owner, scope, content version, binding), written in the turn's own store transaction; an id alone is never authorization. |
| D7 | A key with a task is recomputed: agreement → basis `both`; proven disagreement → `needs_review` (no verdict, notice, solution not overwritten); an inconclusive computation proves nothing and leaves basis `material`. |
| D8 | Expressions: rational functions with rational coefficients, compared exactly, only after the domains (guards from the original parse, intersected with a stated domain) are proven equal; otherwise `undecided`. |
| D9 | Choice card: the declaration loses `correct_option_id` and `feedback`; a lenient reading model accepts them in stored and reported cards and drops them; no pick is coloured without a checker verdict, in every mode. |
| D10 | Révision results per exercise in `exercise_results` (023b); `revision_results` and spec 020's outcome logic unchanged. |
| D11 | Rules: `exact`; `±t`; `round d` (d < 0: tens, hundreds); `approx` (material wrote `≈`/« rund »/« ca. », or a governing note; d = the key's decimals). Under `round`/`approx`: `correct` iff the answer rounded to d (half away from zero, exact) equals the key and has ≥ d decimals; `precision` iff it has fewer decimals and the key rounded to them equals it; else `incorrect`. A vague « Runde sinnvoll » is no rule: the rounding gets no verdict. |
| D12 | Exact numbers: `Fraction`, `Surd(a, b, c)` = a + b√c, `PiLinear(a, b)` = a + bπ. Quadratic roots come out as surds. |
| D13 | Required form on the key: `unit`, `fraction`, `reduced`, `mixed`, `decimal`, `scientific`, `power` → `form_differs` when unmet; expression forms (`vertex`, `factored`, `expanded`) are not checked → `form_unchecked`. |
| D14 | Figure marks and measuring operators make an exercise unbindable. |
| D16 | Textbook authoring: references in headings, appendix solutions joined, answer pools never keys, named key parts, `mapping` kind. |
| D17 | Submissions only from the student: the card's field or pick (023a), a confirmed chat candidate taken from the student's own message (023c). |
| D19 | Review labels from explicit material marks; the student's correction is an override outside the pack (023b). |

D2 (`check_question` unchanged) is superseded by D9; D15, D18 are folded into D3 and D8.

## 2. Architecture

```
 material ─► pack.md + key lines ─► index_pack / pack_keys (validate, recompute tasks)
                                              │  cached per (chapter, content version)
 model ─► display_board(card + check) ─► bind.py: key or task → bound card (statement from
                                              │  pack or generated), presentation record
                                              ▼
           turn store (store_seance / conversations.append) writes cards + presentations
                                              │  success → SSE turn.stored {exercise_ids, message_id}
                                              ▼
 student ─► card field / pick ─► POST /api/answers ─► services/answers.py
            (023c: confirmed chat candidate)          resolve presentation, check(), store
                                              │       submission + transcript entry
                                              │       (+ exercise_results in révision, 023b)
                                              ▼
                       response → card verdict;  next turn: tutor reads the entry
```

Layering: `domain/answers/` imports only `domain/`. `services/tools/bind.py` and
`services/answers.py` are services. Nothing imports `openai`.

## 3. Components and interfaces

### 3.1 `app/domain/notation.py` (023a, moved, behaviour unchanged)

`NUMBER`, `_decimal_comma`, `_thousands_comma`, `_german_number`, `INTERVAL`, `COORDS` and their
per-language patterns move out of `services/tools/figures.py`; `figures.py` and `plots.py`
import them. `notation_cases.json` (both copies) and the rule tests stay green unchanged.

### 3.2 `app/domain/answers/kinds.py` (023a)

```python
Kind = Literal["choice", "number", "expression", "interval", "set", "point", "word", "mapping"]

class Surd:      a: Fraction; b: Fraction; c: int        # a + b√c, c square-free ≥ 2
class PiLinear:  a: Fraction; b: Fraction                # a + bπ
Exact = Fraction | Surd | PiLinear                       # a zero b normalises to Fraction
class Unit:      dimension: str; factor: Fraction; symbol: str
class Rule:      mode: Literal["exact", "tolerance", "round", "approx"] = "exact"
                 tolerance: Fraction | None = None; round: int | None = None
Form = Literal["unit", "fraction", "reduced", "mixed", "decimal", "scientific", "power",
               "vertex", "factored", "expanded"]
class Quantity:  value: Exact; decimals: int; unit: Unit | None; written: str
class Bound:     value: Exact | None; closed: bool       # None = ±∞, never closed
class Interval:  low: Bound; high: Bound

class ChoiceKey:     option: str; options: tuple[str, ...]
class NumberKey:     quantity: Quantity; rule: Rule; form: Form | None; remainder: Fraction | None
class ExpressionKey: function: GuardedRational; variable: str; form: Form | None
class IntervalKey:   union: tuple[Interval, ...]; rule: Rule
class SetKey:        values: tuple[Exact, ...] | Literal["reals"]; rule: Rule
class PointKey:      coords: tuple[Exact, ...]; rule: Rule
class WordKey:       words: tuple[str, ...]; accents: bool
class MappingKey:    pairs: frozenset[tuple[str, str]]

Basis = Literal["material", "computed", "both"]
Verdict = Literal["correct", "incorrect", "unreadable", "precision", "unit_differs",
                  "form_differs", "form_unchecked", "undecided"]
class Checked: verdict: Verdict; kind: Kind; basis: Basis; expected: str | None; reason: str | None
RECORDABLE = ("correct", "incorrect", "precision", "unit_differs", "form_differs")
```

All frozen dataclasses.

### 3.3 `app/domain/answers/readers.py` (023a)

One reader per kind and language; the same reader parses keys and answers and returns a value or
`None` (unreadable). Normalisation first: NFKC (`ℓ` → `l`), `−`/`–` → `-`, `$…$` stripped,
trailing `.` stripped, a leading `APPROX_WORDS[lang]` (`≈`, `~`, « rund », « ca. », « etwa » and
equivalents) stripped and noted (no effect under an `exact` key).

| Kind | Accepts (de shown) | Notes |
| --- | --- | --- |
| number | `374`, `12,5`, `12.500`, `10 000`, `3/4`, `2 1/4`, `0,1̄` / `0,\overline{1}`, `−2`, `12,5 %`, `25 m/s`, `x = 3`, `2√2`, `(3 + √2) cm`, `2π`, `3 + 2π`, `1,15 · 10⁴` / `1,15 · 10^4`, `4 Rest 7`, « nicht definiert » | space grouping only for groups of exactly three digits (so `2 1/4` is mixed); unit via 3.4; leading `<name> =` stripped; written form kept for D13 |
| expression | `2(x+1)`, `2x+2`, `f(x) = x^2`, `x+1 für x ≠ 1`, `x+1; D = ℝ \ {1}` | exact parse (3.6); `DOMAIN_WORDS[lang]` (de « für », fr « pour », en « for », nl « voor ») with `≠` exclusions, or `D = ℝ \ {…}`; other annotations → `undecided` |
| interval | `]2; 5]`, `[3; 4]`, `]−∞; 3[ ∪ ]4; +∞[`, `x > 2`, `L = ]2; 5]` | ∞ never closed; `∞`, `inf`, `unendlich` |
| set | `{−1; 3}`, `L = {1 − √7; 1 + √7}`, `x = −1 oder x = 3`, `x₁ = −1; x₂ = 3`, `x₁ = −1,5, x₂ = 0,5`, `x = ±3`, `{}` / `∅` / `L = { }`, « keine Lösung », `L = ℝ` | `SET_SEPARATOR`, `JOINERS`, `NO_SOLUTION` per language |
| point | `P(2 \| −1,5)`, `(2 \| −1,5)`, `(2; −1,5)`; en `(2, −1.5)` | `COORDS[lang]` + value reader |
| word | any text | casefold, collapse spaces; accents stripped unless `accents` |
| choice | `B`, `b)`, `Antwort B`, `(b)`, `richtig` / `falsch` | id among the key's `options`; `TRUE_FALSE[lang]`; a reason after it ignored |
| mapping | `A–2, B–1`, `A2 B1`, `A → 2; B → 1` | pairs, any order |

### 3.4 `app/domain/answers/units.py` (023a)

`UNITS` maps aliases to (dimension, exact factor to SI): mm, cm, dm, m, km; mg, g, kg, t; s, min,
h, d; m/s, km/h (5/18); mL, cL, dL, L, cm³, dm³, m³; mm², cm², dm², m², km², a, ha; `%` (1/100,
dimensionless); €, ct (1/100); °C (no conversion). Same dimension → convert the answer exactly
into the key's unit, then apply the rule. Different dimension, an unknown unit differing from the
key's, a missing or extra physical unit → `unit_differs`. `form unit` → the answer's unit must be
the key's written unit, else `form_differs`.

### 3.5 `app/domain/answers/check.py` (023a)

`check(key, answer, language, basis) -> Checked`, never raises on student input (fuzz test).

- number: read, units, rule (D11), form (D13), `remainder` compares both parts; surds and π forms
  exactly; under `round`/`approx` an irrational answer or key is rounded via certified bounds
  (3.6), else `undecided`.
- expression: both to `GuardedRational`; outside the class → `undecided` (`expression_class`);
  domains equal (3.6) else `undecided` (`domain`); then `n₁·d₂ == n₂·d₁` → `correct`
  (`form_unchecked` if the key has an expression form) or `incorrect`.
- interval, set, point: normalised, compared under the rule; set duplicates ignored.
- word, choice, mapping: as in 3.3.

### 3.6 `app/domain/answers/algebra.py` (023a)

- **Exact parse.** `domain/expression.py` gains an exact mode (`parse(…, exact=True)`): its `num`
  nodes keep the lexeme (`atom()` today returns `float(t.text)`); the default mode and the plotting
  pins are unchanged. `:` and `÷` are division, `√(…)` and `π` are accepted in exact mode only.
- **`GuardedRational`**: numerator and denominator polynomials over `Fraction`, plus the nonzero
  guards of every division and negative power in the original tree; simplification never removes
  a guard; an identically zero divisor → `undecided`.
- **Domain equality.** Exclusions = real roots of the square-free product of the guard polynomials,
  minus/plus a stated annotation (which may only intersect, never widen). Two exclusion sets are
  equal when proven by exact gcd and Sturm counts; anything unproven → `undecided`.
- **Roots.** Rational root theorem for rational roots (coefficients ≤ 10⁶); remaining quadratic
  factors give exact surds; other real roots are isolated by Sturm sequences into disjoint rational
  intervals. The root count is proven before and after isolation. Multiplicities are kept for
  inequality signs.
- **Certified rounding.** An isolated algebraic root is bisected until its interval excludes the
  rounding boundary; if the boundary itself is a root (exact substitution) it is rational and is
  rounded exactly. π uses the rational bounds 3.14159265358979323846264338327 ± 10⁻²⁹; a rounding
  is certified when both bounds round alike.
- **Limits** (exceeding any → `undecided`): expression degree ≤ 24, ≤ 64 coefficients, each
  coefficient's numerator and denominator ≤ 10¹²; solve degree ≤ 4; ≤ 200 bisection steps per
  root; 50 ms wall time per `check` call.

### 3.7 `app/domain/answers/variants.py` (023a)

```python
class Evaluate: expression: str; variable: str; at: str    # `at` in course notation
class Solve:    relation: str; variable: str               # = < > ≤ ≥ (<=, >=)
def task_key(task, kind, rule, language) -> Key | NotCheckable
def task_statement(task, rule, language) -> str           # the statement the card shows
```

- Evaluate: exact class at an exact point → exact `NumberKey`; `√` and `π` forms exactly; anything
  else only with `round d` and a certified rounding; division by zero → `undefined`.
- Solve: `left − right` as a `GuardedRational`: constant denominator → polynomial of degree 1–4;
  variable in a denominator → `=` only, roots minus guard roots; `x^n = c` → exact roots when `c`
  is an exact n-th power or n = ±2 (surds), else approximate. `=` → `SetKey` (a `number` kind only
  for exactly one root); inequalities → `IntervalKey` from exact sign tests between roots.
  Approximate roots need `round d` and certified rounding.
- Reasons: `not_polynomial`, `degree`, `variables`, `parse`, `kind_mismatch`, `no_unique_number`,
  `irrational`, `boundary`, `undefined`, `size`.

### 3.8 Keys in the pack: `app/domain/answers/keys.py` (023a)

```
**<KEY_LABEL>[ <sub>[ <part>]]:** <kind> <key>[ <rule>][ form <form>][ | <task>]
```

- `KEY_LABEL` = fr « Clé », en « Key », nl « Sleutel », de « Schlüssel ».
- `<key>` may start with `≈` → rule `approx`. `<rule>`: `round <d>` or `±<t>`. word: alternatives
  ` / `, `accents`; choice: `of <ids>` (`of richtig falsch`). `<task>`: `solve <relation>` or
  `eval <expression> at <variable> = <value>`.
- Examples (de): `**Schlüssel:** number 374` · `**Schlüssel c):** number ≈ 3,84 cm` ·
  `**Schlüssel:** number 300 dm² form unit` · `**Schlüssel b):** set {2; 3} | solve x^2 - 5x + 6 = 0` ·
  `**Schlüssel a) u:** number ≈ 51,05 mm` · `**Schlüssel:** choice B of A B C D` ·
  `**Schlüssel:** mapping A–2, B–1, C–3`.

```python
ExerciseRef = str     # "6.1.2", "6.1.2 a)", "6.1.2 a) u"
class PackKey: key: Key; task: Task | None; status: Literal["material", "agrees", "needs_review"]
def pack_keys(markdown, language) -> tuple[dict[ExerciseRef, PackKey], list[ContentIssue]]
def exercise_statement(markdown, ref, language) -> str | None
```

- Read in the `index_pack` walk (fences skipped, exercises section only). Issues:
  `pack.key_outside`, `pack.key_duplicate`, `pack.key_kind`, `pack.key_unreadable`,
  `pack.key_task` (malformed), `pack.key_class` (expression outside the class); catalog keys in
  four languages. A well-formed task over the limits is not an issue and proves nothing (D7).
- `exercise_statement`: the lines under the heading up to the first `ANSWER_LABEL[lang]` or
  `KEY_LABEL[lang]` line; for a sub-question, the stem before the first sub-item plus that
  sub-item; `None` when the cut is not found, or with a figure mark or `MEASURE_WORDS[lang]`.
- `PackIndex.keys: frozenset[ExerciseRef]`. The pack view API (`GET …/pack`) gains
  `keys: [{ref, status}]`.

### 3.9 Binding: `app/services/tools/bind.py` (023a)

```python
class CheckSpec(BaseModel):     # optional `check` on ExerciseCard and CheckQuestionCard
    exercise: Annotated[str, Field(max_length=24)] | None      # pack ref
    task: TaskArgs | None                                       # variant
class TaskArgs(BaseModel):
    kind: Kind; solve: str | None; evaluate: str | None; at: str | None
    variable: Annotated[str, Field(pattern=r"^[a-z]$")]
    round: Annotated[int, Field(ge=-3, le=6)] | None
```

`display_board` calls `bind(card, ctx)` for each card with `check`:

1. Exactly one of `exercise`/`task`; `check_question` only with an `exercise` whose key is `choice`.
2. Pack: the ref is in the chapter's keys (révision: of the section's chapter); status not
   `needs_review` for binding an answer field (a `needs_review` card is shown with its notice and no
   field); `exercise_statement` cuts. Variant: `task_key` succeeds.
3. Success: the server rewrites the card (pack → `statement`/`question` := the cut statement,
   choice options := the key's ids; variant → `statement` := `task_statement`, the model's
   statement dropped) and creates a pending presentation `{id: uuid4 hex, binding, status}`; the
   card carries `exercise_id`, `status` and no key.
4. Failure: the card is shown unbound; the tool output says why in the course language
   (« … ist nicht prüfbar: … Begleite ohne Urteil. »). Never a tool error.
5. Voice: `/api/voice/tool` never binds (`check` is ignored there).

Declarations: `ExerciseCard` and `CheckQuestionCard` gain `check`; `CheckQuestionCard`'s
declaration model has no `correct_option_id`/`feedback` (D9). The server-set fields
(`exercise_id`, `status`) are not in any declaration. `board_declarations.json` is regenerated and
its diff reviewed. Reading stored or reported cards uses a lenient model that drops the legacy
fields and every server-set field a browser sends.

### 3.10 Presentations and `turn.stored` (023a)

Table `exercise_presentations` (migration 0015):

| Column | |
| --- | --- |
| `id` String(32) PK | opaque uuid4 hex |
| `user_id`, `course_id`, `chapter_id` | FK, `ON DELETE CASCADE` |
| `section_id` String(40) | the section the card was shown in (parcours), or the révision section |
| `mode` | `parcours` \| `revision`, check constraint |
| `content_version` int | the chapter's version at presentation |
| `conversation_id` | FK `SET NULL`: the row the card was stored in; for révision, the run |
| `binding` JSON | `{exercise: ref}` or `{task, kind, rule}`, never a key |
| `status` | `material` \| `agrees` \| `computed` |
| `created_at` | |

- Written in the **same transaction** as the turn's entries: `conversations.store_seance(…,
  presentations=)` for the parcours, `conversations.append(…, presentations=)` for révision, like
  `results`. A failed store writes neither.
- **Eligibility** at submission: owner matches; chapter's current content version equals
  `content_version`; parcours: the learner's live séance is for `section_id` (rollover and return
  to the section are fine); révision: `conversation_id` is the open révision run (not `capped`,
  not replaced). Content change, reset and deletion end eligibility (rows cascade on deletion).
- **`turn.stored`**: the store hook returns what it stored; the SSE controller sends
  `turn.stored {exercise_ids: [...], message_id: str | null}` after a successful `on_complete` and
  before `turn.end`. `exercise_ids` lists only presentations eligible right after the store (a
  révision run capped by this very turn lists none; its cards show « Diese Wiederholung ist voll »).
  A failed store sends no `turn.stored` (`turn.end` still follows, as today). `message_id` is null
  until 023c.
- **Reported turns** (`seance/report`, stopped parcours turns): cards are stored as reported, with
  server-set fields stripped; no presentation is ever created from a report.
- **Reload**: the séance and révision read endpoints return, per stored card, whether its
  presentation is eligible now (`exercise_id` + `eligible` + reason), so the client enables fields
  without trusting stored card JSON.

### 3.11 Submission: `POST /api/answers` and `app/services/answers.py` (023a)

Request `{exercise_id, answer (1–200 chars), source: "card" | "choice", request_id (≤ 64)}`
(023c adds `"chat"`; `"voice"` → 422). Response `{submission_id, exercise_id, verdict, basis,
expected?, reason?}`, never a key.

1. Resolve the presentation for the authenticated student; refuse unknown, foreign, ineligible
   (`409 exercise_unavailable` with the reason) or wrong mode.
2. Idempotency: table `answer_submissions` (migration 0015) `(id, user_id, presentation_id FK
   CASCADE, request_id, source, answer, verdict, basis, reason, created_at)`, unique
   `(user_id, request_id)`. Same request id + same payload → the stored response; different payload
   → `409 request_conflict`.
3. Key from the presentation's binding (pack key of the current content version, or `task_key`),
   then `check()` in a worker thread with its time limit.
4. One transaction: insert the submission and append a `submission` transcript entry
   `{kind: "submission", submission_id, exercise_id, answer, verdict, basis, reason}` to the
   learner's live séance (parcours) or the révision run, under the conversation's optimistic guard;
   a concurrent turn → `409 conversation_busy`, the client retries the same request id. (023b: the
   same transaction inserts `exercise_results` for a recordable révision verdict.)
5. After the response the client starts a tutor turn without a learner message (`message: null`
   is accepted when the last stored entry is a submission, as for an opening turn); the model input
   renders the entry in the course language: « Antwort zu 6.1.2 a): „…“ — Prüfer: stimmt mit der
   Lösung in deinem Material überein. » A failed tutor turn leaves the submission and verdict stored.

No model tool can create, change or check a submission. Parcours verdicts never reach révision
tables.

### 3.12 Tutor prompt and mode layers (023a; 023c for `propose_answer`)

- `tutor.<lang>.md` (4 files): bind checkable exercises with `check`; say verdicts only from a
  submission entry, with its source; never « richtig »/« falsch » from own judgment; guide without
  a verdict otherwise. The card's verdict line is the authoritative one.
- `modes/revision.<lang>.md`: after a checked submission, still show the course's wording and ask
  for the self-assessment (spec 020 D3). `modes/parcours.<lang>.md`: one line on keyed exercises.
- Measured by `scripts/probe.py --checker` per language; its metric (semantic judgment, denominator,
  threshold) is fixed when the probes are written (`decisions.md` §14.3).
- Pins regenerated deliberately (`system_text_sha*`, declarations).

### 3.13 Authoring (023a)

- Templates (4 subjects × 4 languages): the §6 comment gains the key rule and the examples of 3.8.
- `prompts/authoring/pack.<lang>.md`: copy, never compute; rules only as requirements §1.3; tasks
  only in the two forms; textbook references in headings (`#### 6.1.2 (S. 128, Nr. 11)`), appendix
  solutions joined by page, number and letter, answer pools never keys or statements, figure marks
  kept, explicit review labels kept (023b reads them).
- Repair: key issues repaired like other issues (bounded); left-over key issues → the runner drops
  those lines and appends one §7 item each (`DROPPED_KEY[lang]`). `needs_review` is not an issue.
  `authoring_stage` logs `keys`, `keys_dropped`, `keys_needs_review`.
- Pack editor (`PUT …/pack`): the same `index_pack`; key issues are `422 content_invalid`.

### 3.14 Chapters and caches (023a)

`LessonChapter.keys` and `RevisionChapter.keys: Mapping[ExerciseRef, PackKey]`, parsed with the
curriculum by `CurriculumCache` per (chapter id, content version), task recomputation included.

### 3.15 Frontend (023a unless marked)

- `types.ts`: `Verdict`, `Basis`, submission request/response, `turn.stored` event, card fields
  `exercise_id`, `status`, `eligible`; `CheckQuestionCard` without `correct_option_id`/`feedback`
  (old JSON still parses, extra fields ignored).
- `ExerciseBoard`: the statement as sent; for a bound card an answer field, disabled until
  `turn.stored` lists its id (or the read endpoint says `eligible`); submit → `POST /api/answers`,
  then the tutor turn; the verdict line with its source (`board_verdict_<verdict>_<basis>`), the
  `needs_review`, `undecided` and « révision full » notes.
- `CheckQuestionBoard`, **every mode** (parcours, discussion, révision, notebook): a pick on an
  unbound card is sent as today, uncoloured, without feedback; on a bound card it is a submission
  with `source: "choice"` and shows the checker's verdict.
- Reducer (`use-tutor-session.ts`): `turn.stored` enables fields; a submission response sets the
  verdict of the card with that `exercise_id` (any board of the séance); `sessionFromEntries`
  replays submission entries onto their cards.
- Pack view: « prüfbar » / « Lösung prüfen » badges from `keys`.
- Catalog keys in four languages for every new text; keyboard and screen-reader paths.
- 023b: Bilan list of checked exercises; label correction. 023c: candidate confirmation chip.

### 3.16 Révision record and labels (023b)

- `exercise_results` (migration in 023b): submission id (unique), owner, course, chapter, section,
  conversation (`SET NULL`), exercise ref or variant task, kind, verdict (`RECORDABLE`), basis,
  content version, created_at; inserted in the submission transaction for révision submissions
  made after 023b ships; no backfill. Reads at the current content version.
- Bilan and state message: per section, the self-assessment as today and the checked exercises
  (ref or task, verdict, source, date), review-labelled ones apart.
- Labels: the pack's explicit label (key-line or heading syntax fixed in 023b); a per-exercise
  override outside the pack. Version and deletion rules of overrides and results are decided when
  023b is planned (`decisions.md` §14.2 holds the recommendation).

### 3.17 Chat candidates (023c)

- The chat and révision turn routes give the learner entry a server `message_id` at turn start
  (`LearnerEntry.id`, optional for old entries); `turn.stored` returns it.
- `propose_answer(exercise_id)` (appended tool, parcours and révision): refers to the running
  turn's learner message; stored as a tool entry with the turn; the candidate text is that
  message's text, never model text; the chip becomes active with `turn.stored`. A turn that is not
  stored leaves no proposal; old entries without an id get none.
- The student confirms or corrects answer and exercise; confirmation posts `source: "chat"` with
  the corrected text.

## 4. Data models

| Where | Stage | Change |
| --- | --- | --- |
| `exercise_presentations` | 023a | new table (3.10) |
| `answer_submissions` | 023a | new table (3.11) |
| Transcript entries | 023a | `submission` entry; cards with `exercise_id`, `status`; 023c: `LearnerEntry.id` |
| `ExerciseCard`, `CheckQuestionCard` | 023a | `check`; choice declaration without legacy fields; lenient reading model |
| `PackIndex`, `LessonChapter`, `RevisionChapter` | 023a | `keys` |
| SSE | 023a | `turn.stored` |
| API | 023a | `POST /api/answers`; séance/révision reads gain per-card eligibility; pack view `keys` |
| `exercise_results`, label overrides | 023b | 3.16 |

## 5. Error handling

- Binding failures leave a card unbound with a reason, never a tool error.
- A failed store sends no `turn.stored`; nothing becomes checkable.
- Submission refusals: `404` unknown, `403` foreign, `409 exercise_unavailable` (reason),
  `409 request_conflict`, `409 conversation_busy` (retry), `422` invalid body or `voice`.
- Unreadable → example of the expected form; `undecided` (incl. limits, checker exception logged
  `check_failed`) → no verdict, guidance; `needs_review` → no verdict, notice without the key.
- A failed tutor turn after a submission leaves the stored verdict intact.
- Old stored cards and entries stay readable; legacy choice fields are ignored.

## 6. Testing strategy (023a; 023b/c extend it)

- **Case tables** `answer_cases.json` per kind × language: exactness (`5`/`5,0`/`5,4`), rules
  (`≈ 3,84 cm` vs `3,8`/`3,84`/`3,842 cm`, `round -1`, `±t`), vague rounding → undecided, exact units
  (`90 km/h`/`25 m/s`, `3 m²` vs `300 dm²` with `form unit`), mixed numbers vs grouping (`2 1/4`),
  repeating decimals, surds, π forms, `4 Rest 7`, set forms, unions, ∞, domain annotations,
  unreadable and undecided inputs. Expected values computed independently.
- `test_algebra.py`: guards survive cancellation (`x/x` vs `1` → undecided), equal real domains
  with different guards, Sturm counts and isolation, repeated and close roots, certified rounding at
  ties, π bounds, every limit → undecided; exact parse leaves the plotting parser's pins unchanged.
- `test_variants.py`, `test_pack_keys.py` (keys per language, statement cut never includes answer or
  key lines, figure marks, `agrees`/`needs_review`/inconclusive), `test_issue_messages.py`.
- `test_bind.py`: pack and variant binding, statement replaced or generated, unbound reasons,
  voice never binds, reported cards stripped.
- Store and `turn.stored`: presentations written with the turn in both stores; failed store → no
  event and no rows; capped révision in the same turn → stored but not listed; reload eligibility.
- `test_answers_route.py`: ownership, eligibility (rollover, section return, content change,
  reset, closed révision), idempotency (same/different payload, concurrent requests), busy retry,
  transcript entry and next-turn rendering, failed tutor turn keeps the verdict, `voice` refused.
- Registry and pins: `board_declarations.json` diff reviewed (choice fields gone, `check` added);
  `path_declarations` unchanged; `system_text_sha*` regenerated.
- Frontend: field activation only by `turn.stored`/`eligible`, submission flow, verdict line and
  notes, choice cards uncoloured in every mode including notebook and old cards, replay of
  submission entries, language sweeps.
- Real-model probes (not in pytest, cost money): run and recorded separately.

## 7. Performance

No model call for a verdict; `check` bounded by 3.6's limits and a 50 ms budget; keys parsed once
per content version; presentation lookup by primary key.

## 8. Security and privacy

Ownership, mode, content version and run checked server-side on every submission; ids are opaque
and never authority. The model cannot create a presentation outside `display_board`'s binding,
submit, or see a key in a tool output; a browser cannot bind a card (reports are stripped). No
evaluation of model or student text beyond the closed grammar. Answers stored only in submissions
and the transcript; logs carry ids, kind, verdict, basis and reasons, never answers or keys. The
tutor's pack may hold solutions; free prose is governed by the prompt and measured by probes, the
card's verdict is authoritative.

## 9. Monitoring and observability

- `exercise_bound` / `exercise_unbound` (ids, mode, status or reason); `turn_stored` (ids count).
- `answer_checked` (ids, kind, verdict, basis, ms) / `answer_refused` (reason).
- `authoring_stage`: `keys`, `keys_dropped`, `keys_needs_review`.

## 10. Before planning each stage

- **023a**: plan now. Exact names of routes, entries and events may be adjusted in the plan if the
  code suggests better ones; the contracts above stand.
- **023b**: decide label syntax, override and result lifecycle (`decisions.md` §14.2).
- **023c**: confirm the message-id change in both turn routes.
- **Probes**: fix the metric when written (`decisions.md` §14.3).
- Spec 022's contract stays deferred until that spec is resumed.

## Appendix A. Input for the later voice spec (not part of spec 023)

The trusted `/api/voice/tool` `display_board` path would validate and persist the presentation and
the authoritative card before returning a checkable card and id, associated with the
authenticated server-owned voice session and the chapter, section, version and transcript order.
A later `/api/seance/report` would reconcile the same server-issued card id, keeping spoken order
and partial stopped turns without duplicating or overwriting the authoritative card; a client
report could never create or alter a checkable presentation. If storage or association fails, the
card is not checkable.
