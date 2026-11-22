# Spec 023 — Answer checker: mechanical verdicts on final answers

Status: requirements only, written at the owner's request (22 November 2026). Not to be designed
or built until the owner resumes it. Foundation of spec 022 (practice test).

## 1. Introduction

Today no answer is checked by code. The tutor prompt says Célestin cannot check a calculation
with certainty and never declares « juste » or « faux » (`tutor.<lang>.md`); révision records
only the student's self-assessment (spec 020 D3); a `check_question` card carries a
`correct_option_id` the model chose, checked in the browser and never reported back.

This spec adds a **checker**: deterministic code that compares a student's final answer with an
answer key and returns a verdict, with no model judging the answer. It adds:

1. **Checkable keys in the pack**: each typical exercise (pack §6) whose material gives a solution
   carries its answer kind and key in a fixed, parseable form, validated when the chapter is
   prepared and when the pack is edited.
2. **The checker module**: one reader and one comparison per answer kind, per course language.
3. **A tool, `check_answer`**, offered in the parcours and in révision: Célestin hands it the
   student's final answer and either an exercise id (key from the pack) or a variant's data (key
   derived or verified by code). The verdict is shown to the student and, in révision, recorded.

Value: the product's principle « it never grades from impression » holds for every answer the
code can check, and the révision record gains verdicts the student can trust.

### 1.1 Answer kinds

| Kind | Key form (illustrative; the design fixes it) | Verdict |
| --- | --- | --- |
| `choice` | option id | equal |
| `number` | value, optional tolerance or rounding, optional unit | equal within tolerance; equal unit after the pack's conversions, else « unit differs » |
| `expression` | expression in the grammar of `domain/expression.py`, variable, domain | equivalent: equal values at sample points of the domain; optionally a required form (« factorised », « simplified ») checked structurally |
| `interval` | bounds and open/closed ends, or a union of intervals | same bounds and ends |
| `solution_set` | finite set of numbers | same set, order and repetition ignored |
| `point` | coordinates | same coordinates within tolerance |
| `word` | one or several accepted words from the pack's vocabulary (pack §5) | equal after normalising case, spaces, accents (accents configurable per subject: a language course may require them) |

Every kind reads the student's text in the **course's** notation (`by_language` tables): decimal
comma or point, thousands grouping, `]a ; b[` or `(a, b)`, `P(2 | −1,5)` or `(2, −1.5)`, `%`.
Fractions and decimals of the same value are equal for `number` unless the key requires a form.

### 1.2 Variants: verify instead of solve

A variant (the course's exercise with other numbers) has no key in the material. The checker
accepts it only when code can settle the answer without solving:

- **Evaluate**: the item is an expression to compute at given values → the code computes the key.
- **Substitute**: the item is an equation or inequality → the code substitutes the student's
  answer (a number, a solution set, an interval's bounds and an inner point) and checks it holds.
  A `solution_set` answer is accepted only if every element satisfies the relation and the
  item states how many solutions there are (or the relation is polynomial of a degree the code can
  bound).
- **Anything else** (a derivation, a proof, a word problem whose relation the item does not state)
  is not a checkable variant: Célestin guides as today, without a verdict.

## 2. Alignment with product vision

- Principle 4 (brief §5): *it never grades from impression; where an answer is mechanically
  checkable, the verdict comes from a checker*. This spec builds that checker.
- Brief §12.1 (checking outside maths) and phase C « Later: a mechanical checker feeding the same
  record »: answered for the kinds of §1.1, in every subject whose pack has them.
- Spec 020 D3: « When a mechanical checker exists, it feeds the same record. »
- Principle 1 and 2: keys come from the student's material; the authoring agent copies them, it
  does not invent them.
- Principle 3: a verdict never reveals the key while the exercise is open.
- Spec 022 (practice test) depends on the keys, the checker and its case tables.

## 3. Requirements

### R1. Checkable keys in the pack

As a student, I want the solutions of my material turned into keys the code can check, so that my
answers to the course's exercises get a reliable verdict.

1. Each pack template (`templates/<subject>.pack.<lang>.md`, every subject and course language)
   asks, per typical exercise, for its answer kind and key in the fixed form, next to the
   existing « Antwort » / « Réponse » line, when the material gives a solution.
2. An exercise with several questions carries one key per sub-question, each with its own id
   (e.g. `6.1.2 a)`).
3. No key is written for an exercise whose material gives no solution, whose solution the agent
   flagged in « points to check » (pack §7), or whose answer is not of a kind of §1.1.
4. The authoring agent copies the key from the material's solution; it does not compute a key
   the material does not give.
5. `domain/pack.py` validates every key when the pack is prepared or edited: the kind is known, the
   key parses in the course's notation, the referenced exercise exists. An invalid key is a
   content issue the agent repairs (bounded, as today); a key that cannot be repaired is dropped
   with a « points to check » entry, never stored invalid.
6. Packs stored before this spec stay valid; their exercises simply have no key.
7. The pack editor (`PUT …/pack`) shows and validates keys like any other pack content.

### R2. The checker module

As a developer, I want one deterministic module that settles answers, so that every mode and
spec 022 share the same verdicts.

1. Input: answer kind, key (or variant data, §1.2), the student's answer text, the course
   language. Output: `correct`, `incorrect`, or `unreadable` with the expected form; for
   `number` also `unit_differs` or `precision` (right value, wrong rounding) when they apply.
2. No model call, no I/O, no randomness: sample points for `expression` are fixed per call.
3. Imports no SDK and no catalog; text it returns to the model is in the course language, text for
   the student goes through the catalog (spec 010).
4. Each kind has a case table per course language (`tests/fixtures/checker_cases.json` or one per
   kind), with accepted, refused and unreadable inputs; where the frontend parses the same notation,
   the table is shared byte-identically, like `notation_cases.json`.
5. It reuses the existing readers: `domain/expression.py` (`parse`, `evaluate`), `NUMBER`,
   `INTERVAL`, `COORDS` (`services/tools/figures.py`), moved to a shared place if needed.
6. Unreadable is not incorrect: the student is told the expected form with an example in the
   course's notation and answers again.

### R3. The `check_answer` tool

As a student, I want Célestin to have my final answer checked by the code, so that « right » or
« wrong » is never his impression.

1. Arguments: the student's final answer, and either an exercise reference (pack id, sub-question)
   or a variant's data (kind, relation or expression, given values), plus for révision the chapter
   and section.
2. **The answer is the student's**: the tool refuses (tool error the model reads) an answer that
   is not found, after normalising spaces, in the latest learner message.
3. A pack reference without a key, or variant data that is not checkable (§1.2), is refused with a
   tool error that tells Célestin to guide without a verdict.
4. Offered in the parcours and in révision; not in discussion. Declared after every existing tool,
   so existing declarations keep their bytes (`path_declarations.json`, `board_declarations.json`).
5. Returns the verdict to the model, never the key while the exercise is open; the key is part of
   the output only after a reveal (the existing reveal rules) or a correct answer.
6. Emits an event the board renders as a verdict mark on the exercise (correct, incorrect,
   unreadable with the expected form); stored in the transcript and replayed like every tool since
   spec 018 (`replay`, `shown`).
7. Available in voice through `/api/voice/tool`, as every tool of the mode is.

### R4. The tutor's rule changes with the checker

As a student, I want Célestin to say « right » or « wrong » only when the code said so, so that I
can rely on it.

1. The tutor prompt (every course language) says: for a final answer of a checkable exercise, call
   `check_answer` and say the verdict it returns; never declare a verdict without it; for anything
   else, the current rule (no verdict, have the student check) holds.
2. After `incorrect`, the usual tutoring applies: questions and hints, no answer.
3. A `check_question` card's correct option must be the pack's key when the question comes from a
   pack exercise with a `choice` key; the student's pick is reported to the tool so the verdict is
   the checker's, not only the browser's.

### R5. Verdicts feed the révision record

As a student, I want verdicts from révision kept with my self-assessments, so that the next
révision starts from what the code saw too.

1. In révision, each verdict is recorded per section in the révision record (spec 020
   `revision_results` or a sibling table), marked as a checker verdict, distinct from a
   self-assessment.
2. Recorded with the transcript when the turn ends, in one transaction, as `record_result` is
   (spec 020 D6): a stopped or failed turn records nothing.
3. The « Bilan » and the révision's trailing state message show, per section, the latest
   self-assessment and the latest verdicts, each with its source and date.
4. Célestin still asks for the student's self-assessment after a question (spec 020 D3); the
   verdict informs it and never replaces it.
5. In the parcours, verdicts are shown and stored in the séance transcript only; they do not move
   the path (`complete_section` stays the only way a section is done).

## 4. Non-functional requirements

### Architecture
- Rules in code: the key, the verdict and the « answer is the student's » check are enforced in
  the tool and the checker, not in prompt text.
- Every per-language reader is a `by_language` table; a missing language fails at import.
- French output of existing tools, prompts and renderings is byte-identical except where this spec
  changes it on purpose (tutor prompt rule, pack templates); `system_text_sha*` pins are
  regenerated deliberately.
- Tool order and declarations stay fixed for the cached prefix; the new declaration goes last.
- `test_language_is_passed.py`, `test_model_input_wall*.py` and `test_route_guards.py` cover the new
  code.

### Performance and cost
- Checking is local and synchronous, well under a millisecond per answer; no extra model call.
- Keys add a few lines per exercise to the pack and so to the cached prefix; no change to the turn
  loop.

### Security and privacy
- Model output is untrusted: tool arguments are validated by Pydantic, keys are parsed, the
  expression grammar never executes text.
- Logs and the usage ledger carry kind, verdict and ids, never answers or keys (spec 015).
- Verdict rows are owned by the student and deleted with the course, the chapter or the account.

### Reliability
- Case tables pin every reader per course language; a notation change edits the table in the same
  commit, both copies where shared.
- An exercise without a usable key degrades to today's behaviour (guidance without verdict),
  never to an error for the student.

### Usability
- The verdict mark and the « expected form » message in French, English, Dutch and German
  (catalog); the example uses the course's notation.
- The student can see on the pack's view which exercises have a checkable key.

## 5. Out of scope

- The practice test itself (spec 022).
- Checking working steps, derivations, proofs, justifications, drawn graphs.
- A computer algebra system: no symbolic solving; variants are verified by evaluation or
  substitution only (§1.2).
- Graded class test analysis and correction review (follow-ups named in spec 022).

## 6. Decisions on the open questions (owner, 22 November 2026)

1. Parcours verdicts are shown and stored in the séance transcript only; they do not feed the
   révision record (R5.5 stands).
2. Required forms for `expression` (« factorised », « simplified ») are later: this spec checks
   equivalence only; when an item asks for a form, the checker settles the value and Célestin
   looks at the form without a verdict.
3. Units: a fixed built-in table of common SI conversions (length, mass, time, speed, volume,
   area, percent); `25 m/s` and `90 km/h` are equal. A unit outside the table is compared as
   written.
4. Tolerance when the material states no rounding: the key's own decimals. An answer that rounds
   to the key at the key's decimals is correct (more decimals allowed); fewer decimals than the
   key is `precision` (« not precise enough »), not correct.
