# Spec 023 — Answer checker: tasks (stage 023a)

Plan for **stage 023a only** (requirements R1–R4, design §§3.1–3.15 parts marked 023a). Stages 023b
(révision record, labels) and 023c (chat candidates) get their own plan after 023a ships
(design §10). Branch: `feature/023-answer-checker` (already contains spec 021's code and the shared
workflow). Status: **planned — awaiting the owner's review**.

Rules for every phase:
- Backend `cd backend && uv run pytest -q`, frontend `npm run typecheck && npm run lint && npm test`
  green at each phase end. French, English and Dutch outputs not touched by a task stay
  byte-identical; every pin change is deliberate and its diff read.
- Every per-language table gets `fr`, `en`, `nl`, `de` rows (`by_language`); new catalog keys in
  all four `messages/*.json`.
- Nothing logs an answer, a key or material text.

## Phase 0 — Groundwork without behaviour change

**Goal:** shared readers and an exact parse mode exist; nothing visible changes.
**Verify:** full suites green; `git diff` shows no pin, golden or declaration change.

- [ ] 0.1 Move `NUMBER`, `_decimal_comma`, `_thousands_comma`, `_german_number`, `INTERVAL`,
  `COORDS` and their patterns from `services/tools/figures.py` to `app/domain/notation.py`;
  `figures.py`, `plots.py` import them. Tests: existing rule tests and `test_notation_cases.py`
  unchanged and green.
- [ ] 0.2 `domain/expression.py`: `parse(…, exact=False)`; exact mode keeps number lexemes in `num`
  nodes, accepts `:`/`÷` as division, `√(…)` and `π`. Default mode byte-identical. Tests:
  `test_expression_exact.py` (lexemes kept, `1,5x` in comma languages, `√`, `π`, `:`); existing
  `expression_cases.json` tests unchanged.

## Phase 1 — Exact values and the checker for non-algebraic kinds

**Goal:** `check()` settles `number`, `set`, `interval`, `point`, `word`, `choice`, `mapping` in four
languages. **Verify:** `uv run pytest tests/unit/test_answer_cases.py -q`; the case table reads as
a list of examples a teacher would agree with.

- [ ] 1.1 `domain/answers/kinds.py`: dataclasses of design 3.2, `RECORDABLE`. Test: construction and
  normalisation (`Surd` with b = 0 → `Fraction`).
- [ ] 1.2 `domain/answers/exact.py`: `Surd` (a + b√c, square-free c) and `PiLinear` arithmetic needed
  by readers and comparison (+, −, × rational, exact equality, ordering of surds by squaring with
  signs). Tests: `test_exact_numbers.py`.
- [ ] 1.3 `domain/answers/units.py`: `UNITS` (design 3.4), exact conversion. Tests: `test_units.py`
  (`90 km/h` = `25 m/s`, `125 ct` = `1,25 €`, `°C` only to itself, unknown units).
- [ ] 1.4 `domain/answers/readers.py`: readers of design 3.3 except expression; `APPROX_WORDS`,
  `SET_SEPARATOR`, `JOINERS`, `NO_SOLUTION`, `TRUE_FALSE` per language; space grouping only for
  three-digit groups. Tests: `test_answer_readers.py` (each form of the table per language,
  `2 1/4` mixed not 21/4, `0,1̄` = 1/9, `x₁ = −1,5, x₂ = 0,5`, garbage → `None`).
- [ ] 1.5 `domain/answers/check.py` for the seven kinds: rules (D11, incl. negative `round`, vague
  rounding → `undecided`), forms (D13 number forms), `remainder`, `unit_differs`. Tests:
  `tests/fixtures/answer_cases.json` + `test_answer_cases.py` (per kind × language; expected values
  computed by hand), fuzz test (never raises).

## Phase 2 — Algebra: expressions and computed tasks

**Goal:** proven expression equivalence and complete, certified solutions for variants and key
tasks. **Verify:** `uv run pytest tests/unit/test_algebra.py tests/unit/test_variants.py -q`.

- [ ] 2.1 `domain/answers/algebra.py`: `Polynomial` over `Fraction`, `GuardedRational` from the
  exact AST (guards of every division and negative power kept), limits of design 3.6 →
  `undecided`. Tests: `x/x` vs `1` keeps the guard; identically zero divisor; caps.
- [ ] 2.2 Square-free part, exact gcd, Sturm sequences, root counting and isolation; rational root
  theorem; quadratic factors as surds; multiplicities kept. Tests: degrees 1–4, repeated roots,
  close roots (`(x−1)(x−1.0001)`), no real root, count before/after isolation.
- [ ] 2.3 Domain equality (exclusion sets proven equal) and stated-domain annotations
  (`DOMAIN_WORDS`, `D = ℝ \ {…}`) that only intersect. Tests: `(x²−1)/(x−1)` vs `x+1` → undecided,
  vs `x+1 für x ≠ 1` → correct; `x` vs `x(x²+1)/(x²+1)` → correct.
- [ ] 2.4 Certified rounding of isolated roots and π forms (bounds of design 3.6), exact tie at the
  boundary. Tests: ties, near-ties, `πr²` rounding, limit exhaustion → undecided.
- [ ] 2.5 `check()` for `expression` (domain then value, `form_unchecked`) and certified rounding for
  irrational number keys/answers; extend `answer_cases.json`.
- [ ] 2.6 `domain/answers/variants.py`: `Evaluate`, `Solve`, `task_key`, `task_statement` per language
  (design 3.7), every `NotCheckable` reason. Tests: `test_variants.py` (polynomial, denominator with
  excluded root, `x^n = c` exact/approximate, inequalities with exact sign tests, statements per
  language).

## Phase 3 — Keys in the pack and authoring

**Goal:** packs carry validated key lines; the agent writes them; the pack view shows which
exercises are checkable. **Verify:** in the pack editor of a German chapter add
`**Schlüssel:** number 374` under an exercise → saved; `**Schlüssel:** number drei` → 422 with a
German message; the pack view shows « prüfbar ».

- [ ] 3.1 `domain/answers/keys.py`: line grammar (design 3.8), `KEY_LABEL`, `ANSWER_LABEL`,
  `MEASURE_WORDS` per language, `pack_keys`, `exercise_statement` (stem + one sub-item, never an
  answer or key line, `None` on figure marks or measuring operators). Tests: `test_pack_keys.py`
  per language.
- [ ] 3.2 Task recomputation → `agrees` / `needs_review` / inconclusive (= `material`). Tests in
  `test_pack_keys.py`.
- [ ] 3.3 `index_pack` returns key issues (`pack.key_*` codes, catalog in four languages,
  `render_issue`); `PackIndex.keys`. Tests: `test_pack.py`, `test_issue_messages.py`.
- [ ] 3.4 `CurriculumCache`: `LessonChapter.keys`, `RevisionChapter.keys` per (chapter, content
  version). `GET …/pack` gains `keys: [{ref, status}]`. Tests: cache and route tests.
- [ ] 3.5 Templates (4 subjects × 4 languages) and `prompts/authoring/pack.<lang>.md`: key rule,
  rules only as requirements §1.3, tasks in two forms, textbook references, appendix solutions,
  answer pools, figure marks, explicit review labels kept. Tests: `test_prompt_files_languages`
  skeleton parity; authoring prompt pins regenerated.
- [ ] 3.6 Runner: left-over key issues → drop lines + `DROPPED_KEY[lang]` §7 item; `authoring_stage`
  logs `keys`, `keys_dropped`, `keys_needs_review`. Tests: fake completion with good, bad,
  unrepairable and disagreeing keys.
- [ ] 3.7 Frontend pack view: « prüfbar » / « Lösung prüfen » badges from `keys`; catalog keys.
  Test: component test per state.

## Phase 4 — Bound cards, presentations and `turn.stored`

**Goal:** Célestin can put a checkable exercise on the board; it is stored with the turn and
announced as eligible. **Verify:** a scripted (fake-provider) parcours turn with a bound card
streams `turn.stored {exercise_ids: [id]}`; the séance read endpoint returns the card with
`eligible: true`; a failed store streams no `turn.stored`.

- [ ] 4.1 Card models: `check: CheckSpec | None` on `ExerciseCard` and `CheckQuestionCard`;
  `CheckQuestionCard` declaration without `correct_option_id`/`feedback`; a lenient reading model
  for stored and reported cards that drops legacy and server-set fields. Regenerate
  `board_declarations.json` (diff: only these changes). Tests: board model tests, declaration pin,
  old stored card JSON still loads.
- [ ] 4.2 Migration `0015_answer_checker`: `exercise_presentations` and `answer_submissions`
  (design 3.10, 3.11), constraints, cascades, indexes. Tests: migration up/down, constraints,
  cascades on user/course/chapter deletion.
- [ ] 4.3 `services/tools/bind.py`: binding rules of design 3.9 (pack and variant, statement
  replaced or generated, unbound reasons in the course language, `needs_review` notice without
  field); `display_board` calls it; voice path ignores `check`. Tests: `test_bind.py`.
- [ ] 4.4 Stores: `conversations.store_seance(…, presentations=)` and `conversations.append(…,
  presentations=)` write presentations in the turn's transaction; `seance/report` never creates one.
  Tests: repository tests (rollback writes nothing), report strips `exercise_id`.
- [ ] 4.5 `turn.stored` event: store hooks return stored presentation ids; `stream_turn` sends
  `turn.stored {exercise_ids, message_id: null}` after a successful `on_complete`, none after a
  failure; a révision run capped by the same turn lists none. Tests: `test_sse.py` cases,
  golden SSE transcripts extended deliberately.
- [ ] 4.6 Eligibility service (design 3.10) and per-card `eligible`/reason on the séance and
  révision read endpoints. Tests: rollover, return to section, content change, reset, closed
  révision, foreign user.

## Phase 5 — Submissions

**Goal:** a submitted answer is checked at once, stored with a transcript entry, and Célestin
reacts on the next turn. **Verify:** with the fake provider: submit `374` to a bound card →
response `correct`/`material`; resubmit the same request id → same response, one row; the next
turn's model input contains the submission line in German.

- [ ] 5.1 `services/answers.py` + `POST /api/answers` (design 3.11): resolve and authorise,
  idempotency on `(user_id, request_id)`, `check()` in a worker with its time limit, one transaction
  (submission + `submission` transcript entry under the optimistic guard), error codes of design §5,
  `voice` → 422. Tests: `test_answers_route.py`, `test_route_guards.py`.
- [ ] 5.2 `submission` entry: schema, `history.to_provider_input` rendering per course language
  (verdict and basis words, never a key), notebook and séance reads include it. Tests:
  `test_model_input_wall*.py`, `test_language_is_passed.py`, history rendering goldens.
- [ ] 5.3 Message-less turn after a submission: `seances.open_turn` and the révision turn accept
  `message: null` when the last stored entry is a submission. Tests: chat and révision route tests.
- [ ] 5.4 Logs `answer_checked`, `answer_refused`, `exercise_bound`, `exercise_unbound`,
  `turn_stored` (ids and codes only). Tests: log assertions without content.

## Phase 6 — Frontend

**Goal:** the student answers in the card, sees the verdict with its source, and no choice card
shows an unverified verdict anywhere. **Verify:** in the browser (fake or real provider) a bound
card's field is disabled while streaming and enabled after `turn.stored`; submitting shows
« Stimmt mit der Lösung in deinem Material überein »; reload keeps it; an old discussion's choice
card shows the pick without colour.

- [ ] 6.1 `types.ts`: `Verdict`, `Basis`, submission request/response, `turn.stored`, card fields
  `exercise_id`, `status`, `eligible`; `CheckQuestionCard` without legacy fields. Typecheck.
- [ ] 6.2 Reducer (`use-tutor-session.ts`): `turn.stored` enables fields; submission response sets
  the verdict of the card with that `exercise_id` on any board of the séance; `sessionFromEntries`
  replays submission entries. Tests: reducer live and replay, verdict on a non-latest board.
- [ ] 6.3 `ExerciseBoard`: answer field, submit (request id per attempt, retry on 409 busy), then a
  message-less tutor turn; verdict line by verdict × basis, `needs_review`, `undecided`,
  « Wiederholung voll », expected-form example. Tests: component tests, keyboard and screen reader.
- [ ] 6.4 `CheckQuestionBoard` in every mode (lesson, discussion, révision, notebook): unbound pick
  uncoloured without feedback; bound pick submits `source: "choice"` and shows the checker's
  verdict; old cards with `correct_option_id` stay uncoloured. Tests: per mode, old card.
- [ ] 6.5 Catalog keys in `fr`, `en`, `nl`, `de` for every new text; language sweeps green.

## Phase 7 — Tutor prompts and probes

**Goal:** Célestin binds keyed exercises and speaks verdicts only from submission entries.
**Verify:** prompt diffs read; `scripts/probe.py --checker` exists and runs against the fake
provider in its unit test (real-model runs are separate and cost money).

- [ ] 7.1 `tutor.<lang>.md` (4): the « no mechanical correction » paragraph becomes the checker rule
  (design 3.12); `modes/parcours.<lang>.md` and `modes/revision.<lang>.md` one line each. Regenerate
  `system_text_sha*` pins deliberately. Tests: `test_prompt_files_languages`, prompt service tests.
- [ ] 7.2 `scripts/probe.py --checker` per language: binds a keyed exercise, submits, checks that the
  tutor uses the entry's verdict and never leaks the key; the verdict-in-prose metric left as a
  marked TODO for the owner's decision (`decisions.md` §14.3). Test: probe unit test with fakes.

## Phase 8 — Documentation and release check

**Goal:** the documentation is true and the status honest. **Verify:** the owner runs the
Docker image, prepares a chapter from textbook material with solutions, answers a keyed exercise
and a variant in the card, and sees verdicts with their source.

- [ ] 8.1 `documentation/answer-checker.md` (new) + `documentation/index.md`; update
  `documentation/chapters.md`, `authoring.md`, `tutor-turn-pipeline.md`, `seances.md`,
  `revision.md`, `course-language.md` where they change; `CLAUDE.md` architecture paragraph.
- [ ] 8.2 Full suites, `docker build` and `docker/smoke.sh`; `git status` shows no unintended pin.
- [ ] 8.3 `specs/index.md`: 023a implemented, 023b/023c planned later; record unrun real-model
  probes.

## Deviations

Recorded here during implementation and reported to the owner at the end.
