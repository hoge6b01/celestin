# Spec 023 — Answer checker: design

Requirements: `requirements.md` (with the owner's decisions in §6). Builds on specs 005 (pack),
009 (expression grammar), 011/017/021 (course languages), 018 (stored tool entries), 020
(révision record). The implementation branch must start from a branch that has spec 021's code
(German rows): every per-language table below has an `fr`, `en`, `nl` and `de` row.

## 1. Overview

Three pieces, all deterministic, no model call:

1. **Keys in the pack.** Each typical exercise (pack §6) whose material gives a solution carries
   one key line per answer: `**Schlüssel:** number 374`. The authoring agent copies it from the
   solution; `index_pack` validates it with the same readers that read student answers.
2. **`app/domain/answers/`**: readers per answer kind and course language, a unit table, the
   comparison, and variant keys computed by code (evaluation; real roots of a polynomial).
3. **`check_answer`**, the eighth tool, declared last, offered in parcours and révision. It
   checks that the answer is in the student's latest message, settles it against a pack key or a
   variant, returns the verdict to the model (never the key) and emits `answer.checked`; the board
   marks the latest exercise card. In révision the verdict is written to `revision_results` with
   `source = 'checker'`.

### Decisions beyond the requirements (flag to the owner)

- **D1. The key never appears in the tool output**, not even after a correct answer or a reveal
  (narrows R3.5): a correct answer is the key already; a reveal stays the tutor's existing
  step-by-step reveal. Removes a leak path.
- **D2. `check_question` cards are unchanged** (defers R4.3): their `correct_option_id` is the
  model's word, so by R3 it is not a key. A pack exercise with a `choice` key is set as an
  `exercise` card listing its options, and the student's choice goes through `check_answer`.
  Changing the card would move the pinned board declarations for no gain in this spec.
- **D3. Variants are computed, not only substituted** (refines §1.2): an equation or inequality
  variant is accepted only if it is a polynomial in one variable of degree ≤ 4; the code computes
  its real solutions (then checks them by substitution). This settles « all solutions found »
  without trusting a solution count from the model. Non-polynomial relations are not checkable.
- **D4. One variable** per expression or relation (the grammar's `evaluate(node, value)`).
  Several variables are not checkable in this spec.

## 2. Architecture

```
 pack.md (§6 exercise)                    learner message (parcours / révision turn,
  **Schlüssel a):** interval ]2 ; 5]        voice: VoiceToolRequest.learner_text)
        │                                              │
        ▼                                              ▼
 domain/pack.py index_pack ──► domain/answers/keys.py  TurnContext.learner_text
   (validates keys, issues)     pack_keys(md, lang)          │
        │                           │                        │
        ▼                           ▼                        ▼
 chapters.py LessonChapter.keys ── cached per content version ──► services/tools/check.py
 revision.py RevisionChapter.keys                                  check_answer(args, ctx)
                                                                    │  answer ∈ learner_text?
                                                                    │  key = pack key | variant
                                                                    ▼
                                              domain/answers/check.py check(key, answer, lang)
                                                (readers.py, units.py, variants.py, expression.py)
                                                                    │ Verdict
                         ┌──────────────────────────────────────────┼────────────────────┐
                         ▼                                          ▼                    ▼
              tool output (course language,              SSE answer.checked      révision: turn_results
              verdict words, never the key)              {verdict, kind,          → revision_results
                                                          exercise, marker}         source='checker'
                                                                    │
                                                    frontend reducer: status of the
                                                    latest exercise board (correct/wrong)
```

Layering: `domain/answers/` imports only `domain/` (`expression.py`, `language.py`,
`notation.py`). `services/tools/check.py` is the tool. Nothing imports `openai`.

## 3. Components and interfaces

### 3.1 `app/domain/notation.py` (moved, behaviour unchanged)

The number, interval and coordinate readers move out of `services/tools/figures.py` so `domain/`
can use them: `NUMBER`, `_decimal_comma`, `_thousands_comma`, `_german_number`, `INTERVAL`,
`COORDS` and their per-language patterns. `figures.py` and `plots.py` import them from here.
`notation_cases.json` (both copies) and every rule test stay green unchanged: a pure move.

### 3.2 `app/domain/answers/kinds.py`

```python
Kind = Literal["choice", "number", "expression", "interval", "set", "point", "word"]
KINDS: tuple[Kind, ...]

@dataclass(frozen=True) class Unit:        dimension: str; factor: float; symbol: str
@dataclass(frozen=True) class Quantity:    value: Fraction | float; decimals: int | None; unit: Unit | None
@dataclass(frozen=True) class Bound:       value: float; closed: bool          # ±inf never closed
@dataclass(frozen=True) class Interval:    low: Bound; high: Bound

@dataclass(frozen=True) class ChoiceKey:     option: str
@dataclass(frozen=True) class NumberKey:     quantity: Quantity; tolerance: float | None   # explicit ±
@dataclass(frozen=True) class ExpressionKey: source: str; variable: str; domain: Interval
@dataclass(frozen=True) class IntervalKey:   union: tuple[Interval, ...]
@dataclass(frozen=True) class SetKey:        values: tuple[float, ...]       # sorted, distinct
@dataclass(frozen=True) class PointKey:      coords: tuple[float, ...]
@dataclass(frozen=True) class WordKey:       words: tuple[str, ...]; accents: bool
Key = ChoiceKey | NumberKey | ExpressionKey | IntervalKey | SetKey | PointKey | WordKey

Verdict = Literal["correct", "incorrect", "unreadable", "precision", "unit_differs"]
@dataclass(frozen=True) class Checked:  verdict: Verdict; kind: Kind; expected: str | None
    # `expected`: for `unreadable`, an example of the expected form in the course's notation
```

### 3.3 `app/domain/answers/readers.py`

One reader per kind, per course language (`by_language` tables). The same reader parses a key and
a student's answer. Each returns a value or `None` (unreadable).

| Kind | Accepts (de shown; fr/nl like de with `;`, en with `,` and `.`) | Notes |
| --- | --- | --- |
| number | `374`, `12,5`, `12.500`, `10 000`, `3/4`, `−2`, `12,5 %`, `25 m/s`, `x = 3` | `NUMBER[lang]`; `a/b` exact `Fraction`; trailing unit via `units.py`; leading `<name> =` stripped |
| expression | `2(x+1)`, `2x+2`, `f(x) = x^2` | `expression.parse(src, frozenset({variable}))`; leading `f(x) =`/`y =` stripped; decimal comma → point for the course languages with a comma (`1,5x`) |
| interval | `]2 ; 5]`, `[−∞ ; 3[` refused (∞ never closed), `]−∞ ; 3[ ∪ ]4 ; +∞[`, `x > 2` (one-sided only), `L = ]2 ; 5]` | value reader built beside `INTERVAL[lang]`; `∞`, `inf`, `unendlich` |
| set | `{−1; 3}`, `L = {−1; 3}`, `x = −1 oder x = 3`, `x₁ = −1; x₂ = 3`, `{}` / `∅` / `L = { }` (empty) | separators `SET_SEPARATOR[lang]`, joiners `JOINERS[lang]` (de: `oder`, `und`; fr: `ou`, `et`; nl: `of`, `en`; en: `or`, `and`) |
| point | `P(2 \| −1,5)`, `(2 \| −1,5)`, `(2; −1,5)` (de); `(2, −1.5)` (en) | `COORDS[lang]` plus a value reader; leading name stripped |
| word | any text | NFKC, casefold, collapse spaces; accents stripped unless the key says `accents` |
| choice | `B`, `b)`, `Antwort B`, `(b)` | one option id, case-insensitive |

Normalisation before every reader: NFKC, `−`/`–` → `-`, `·`/`×` kept for expressions, surrounding
`$…$` stripped (`text.MATH`), trailing `.` stripped.

### 3.4 `app/domain/answers/units.py`

`UNITS: dict[str, Unit]`, aliases to `(dimension, factor to SI)`:

- length: mm, cm, dm, m, km; mass: mg, g, kg, t; time: s, min, h; speed: m/s, km/h (`m·s^-1`,
  `km·h^-1`, `m/s`, `km/h`); volume: mL/ml, cL/cl, dL/dl, L/l, cm³, dm³, m³ (`cm^3`); area: mm², cm²,
  dm², m², km², a, ha; percent: `%` (dimensionless, factor 0.01).
- Same dimension → compare in SI. Different dimension, or a unit outside the table that differs
  from the key's written unit → `unit_differs`.
- Key with a physical unit, answer without one → `unit_differs` (the course expects the unit).
  Key without a unit, answer with a physical unit → `unit_differs`.
- `%` is dimensionless with factor 0.01: `12,5 %` and `0,125` are equal in either direction.

### 3.5 `app/domain/answers/check.py`

```python
def check(key: Key, answer: str, language: CourseLanguage) -> Checked
```

- **number**: read; unit handling (3.4); explicit `tolerance` → `|a−k| ≤ tol`; else key decimals
  `d` (from the key as written; `Fraction` keys and computed keys: see variants) → answer must
  have `≥ d` decimals and `round(a, d) == round(k, d)` (half away from zero) → correct; fewer
  decimals and equal at the answer's precision → `precision`; else incorrect. Integer key: `d = 0`,
  `5,0` equals `5`. Fractions: `3/4` equals `0,75` (exact compare when both exact).
- **expression**: parse both; 12 fixed sample points spread over `domain` (default `[−10 ; 10]`),
  irrational offsets (`k·0.7071 + 0.3183`, clipped into the domain); skip points where either is
  NaN; need ≥ 6 shared defined points and the same definedness at every point; equal if
  `|a−b| ≤ 1e−9·max(1, |a|, |b|)` everywhere.
- **interval**: union normalised (sorted, merged); equal bounds (`1e−9`) and equal closedness.
- **set**: same size, pairwise equal sorted (`1e−9`); duplicates in the answer ignored.
- **point**: same dimension, coordinates equal (`1e−9`, or decimals as for numbers when the key
  has decimals).
- **word**: normalised answer equals one of `words`.
- **choice**: equal ids, case-insensitive.

### 3.6 `app/domain/answers/variants.py`

```python
@dataclass(frozen=True) class Evaluate: expression: str; variable: str; at: str   # `at` in course notation
@dataclass(frozen=True) class Relation: relation: str; variable: str             # one of = < > ≤ ≥ (<=, >=)

def variant_key(variant: Evaluate | Relation, kind: Kind, language) -> Key | NotCheckable
```

- `Evaluate` → `NumberKey` from `evaluate(parse(expression), number(at))`; decimals: exact
  integer → 0; terminating decimal → its digits (≤ 6); otherwise `None`, and `check` accepts an
  answer with `≥ 2` decimals that rounds to the value at its own decimals, or the exact fraction
  when the evaluation is rational.
- `Relation` → split on the single top-level relational operator; `left − right` must be a
  polynomial in `variable` of degree 1–4 (`polynomial.py`: coefficient expansion over the AST: `+`,
  `−`, `×`, `^` with a non-negative integer literal, no function, no division by an expression
  containing the variable). Real roots: closed form for degree ≤ 2, Durand–Kerner then Newton
  polish for 3–4, imaginary parts `< 1e−9` dropped, roots verified by substitution.
  - `=` → `SetKey(roots)`; with `kind == "number"` only when exactly one real root.
  - `<`, `>`, `≤`, `≥` → `IntervalKey` from the sign of the polynomial between roots.
- Anything else → `NotCheckable(reason)`: `not_polynomial`, `degree`, `variables`, `parse`,
  `kind_mismatch`, `no_unique_number`.

### 3.7 Keys in the pack: `app/domain/answers/keys.py`

Line form, under an exercise's `#### N.M.K` heading, after its answer line:

```
**<KEY_LABEL>[ <sub>]:** <kind> <key in the course's notation>[ <modifier>]
```

- `KEY_LABEL = by_language(fr="Clé", en="Key", nl="Sleutel", de="Schlüssel")`.
- `<sub>`: a sub-question label, `a)`, `b)`, `1)`, …; absent for a single answer.
- `<kind>`: the fixed identifiers of `KINDS` (language-neutral; the model never says them aloud).
- Modifiers: number `±<tol>`; expression `in <interval>` (domain) and the variable first:
  `expression x 2(x+1)`; word alternatives separated by ` / `, `accents` flag; choice: the option
  id.
- Examples (de): `**Schlüssel:** number 374` · `**Schlüssel:** number 25 m/s` ·
  `**Schlüssel a):** interval ]2 ; 5]` · `**Schlüssel b):** set {−1; 3}` ·
  `**Schlüssel:** point P(2 | −1,5)` · `**Schlüssel:** expression x 2(x+1)` ·
  `**Schlüssel:** word Hypotenuse` · `**Schlüssel:** choice B`.

```python
ExerciseRef = str   # "6.1.2" or "6.1.2 a)"
def pack_keys(markdown: str, language: CourseLanguage) -> tuple[dict[ExerciseRef, Key], list[ContentIssue]]
```

- Read in the same walk as `index_pack` (fences skipped, only under the exercises section); a key
  line outside an exercise, a duplicate ref, an unknown kind or an unreadable key is a
  `ContentIssue` with codes `pack.key_outside`, `pack.key_duplicate`, `pack.key_kind`,
  `pack.key_unreadable` (catalog keys in fr/en/nl/de, `render_issue`).
- `index_pack` calls it and returns the issues with its own; `PackIndex` gains
  `keys: frozenset[ExerciseRef]`.

### 3.8 Authoring

- Templates `templates/<subject>.pack.<lang>.md` (4 subjects × 4 languages): the §6 comment gains
  the key rule (one line per answer, from the solution only, not for « not corrected » or for an
  answer listed in §7, not for kinds outside the list) with the examples of 3.7.
- `prompts/authoring/pack.<lang>.md`: the same rule in the agent's words; « copy, never compute ».
- Repair: key issues are repaired like other pack issues (bounded attempts). If the last attempt
  still has only key issues, the runner drops those key lines and appends one §7 item per dropped
  key (`DROPPED_KEY[lang]`: « 6.1.2 a): Lösung nicht als Schlüssel lesbar »), then accepts the pack.
  `authoring_stage` logs `keys`, `keys_dropped`.
- Packs stored before this spec: no key lines, `keys = {}`; nothing re-authored.
- Pack editor (`PUT …/pack`): same `index_pack`, so key issues are 422 `content_invalid` with
  their messages, like any pack issue.

### 3.9 Chapters and révision scope

- `LessonChapter.keys: Mapping[ExerciseRef, Key]`, parsed by `CurriculumCache` per (chapter id,
  content version) beside the curriculum.
- `RevisionChapter.keys`, from the same cache when the scope is built.

### 3.10 `TurnContext.learner_text`

- New field `learner_text: str | None = None`: the learner message of this turn, set by the
  parcours chat route and the révision turn route (`payload.message`); `None` on an opening turn
  and in discussion.
- Voice: `VoiceToolRequest.learner_text: str ≤ 2000 = ""`, the latest user transcript the
  browser's Realtime bridge holds; `/api/voice/tool` puts it on the context.
- `answers/normalise.py: contains(learner_text, answer) -> bool`: both normalised (3.3), spaces
  removed, casefolded; substring test.

### 3.11 The tool: `app/services/tools/check.py`

```python
class VariantArgs(BaseModel):            # strict: every field present, nullable where optional
    expression: str | None               # Evaluate
    at: str | None
    relation: str | None                 # Relation
    variable: Annotated[str, Field(pattern=r"^[a-z]$")]

class CheckAnswerArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: Annotated[str, Field(min_length=1, max_length=200)]
    kind: Kind
    exercise: Annotated[str, Field(max_length=16)] | None     # "6.1.2" / "6.1.2 a)"
    variant: VariantArgs | None
    chapter: Annotated[int, Field(ge=1, le=999)] | None       # révision: required
    section_id: Annotated[str, Field(max_length=40)] | None   # révision: required

@dataclass(frozen=True)
class AnswerChecked:
    checked: Checked
    exercise: str | None
    chapter_id: str | None
    section_id: str | None
    output: str          # course language, never the key
    marker: Marker       # marker.answer_checked.<verdict>, label = exercise ref or the variant word
```

Order of checks (each refusal is a `ToolValidationError` in the course language, `_WORDS` by
language):

1. exactly one of `exercise` / `variant` (`one_source`);
2. révision: `chapter` and `section_id` present and valid (reuses `result.py`'s words); parcours:
   ignored;
3. `ctx.learner_text` present and `contains(learner_text, answer)` (`not_the_students`: « Prüfe
   nur die Antwort, die dein Gegenüber in der letzten Nachricht geschrieben hat, wörtlich. »);
4. exercise: ref in the chapter's keys (`no_key`: « Für 6.1.2 gibt es keinen Schlüssel: begleite
   ohne Urteil. »), kind equal to the key's kind (`kind_mismatch`);
5. variant: `variant_key` (`not_checkable` with the reason, and « begleite ohne Urteil »);
6. `check(key, answer, language)`.

Output words (`_VERDICT_WORDS`, by language), e.g. de: correct « Vom Prüfer bestätigt: richtig. »;
incorrect « Vom Prüfer: nicht richtig. Verrate die Lösung nicht; arbeite mit Fragen und
Hinweisen weiter. »; unreadable « Nicht als {kind_word} lesbar. Bitte um die Antwort in der Form
{expected}. »; precision « Der Wert stimmt, ist aber nicht genau genug gerundet (Lösung mit
{decimals} Nachkommastellen). »; unit_differs « Die Einheit passt nicht zur Aufgabe. ».

Registry row: `name="check_answer"`, `strict=True`, declared **after `record_result`**;
`replay=replay_check` (the output rebuilt from `entry.verdict`), `shown=shown_check` (marker and
`{verdict, kind, exercise}`), `check=None` (a reported parcours turn may not carry it: voice reports
go through `/api/voice/tool`, which runs it live). `_MODE_TOOLS`: parcours += `check_answer`;
révision += `check_answer`; discussion unchanged. Description (French, as all declarations):
« Fais vérifier par le code la réponse finale de ton élève… ».

### 3.12 Events, stored entries, history

- SSE event `answer.checked`: `{verdict, kind, exercise: str | null, chapter_id: str | null,
  section_id: str | null, marker}`. Added to `api/schemas` events, `tool_events.event_of`,
  `frontend/src/lib/tutor/types.ts` `TutorEvent`, and to the design of spec 001 §3.2's list.
- `ToolEntry` gains `verdict: Verdict | None` (only on a `check_answer` entry; the validator
  `_recorded_on_their_tool_only` extended) and reuses `chapter_id`. Never sent to the model.
- `history.to_provider_input` replays the stored output via `replay_check`.

### 3.13 Révision record

- Migration `0015_result_source`: `revision_results.source` String(8) NOT NULL default `'self'`,
  check `source in ('self','checker')`. Existing rows: `'self'`.
- `NewResult.source`; `revision.turn_results` reads `check_answer` entries too: verdict →
  outcome `correct → solid`, `precision`/`unit_differs → shaky`, `incorrect → todo`,
  `unreadable →` nothing.
- Reads: latest per (chapter, section, **source**). `Noted` gains `source`; `RevisionScope.earlier`
  keyed by `(chapter_id, section_id, source)`.
- Trailing state message (`curriculum_render`, by language): per section « selbst: fragile
  (12.11.) · Prüfer: richtig (12.11.) ».
- `GET/POST /api/courses/{c}/revision`: `results[]` items gain `source`. `record_result`'s tally
  counts self-assessments only (unchanged).
- Parcours: no write (decision 1).

### 3.14 Tutor prompt and mode layers

- `tutor.<lang>.md` (4 files): the paragraph « Tu ne corriges pas mécaniquement » becomes: for a
  final answer to an exercise that has a key (the pack shows `Clé`) or to a checkable variant,
  call `check_answer` and say its verdict; never say « juste » / « faux » without it; for
  anything else the previous rule holds. Sends the answer exactly as the student wrote it.
- `modes/revision.<lang>.md`: after `check_answer`, still show the course's wording and ask the
  student's own assessment (spec 020 D3).
- `modes/parcours.<lang>.md`: one line, the checker for exercises with keys.
- Pins regenerated deliberately: `system_text_sha*.txt` (all modes and languages),
  `test_prompt_files_languages` (twins still match).

### 3.15 Frontend

- `types.ts`: `AnswerCheckedEvent`, `Verdict`; `StoredEntry` tool fields `verdict`, `kind`,
  `exercise`.
- Reducer (`use-tutor-session.ts`): `answer.checked` → transcript marker; the status of the
  latest board whose cards include an `exercise` card: `correct` → `"correct"`, `incorrect` →
  `"wrong"`, other verdicts → unchanged (`"open"`); `history` gains the tool entry. Replay in
  `sessionFromEntries` the same way.
- `whiteboard.tsx`: the strip reads the board's status instead of the hard-coded `"done"`;
  `StatusGlyph` already has `correct` / `wrong` labels. `ExerciseBoard` shows a small verdict
  line under the statement (catalog `board_verdict_*`, 4 languages).
- Révision « Bilan » (`revision-bilan.tsx`, `lib/tutor/revision.ts latestResults`): two chips per
  section, « selbst » and « Prüfer », each with its date.
- Pack view: exercises with a key show a small « prüfbar » badge (catalog key), from the
  key lines in the pack Markdown (frontend regex on `KEY_LABEL` words, case table shared with
  the backend: `key_line_cases.json`).
- Voice bridge: sends `learner_text` (latest user transcript) with every tool call.

## 4. Data models

| Where | Change |
| --- | --- |
| `revision_results` | `source` String(8) NOT NULL default `'self'`, check constraint (migration 0015) |
| `ToolEntry` (stored JSON) | `verdict` (check_answer only) |
| `PackIndex` | `keys: frozenset[str]` |
| `LessonChapter`, `RevisionChapter` | `keys: Mapping[str, Key]` |
| `TurnContext` | `learner_text: str \| None` |
| `VoiceToolRequest` | `learner_text: str` (≤ 2000) |
| Revision DTO `results[]` | `source: "self" \| "checker"` |
| SSE | `answer.checked` |

No new table. No content stored beyond what the transcript already holds (the answer is in the
learner entry and the tool's arguments).

## 5. Error handling

- Model errors are tool errors (3.11), never HTTP errors; the model reads the reason and either
  asks the student again (unreadable, not the student's) or guides without a verdict.
- A `check_answer` call in discussion is refused by `registry.execute` (not offered).
- Reader exceptions are impossible by contract: readers return `None`; `check` never raises on
  student input (fuzz test). An exception in the checker is a bug: logged `check_failed`, the tool
  returns a tool error « Prüfer nicht verfügbar: begleite ohne Urteil. », the turn continues.
- Authoring: unreadable keys → repair → drop with §7 item (3.8); never a failed run because of keys.
- Old stored `ToolEntry` JSON without `verdict` stays valid.

## 6. Testing strategy

- **Case tables** `tests/fixtures/answer_cases.json`: per kind × course language, rows
  `{key, answer, verdict}` incl. notation variants (`12,5` / `12.5` / `12.500` / `10 000`), units
  (`90 km/h` vs `25 m/s`), precision (`3,1` vs key `3,14`), fractions, empty set, unions, ∞,
  leading names (`x =`, `L =`, `P`), garbage → unreadable. `test_answer_cases.py` runs them.
- `test_answer_readers.py`, `test_units.py`, `test_polynomial.py` (coefficients, roots degree 1–4,
  repeated roots, no real root, non-polynomial refused), `test_variants.py`.
- `test_pack_keys.py`: key lines per language, issues and codes; `test_pack.py` extended;
  `test_issue_messages.py` parity for the new codes.
- `test_check_tool.py`: each refusal, verdict outputs per language never containing the key
  (`assert key_text not in output` over the case table), learner-text check, révision args.
- Registry: `tests/fixtures/check_declaration.json` pins the new declaration; `board_declarations`
  and `path_declarations` pins **unchanged**; `test_mode_tools` lists updated.
- Révision: migration test (0015 up/down, defaults), `turn_results` mapping, reads per source,
  render goldens of the state message per language.
- Authoring: fake completion with good, bad and unrepairable keys (`fake_completion.py`); drop and
  §7 item; `authoring_eval` fixtures gain key lines.
- Model input wall: unchanged guarantees (`test_model_input_wall*.py` include a check call).
- `test_language_is_passed.py`, `test_by_language_tables.py` cover the new tables.
- Frontend: reducer (live and replay), strip status, ExerciseBoard verdict line, Bilan chips,
  pack badge, `key_line_cases.json` copy compared byte-for-byte, language sweeps for the new copy.
- Real-model probes (cost money, not in pytest): `scripts/probe.py --checker` per language: the
  tutor calls `check_answer` on a keyed exercise, passes the answer verbatim, never states a
  verdict without it, never leaks the key after `incorrect`.

## 7. Performance

- `check` is pure Python, sub-millisecond; root finding for degree ≤ 4 is a few hundred
  iterations at most.
- Keys parsed once per chapter content version (cache), not per turn.
- The new declaration and the prompt changes move the cached prefix once per mode and language;
  no per-turn variation is added before the breakpoint.

## 8. Security

- No evaluation of model or student text: the expression grammar parser only
  (`MAX_DEPTH`, length caps); answers ≤ 200 chars, voice `learner_text` ≤ 2000.
- The answer must come from the student's message: the model cannot check (and so claim a
  verdict on) text the student did not write.
- The key never leaves the server in a tool output; the pack (which the tutor reads) already holds
  the solution, as today.
- Routes unchanged except `/api/voice/tool` body; guards and ownership as before.

## 9. Monitoring and observability

- Log `answer_checked`: user, course, chapter, mode, kind, verdict, source (`pack` | `variant`),
  exercise ref, ms. Never the answer or the key.
- Log `answer_check_refused`: reason code only.
- Authoring: `keys`, `keys_dropped` counts on `authoring_stage`.
- `revision_result` log gains `source`.
