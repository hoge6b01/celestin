# Spec 023 — Answer checker: mechanical verdicts on final answers

Status: requirements written at the owner's request (22 November 2026), open questions answered
by the owner (§6), then revised after a review the owner did with another assistant
(`specs/023-review.md`, decisions in §7; they supersede §6.4 and design proposal D2), then
checked against two NRW textbooks (decisions in §8; §8.1 refines §7.1). Foundation of spec 022
(practice test).

## 1. Introduction

Today no answer is checked by code. The tutor prompt says Célestin cannot check a calculation
with certainty and never declares « juste » or « faux » (`tutor.<lang>.md`); révision records
only the student's self-assessment (spec 020 D3); a `check_question` card carries a
`correct_option_id` the model chose, and the browser colours the student's pick green or red from
it: a verdict that is the model's word.

This spec adds a **checker**: deterministic code that compares a student's final answer with an
answer key and returns a verdict, with no model judging the answer. It adds:

1. **Checkable keys in the pack**: each typical exercise (pack §6) whose material gives a solution
   carries its answer kind and key in a fixed, parseable form, validated when the chapter is
   prepared and when the pack is edited; optionally the exercise's task in a form the code can
   compute, so the stored solution can be recomputed.
2. **The checker module**: one reader and one comparison per answer kind, per course language,
   with exact arithmetic.
3. **Exercises bound to their checking data**: when Célestin sets a checkable exercise, the server
   records it with its checking data and shows what is checked; the answer is checked against
   that recorded exercise.
4. **A tool, `check_answer`**, offered in the parcours and in révision: Célestin hands it the
   student's final answer and the recorded exercise. The verdict, with its source (the student's
   material, a computation, or both), is shown to the student and, in révision, recorded for that
   exercise.

Value: the product's principle « it never grades from impression » holds for every answer the
code can check, and the révision record gains verdicts the student can trust.

Expected coverage (textbook check, §8): a German Gymnasium textbook prints solutions only for its
self-test and review pages, about a quarter of its exercises; of those, about half to
three-fifths of the sub-answers in algebra and a third in geometry are of a checkable kind.
Variants settled by code (§1.2) carry the rest of the practice.

### 1.1 Answer kinds

| Kind | Key form (illustrative; the design fixes it) | Verdict |
| --- | --- | --- |
| `choice` | option id, among the exercise's option ids | equal |
| `number` | value (decimal, fraction, mixed number, repeating decimal, exact root form `a + b√c`, power of ten), optional rule, optional unit, optional required form | exactly equal (after the built-in unit conversions); a rounding rule when the exercise states it or the material marks the solution as rounded (§7.1, §8.1); a required unit or form when the exercise asks for one (§8.3) |
| `expression` | expression in the grammar of `domain/expression.py`, variable | equivalent, only where the code can establish it for the expression's class (§7.5); otherwise « not reliably checkable »; a required form (« Scheitelpunktform ») is not checked and said so (§8.3) |
| `interval` | bounds and open/closed ends, or a union of intervals | same bounds and ends |
| `solution_set` | finite set of numbers (exact root forms included), the empty set, `ℝ` | same set, order and repetition ignored |
| `point` | coordinates | same coordinates |
| `word` | one or several accepted words from the pack's vocabulary (pack §5) | equal after normalising case, spaces, accents (accents configurable per subject: a language course may require them) |
| `mapping` | pairs (« Ordne zu »: `A–2, B–1`) | same pairs |

Every kind reads the student's text in the **course's** notation (`by_language` tables): decimal
comma or point, thousands grouping, `]a ; b[` or `(a, b)`, `P(2 | −1,5)` or `(2, −1.5)`, `%`.
Fractions and decimals of the same value are equal (`3/4` = `0,75`) unless the exercise asks for
a form (§8.3). An answer may carry `≈`, « rund » or « ca. » before it.

### 1.2 Variants: settled by code

A variant (the course's exercise with other numbers) has no key in the material. The checker
accepts it only when code can settle the answer itself:

- **Evaluate**: the item is an expression to compute at given values → the code computes the key.
- **Solve**: the item is an equation or inequality of a class the code can solve completely (the
  design fixes the class: polynomial, rational with the variable in a denominator, pure power
  `x^n = c`) → the code computes the full solution and checks the answer against it.
- **Anything else** (a derivation, a proof, a word problem whose relation the item does not state)
  is not a checkable variant: Célestin guides as today, without a verdict.

The task the code computes is the task the student sees: the server shows it on the exercise card
from the checking data (§7.2).

## 2. Alignment with product vision

- Principle 4 (brief §5): *it never grades from impression; where an answer is mechanically
  checkable, the verdict comes from a checker*. This spec builds that checker, and removes the one
  verdict today that is the model's word (`check_question`, §7.6).
- Brief §12.1 (checking outside maths) and phase C « Later: a mechanical checker feeding the same
  record »: answered for the kinds of §1.1, in every subject whose pack has them.
- Spec 020 D3: « When a mechanical checker exists, it feeds the same record. » It does, per
  exercise, beside the self-assessment (§7.7).
- Principles 1 and 2: keys come from the student's material; the authoring agent copies them, it
  does not invent them. A verdict against the material says so; it does not claim the material
  is right (§7.3).
- Principle 3: a verdict never reveals the key while the exercise is open.
- Spec 022 (practice test) depends on the keys, the exercise binding, the checker and its case
  tables.

## 3. Requirements

### R1. Checkable keys in the pack

As a student, I want the solutions of my material turned into keys the code can check, so that my
answers to the course's exercises get a reliable verdict.

1. Each pack template (`templates/<subject>.pack.<lang>.md`, every subject and course language)
   asks, per typical exercise, for its answer kind and key in the fixed form, next to the
   existing « Antwort » / « Réponse » line, when the material gives a solution.
2. An exercise with several questions carries one key per sub-question, each with its own id
   (e.g. `6.1.2 a)`); a sub-answer with several quantities carries one key per named part
   (`6.1.2 a) u`, `6.1.2 a) A`).
3. No key is written for an exercise whose material gives no solution, whose solution the agent
   flagged in « points to check » (pack §7), or whose answer is not of a kind of §1.1.
4. The authoring agent copies the key from the material's solution; it does not compute a key
   the material does not give. A rounding rule is written when the exercise or a note governing
   it states one, or when the solution is marked `≈`, « rund » or « ca. » (§8.1); a required unit or
   form when the exercise asks for one (§8.3).
4a. Textbooks (§8.4): each pack exercise keeps the material's reference (« S. 128, Nr. 11 »);
   solutions printed elsewhere (an appendix) are joined to their exercise by that reference; an
   unordered pool of answers (« Lösungen zu 5 ») never becomes a key and is never copied into an
   exercise's statement. An exercise that needs a figure or a measurement on the page is marked so
   (§8.5).
5. Where the exercise's task is of a class the code can compute (§1.2), the key line may also
   carry that task in the fixed form, copied from the statement, so the code can recompute the
   solution (§7.3, §7.4).
6. `domain/pack.py` validates every key when the pack is prepared or edited: the kind is known, the
   key parses in the course's notation, the referenced exercise exists, an `expression` key is of a
   class the checker can establish equivalence for. An invalid key is a content issue the agent
   repairs (bounded, as today); a key that cannot be repaired is dropped with a « points to check »
   entry, never stored invalid.
7. When a key carries a task and the computed solution differs from the stored one, the key is
   marked as needing review (§7.4); the stored solution is kept as the material gives it.
8. Packs stored before this spec stay valid; their exercises simply have no key.
9. The pack editor (`PUT …/pack`) shows and validates keys like any other pack content.

### R2. The checker module

As a developer, I want one deterministic module that settles answers, so that every mode and
spec 022 share the same verdicts.

1. Input: answer kind, key (from the pack or computed for a variant), the student's answer text,
   the course language. Output: `correct`, `incorrect`, `unreadable` with the expected form; for
   `number` also `unit_differs`, `form_differs` (right value, not in the unit or form the exercise
   asks, §8.3), and `precision` (right value, not rounded as the rule asks) when the key carries a
   rounding rule; for `expression` with a required form, `form_unchecked` (value right, form not
   checked, §8.3); or **not reliably checkable** when the code cannot settle the answer (§7.5). Every verdict names its **basis**: the material's solution, a computation, or
   both (§7.3).
2. Exact arithmetic: numbers read from keys and answers are exact rationals; unit conversions are
   exact; floating point is used only where a rounding rule is stated.
3. No model call, no I/O, no randomness.
4. Imports no SDK and no catalog; text it returns to the model is in the course language, text for
   the student goes through the catalog (spec 010).
5. Each kind has a case table per course language (`tests/fixtures/answer_cases.json` or one per
   kind), with accepted, refused, unreadable and not-checkable inputs; where the frontend parses
   the same notation, the table is shared byte-identically, like `notation_cases.json`.
6. It reuses the existing readers: `domain/expression.py` (`parse`), `NUMBER`, `INTERVAL`, `COORDS`
   (`services/tools/figures.py`), moved to a shared place.
7. Unreadable is not incorrect: the student is told the expected form with an example in the
   course's notation and answers again.

### R3. Exercises bound to their checking data, and the `check_answer` tool

As a student, I want my answer checked against the exercise I was actually given, so that the
verdict is about that exercise and nothing else.

1. **Binding** (§7.2): when Célestin puts a checkable exercise on the board, it names its checking
   data (a pack exercise reference, or a variant's task). The server validates it, records the
   exercise with an id and its checking data in the séance's stored entries, and shows the
   student what is checked: for a pack exercise, the exercise as the pack states it (its shared
   stem and the one sub-question checked); for a variant, the task as the code reads it. An
   exercise whose checking data does not validate, or that needs a figure the card cannot show
   (§8.5), is shown without being checkable.
2. `check_answer` takes the student's final answer and the recorded exercise's id (plus for
   révision the chapter and section). It checks against that recorded exercise only; the verdict
   belongs to that exercise and is shown on its card, wherever it is in the séance.
3. **The answer is the student's**: the tool refuses (tool error the model reads) an answer that
   is not found, after normalising spaces, in the latest learner message.
4. An unknown or uncheckable exercise id, an exercise marked as needing review (§7.4), or an
   answer the code cannot settle (§7.5) gives no correct/incorrect verdict: the tool tells Célestin
   to guide without one.
5. Offered in the parcours and in révision; not in discussion. Declared after every existing tool.
6. Returns the verdict and its basis to the model, never the key.
7. Emits an event the board renders as a verdict mark on the bound exercise (correct, incorrect,
   unreadable with the expected form, not reliably checkable), with its source in words; stored in
   the transcript and replayed like every tool since spec 018 (`replay`, `shown`).
8. Available in voice through `/api/voice/tool`, as every tool of the mode is.

### R4. The tutor's rule changes with the checker

As a student, I want Célestin to say « right » or « wrong » only when the code said so, so that I
can rely on it.

1. The tutor prompt (every course language) says: for a final answer to a checkable exercise, call
   `check_answer` and say the verdict it returns, with its source; never declare a verdict without
   it; for anything else, the current rule (no verdict, have the student check) holds.
2. After `incorrect`, the usual tutoring applies: questions and hints, no answer.
3. **Multiple choice** (§7.6): a choice card shows a correct/incorrect verdict only when it is bound
   to a `choice` key and the checker evaluated the pick. A choice card without such a key shows the
   pick and no verdict; Célestin may still discuss it. The model-chosen correct option no longer
   produces a verdict, in any mode; stored cards replay without one.

### R5. Checked exercises in the révision record

As a student, I want the exercises the code checked in révision kept with my self-assessments, so
that the next révision starts from what the code saw too, without pretending one answer proves a
whole section.

1. In révision, each checker verdict is recorded as the result of **that exercise** (its pack
   reference, or the variant's task), with its date, verdict and basis, and the chapter and section
   it belongs to (§7.7).
2. A checker result does not set or change the section's self-assessed outcome (acquis, fragile,
   à revoir) and never marks a section as mastered; the self-assessment stays beside it.
3. Recorded with the transcript when the turn ends, in one transaction, as `record_result` is
   (spec 020 D6): a stopped or failed turn records nothing. « Not reliably checkable » and
   « needs review » record nothing.
4. The « Bilan » and the révision's trailing state message show, per section, the latest
   self-assessment and the checked exercises with their latest verdict, source and date.
5. Célestin still asks for the student's self-assessment after a question (spec 020 D3); the
   verdict informs it and never replaces it.
6. In the parcours, verdicts are shown and stored in the séance transcript only; they do not move
   the path (`complete_section` stays the only way a section is done) and are not recorded in
   révision.
7. Summaries over several checked exercises of a section belong to spec 022.

## 4. Non-functional requirements

### Architecture
- Rules in code: the key, the binding, the verdict and the « answer is the student's » check are
  enforced in the tools and the checker, not in prompt text.
- Every per-language reader is a `by_language` table; a missing language fails at import.
- French output of existing tools, prompts and renderings is byte-identical except where this spec
  changes it on purpose (tutor prompt rule, pack templates, the board's exercise and choice cards);
  `system_text_sha*` and declaration pins are regenerated deliberately.
- Tool order stays fixed for the cached prefix; the new declaration goes last.
- `test_language_is_passed.py`, `test_model_input_wall*.py` and `test_route_guards.py` cover the new
  code.

### Performance and cost
- Checking is local and synchronous, well under a millisecond per answer; no extra model call.
- Keys add a few lines per exercise to the pack and so to the cached prefix; no change to the turn
  loop.

### Security and privacy
- Model output is untrusted: tool arguments are validated by Pydantic, keys and tasks are parsed,
  the expression grammar never executes text.
- Logs and the usage ledger carry kind, verdict, basis and ids, never answers or keys (spec 015).
- Result rows are owned by the student and deleted with the course, the chapter or the account.

### Reliability
- Case tables pin every reader per course language; a notation change edits the table in the same
  commit, both copies where shared.
- An exercise without a usable key, a key needing review, or an answer the code cannot settle
  degrades to today's behaviour (guidance without verdict), never to an error for the student.

### Usability
- The verdict mark, its source and the « expected form » and « not reliably checkable » messages
  in French, English, Dutch and German (catalog); the example uses the course's notation.
- The student can see on the pack's view which exercises have a checkable key, and which need
  their solution reviewed.

## 5. Out of scope

- The practice test itself (spec 022), including section summaries over several checked
  exercises.
- Checking working steps, derivations, proofs, justifications, drawn graphs.
- A general computer algebra system: only the expression and equation classes the design names.
- Checking required forms of `expression` answers (« factorised », « Scheitelpunktform »): §6.2;
  the value is checked and the form is said to be unchecked (§8.3).
- Exercises that depend on a figure or a measurement on the page (§8.5).
- Graded class test analysis and correction review (follow-ups named in spec 022).

## 6. Decisions on the open questions (owner, 22 November 2026)

1. Parcours verdicts are shown and stored in the séance transcript only; they do not feed the
   révision record (R5.6 stands).
2. Required forms for `expression` (« factorised », « simplified ») are later: this spec checks
   equivalence only; when an item asks for a form, the checker settles the value and Célestin
   looks at the form without a verdict.
3. Units: a fixed built-in table of common SI conversions (length, mass, time, speed, volume,
   area, percent); `25 m/s` and `90 km/h` are equal. A unit outside the table is compared as
   written.
4. ~~Tolerance when the material states no rounding: the key's own decimals.~~ Superseded by §7.1.

## 7. Decisions from the review (owner, 22 November 2026; `specs/023-review.md`)

1. **Numbers are exact by default.** A key of `5` accepts `5` and `5,0`, not `5,4`. A tolerance or
   rounding rule applies only when the exercise or its key states it; `precision` exists only
   under such a rule. Applies to converted units too (`90 km/h` = `25 m/s` exactly). Refined by
   §8.1: a solution the material marks as rounded states its own rule.
2. **An answer is bound to its exercise.** The server records a checkable exercise with its id and
   checking data when it is presented; the check uses that record, and the verdict belongs to that
   exercise, not to whichever card is latest. Checking data that cannot be reliably associated
   with the exercise gives no verdict. For a variant, the displayed task is the checked task.
3. **A verdict names its source.** Against the material's solution, the app says the answer
   matches or does not match the stored solution; a valid key does not prove the solution was
   transcribed correctly or that the material is right. When the code also computes the solution,
   it may say so. The source stays visible to the student.
4. **Stored and computed solutions disagree → no verdict.** The app shows that the solution needs
   review, without disclosing it while the exercise is open; the stored solution is not
   overwritten and stays available; nothing is recorded.
5. **Expression equivalence only where it can be established** for the expression's class; sample
   points alone are not proof. Otherwise the result is « not reliably checkable » and Célestin
   guides without a verdict; spec 022 treats such an item as self-assessed.
6. **Multiple choice** shows a verdict only when the card is bound to a key and the checker
   evaluated the pick; a model-chosen correct option no longer justifies one. Supersedes design
   proposal D2 (« `check_question` unchanged »).
7. **Révision records the checked exercise**, with date and source, beside the self-assessment; a
   single verdict does not set a section's outcome. Replaces the earlier mapping of a verdict to
   `solid` / `shaky` / `todo`.

Open after the review: the exact contract with spec 022, and the implementation details of the
binding, multiple choice, result storage, conflict handling and equivalence classes; the design
proposes them for the owner's review.

## 8. Decisions after the textbook check (owner, 22 November 2026)

Evidence: Cornelsen's *Fundamente der Mathematik* NRW, grades 5 and 9, supplied by the owner and
not stored in the repository (findings summarised here, no excerpts).

1. **Solutions marked as rounded.** A solution the material writes with `≈`, « rund » or « ca. »
   counts as a stated rounding rule, at the solution's own decimals: an answer that rounds to it
   at those decimals is correct (more decimals allowed); fewer decimals is `precision`. A rule in
   a note that governs the exercise (« Runde immer auf zwei Nachkommastellen, wenn nichts anderes
   angegeben ist »), and « Runde sinnvoll », count as stated. Rounding to tens, hundreds or
   thousands is a rule too. Without any of these, §7.1 holds: exact. (About 45 % of the solutions
   in the grade 9 chapters on similarity and circles are rounded with no rule in the task.)
2. **Exact roots are numbers.** `2√2`, `(3 + √2) cm`, `x₁ = −3 + √2`, `L = {1 − √7; 1 + √7}` are read
   and compared exactly; an equation whose solutions are of that form is checkable without a
   rounding rule.
3. **Required unit or form.** When the exercise asks for a unit (« Rechne um in dm² ») or a number
   form (fraction, mixed number, decimal, scientific notation, « kürze », « Vereinfache … zu einer
   Potenz »), the answer must have it: the right value in another unit or form is not correct.
   A required *expression* form (« Scheitelpunktform », « faktorisiert ») is not checked in this
   spec: the checker settles the value and says the form is unchecked; nothing is recorded.
4. **Textbook references and solutions**: R1.4a.
5. **Figures.** An exercise that needs a figure, a diagram or a measurement on the page is not
   bindable in this spec (no verdict); « Miss … » tasks never get a key.
6. **Further readers and kinds**: mixed numbers (`2 1/4`, never read as `21/4`), repeating decimals
   (`0,1̄`), powers of ten (`1,15 · 10⁴`), division with remainder (`4 Rest 7`), `±`, `x₁ = …, x₂ = …`,
   « keine Lösung », `L = ℝ`, « nicht definiert »; units `€`/`ct`, `°C`, days; « Ordne zu » as the kind
   `mapping`; « richtig oder falsch? Begründe »: only the choice is checked, the reason is not.
7. **Equations**: besides polynomials of degree ≤ 4, equations with the variable in a denominator
   (`24/x = 3`, Strahlensätze) and pure powers (`x⁵ = 1024`, `x⁻² = 1/9`) are solved by code.
