# Spec 023 — Answer checker: mechanical verdicts on final answers

Status: requirements, consolidated on 22 November 2026 after four review rounds and a textbook
check. This file states the current requirements; the owner's decisions and their history are in
`decisions.md` (§§6–14), the reviews in `specs/023-review*.md`. Delivered in three stages
(**023a**, **023b**, **023c**); each requirement names its stage. Foundation of spec 022
(practice test).

## 1. Introduction

Today no answer is checked by code. The tutor prompt says Célestin cannot check a calculation
with certainty and never declares « juste » or « faux » (`tutor.<lang>.md`); révision records
only the student's self-assessment (spec 020 D3); a `check_question` card carries a
`correct_option_id` the model chose, and the browser colours the student's pick from it: a
verdict that is the model's word.

This spec adds a **checker**: deterministic code that compares a student's final answer with an
answer key and returns a verdict, with no model judging the answer:

1. **Checkable keys in the pack**, copied from the material's solution by the authoring agent,
   validated when the chapter is prepared and when the pack is edited; optionally with the
   exercise's task in a form the code can compute, so the stored solution can be recomputed.
2. **An exact checker**: one reader and one comparison per answer kind and course language.
3. **Bound exercises**: when Célestin sets a checkable exercise, the server stores it with its
   checking data and shows exactly what is checked.
4. **Direct checking of a submission**: the student answers in the card's field or picks an
   option (023a), or confirms a candidate from chat (023c); the server checks at once and stores
   the submission and its verdict. Célestin reads the verdict on its next turn; the model never
   runs, chooses or changes a check.
5. **A per-exercise record in révision** beside the self-assessment, and review labels (023b).

Expected coverage (textbook check, `decisions.md` §8): a German Gymnasium textbook prints solutions
only for its self-test and review pages, about a quarter of its exercises; of those, about half to
three-fifths of the sub-answers in algebra and a third in geometry are of a checkable kind.
Variants settled by code carry the rest of the practice.

### 1.1 Answer kinds

| Kind | Key | Verdict |
| --- | --- | --- |
| `choice` | option id among the exercise's ids (`richtig`/`falsch` included) | equal; a reason given after a true/false choice is not checked |
| `number` | exact value (decimal, fraction, mixed number, repeating decimal, `a + b√c`, `a + bπ`, power of ten, `q Rest r`), optional rule, unit, required form | exactly equal after exact unit conversion, unless a rule applies (§1.3); a required unit or number form must be met |
| `expression` | one-variable expression, optional stated domain | equivalent only where value **and** domain equality can be established exactly; else « not reliably checkable »; a required expression form is not checked and said so |
| `interval` | bounds, ends, unions | same bounds and ends |
| `solution_set` | finite set of exact values, the empty set, `ℝ` | same set, order and repetition ignored |
| `point` | coordinates | same coordinates |
| `word` | accepted words from the pack's vocabulary | equal after normalising case, spaces, accents (accents kept where the subject requires) |
| `mapping` | pairs (« Ordne zu »: `A–2, B–1`) | same pairs |

Every kind reads the student's text in the **course's** notation (`by_language` tables): decimal
comma or point, thousands grouping, `]a; b[` or `(a, b)`, `P(2 | −1,5)` or `(2, −1.5)`, `%`.
Fractions and decimals of the same value are equal (`3/4` = `0,75`) unless a form is required.
An answer may start with `≈`, « rund », « ca. ».

### 1.2 Variants: settled by code

A variant (the course's exercise with other numbers) has no key in the material. It is checkable
only when the code settles the answer itself and the student sees exactly the task that is
checked (the server generates the statement from the checking data):

- **Evaluate** an expression at given values → the code computes the key.
- **Solve** an equation or inequality of a supported class (polynomial of degree ≤ 4, variable in
  a denominator, pure power `x^n = c`) → the code computes the **complete** solution.
- Anything else (a derivation, a proof, a word problem whose relation cannot be verified against
  the data) can be posed and discussed, without a verdict.

### 1.3 Exactness and rounding

- Exact by default: a key of `5` accepts `5` and `5,0`, not `5,4`; `90 km/h` = `25 m/s` exactly.
- A rounding rule applies when the exercise or a note governing it states one (« auf zwei
  Nachkommastellen », « auf Zehner »), or when the material marks its solution `≈`, « rund »,
  « ca. » (then at the solution's own decimals). An explicit tolerance `±t` likewise.
- « Runde sinnvoll » or another vague instruction, without an unambiguous rule in the material, is
  not a rule: the rounding gets no verdict.
- A computed approximate value gets a verdict only when its rounding is certified unambiguous,
  and a computed solution set only when it is proven complete.

### 1.4 What a verdict says

- **Source**: against the material's solution the app says the answer matches or does not match
  the stored solution (a valid key does not prove the material is right); a computed key says
  « recomputed »; both when both agree. The source is always visible.
- **Disagreement**: when the stored solution and the code's computation disagree, there is no
  verdict; the app says the solution needs review, without disclosing it; the stored solution is
  not overwritten.
- **No verdict** (« not reliably checkable ») whenever the code cannot settle the answer: then
  Célestin guides as today.

## 2. Alignment with product vision

- Principle 4 (brief §5): *it never grades from impression; where an answer is mechanically
  checkable, the verdict comes from a checker*. This spec builds that checker and removes the one
  verdict today that is the model's word (`check_question`).
- Brief §12.1 and phase C « a mechanical checker feeding the same record »: answered for the kinds
  of §1.1; spec 020 D3 « when a mechanical checker exists, it feeds the same record »: per exercise,
  beside the self-assessment (R5).
- Principles 1 and 2: keys come from the student's material, copied, never invented.
- Principle 3: no verdict, card or message reveals the key while the exercise is open.
- Spec 022 (practice test) depends on the keys, the binding, the checker and its case tables.

## 3. Requirements

### R1. Checkable keys in the pack (023a)

As a student, I want the solutions of my material turned into keys the code can check, so that my
answers to the course's exercises get a reliable verdict.

1. Each pack template (`templates/<subject>.pack.<lang>.md`, every subject and course language)
   asks, per typical exercise with a solution in the material, for its answer kind and key in the
   fixed form, next to the existing answer line.
2. An exercise with several questions carries one key per sub-question (`6.1.2 a)`); a sub-answer
   with several quantities one key per named part (`6.1.2 a) u`, `6.1.2 a) A`).
3. No key for an exercise without a solution in the material, whose solution the agent flagged in
   « points to check », or whose answer is not of a kind of §1.1; no key for a task that needs a
   figure, a diagram or a measurement on the page (« Miss … »).
4. The agent copies the key; it never computes one. It writes a rounding rule only as §1.3 allows,
   and a required unit or form only when the exercise asks for one.
5. Textbooks: each pack exercise keeps the material's reference (« S. 128, Nr. 11 »); solutions
   printed elsewhere are joined to their exercise by that reference; an unordered pool of answers
   (« Lösungen zu 5 ») never becomes a key and is never copied into a statement.
6. A key may carry the exercise's task in the fixed form (copied from the statement) when the task
   is of a class the code computes; the code then recomputes the solution (§1.4).
7. `domain/pack.py` validates every key on preparation and on edit: known kind, readable in the
   course's notation, existing exercise, an `expression` key within the supported class. An
   invalid key is a content issue the agent repairs (bounded); one that cannot be repaired is
   dropped with a « points to check » entry, never stored invalid.
8. Packs stored before this spec stay valid; their exercises have no key.
9. The pack editor shows and validates keys like any other pack content; the pack view shows which
   exercises are checkable and which need their solution reviewed.

### R2. The checker module (023a)

As a developer, I want one deterministic module that settles answers, so that every mode and spec
022 share the same verdicts.

1. Input: kind, key, the student's answer text, the course language. Output: `correct`,
   `incorrect`, `unreadable` (with an example of the expected form), `precision` (right value, not
   rounded as the rule asks), `unit_differs`, `form_differs` (right value, not in the required unit
   or number form), `form_unchecked` (expression value right, required form not checked), or
   `undecided` (not reliably checkable); each with its basis (material, computed, both).
2. Exact arithmetic: rationals, surds `a + b√c` and `a + bπ` compared exactly; unit conversions
   exact; rounding of approximate values only when certified (§1.3).
3. No model call, no I/O, no randomness; bounded work: exceeding a limit is `undecided`, never a
   verdict.
4. Imports no SDK and no catalog; text it returns to the model is in the course language, text for
   the student goes through the catalog (spec 010).
5. A case table per kind and course language (accepted, refused, unreadable, undecided), shared
   byte-identically with the frontend where it parses the same notation.
6. Reuses the readers `NUMBER`, `INTERVAL`, `COORDS`, moved to a shared module, and the grammar of
   `domain/expression.py` through an **exact** mode that keeps numbers as written; the plotting
   parser's behaviour does not change.
7. Unreadable is not incorrect: the student is told the expected form and answers again.

### R3. Bound exercises and direct submission

As a student, I want my answer checked against the exercise I was actually given, so that the
verdict is about that exercise and nothing else.

1. **Binding (023a).** When Célestin puts a checkable exercise on the board it names its checking
   data (a pack reference or a variant task). The server validates it and shows exactly what is
   checked: for a pack exercise, its statement from the pack (the shared stem and the one
   sub-question), cut before any answer or key line; for a variant, the statement the server
   generates from the task. A card that cannot be bound reliably (cut not found, figure needed,
   word problem not verifiable, key needing review) is shown without an answer field.
2. **Activation (023a).** A bound card is stored with its turn; its answer field becomes active
   only when the server confirms that the turn was stored. A failed store, a stopped turn reported
   afterwards, or a card whose révision closed in the same turn leaves the card without an active
   field (the last with the reason).
3. **The answer is the student's.** 023a: the card's own field, or a pick on a bound choice card,
   is submitted whole. 023c: an answer written in chat becomes a submission only after Célestin
   proposes it and the student confirms or corrects both the answer and the exercise; the
   candidate text comes from the student's message, never from the model.
4. **Direct checking (023a).** The server checks a submission at once, without a model call, and
   stores the submission and its verdict together; the card shows the verdict and its source. A
   later model turn neither waits for nor changes it. A retried request gives the same result and
   no duplicate; a new attempt is a new submission.
5. No correct/incorrect verdict for an unknown, foreign, stale or unbound exercise, a key needing
   review, or an answer the code cannot settle.
6. Célestin receives the stored verdict and its basis on its next turn, never the key. The board
   and transcript restore the verdict on its card on reload.
7. A bound parcours card stays usable across a séance rollover and a return to its section, within
   the same student, chapter, section and content version. A content change, reset or deletion
   invalidates it; a révision card is usable only while its révision is open.
8. Available in parcours and révision, not in discussion.
9. **Not in voice.** A card created in a voice session is not bound and a spoken answer is not
   submitted; a card created in a stored text turn keeps its field while a voice session runs.
   Text dictated into the composer and sent by the student is text input. Checking spoken answers
   is a later spec.

### R4. The tutor and the choice card (023a)

As a student, I want « right » or « wrong » to come from the code only, so that I can rely on it.

1. The tutor prompt (every course language): use the stored checker verdict and its source; never
   declare a verdict without one; otherwise guide without a verdict, as today. This is tutor
   behaviour, measured by real-model probes; the authoritative verdict is the one on the card.
2. After `incorrect`, the usual tutoring: questions and hints, no answer.
3. A choice card shows a verdict only when bound to a `choice` key and checked. Otherwise it shows
   the pick and no verdict, and no model-written feedback, in every mode (parcours, discussion,
   révision, notebook), stored cards included.

### R5. Checked exercises in the révision record (023b)

As a student, I want the exercises the code checked in révision kept with my self-assessments, so
that the next révision starts from what the code saw too, without pretending one answer proves a
whole section.

1. In 023a a révision verdict is on its card and in the transcript only. From 023b, each new
   révision submission with a recordable verdict (`correct`, `incorrect`, `precision`,
   `unit_differs`, `form_differs`) is also recorded as the result of **that exercise** (pack
   reference or variant task), with date, verdict, basis, chapter and section, in the
   submission's own transaction. Earlier submissions are not imported.
2. A checker result never sets or changes the section's self-assessment and never marks a section
   as mastered.
3. The « Bilan » and the révision's state message show per section the latest self-assessment and
   the checked exercises with verdict, source and date.
4. Célestin still asks for the student's self-assessment (spec 020 D3).
5. Parcours verdicts stay in the séance transcript; they do not move the path and are not recorded
   in révision.
6. **Review labels.** An exercise the material explicitly labels as review of earlier material
   keeps that label in the pack and is shown apart in the Bilan; no label is inferred. The student
   can correct a label; the correction is stored outside the pack and resets no progress.
7. Summaries over several checked exercises belong to spec 022.

## 4. Non-functional requirements

### Architecture
- Rules in code: key, binding, activation, submission and verdict are enforced by the server and
  the checker, not by prompt text.
- Every per-language table is a `by_language` table; a missing language fails at import.
- French output of existing tools, prompts and renderings is byte-identical except where this spec
  changes it on purpose (tutor prompt rule, pack templates, exercise and choice cards); pins are
  regenerated deliberately.
- Existing tool order stays fixed; a new tool is appended and can neither submit nor grade.
- `test_language_is_passed.py`, `test_model_input_wall*.py` and `test_route_guards.py` cover the new
  code.

### Performance and cost
- Checking is local and bounded; no model call for a verdict.
- Keys add a few lines per exercise to the pack and its cached prefix.

### Security and privacy
- Model and browser input are untrusted: arguments validated, keys and tasks parsed by a closed
  grammar, ownership, mode and content version checked on every submission.
- Logs and the usage ledger carry ids, kind, verdict and basis, never answers or keys.
- Submissions and results are the student's, deleted with the account, course or chapter.

### Reliability
- Case tables pin every reader per language; a notation change edits the table in the same commit.
- Without a usable key, a verdict or an active field, the student gets today's guidance, never an
  error.

### Usability
- Verdict mark, source, « expected form », « not reliably checkable », « solution needs review » and
  « révision full » in French, English, Dutch and German; examples in the course's notation.
- The answer field and the choice buttons work with keyboard and screen reader.

## 5. Out of scope

- The practice test itself (spec 022), including summaries over several checked exercises.
- Checking working steps, derivations, proofs, justifications, drawn graphs, the reason given for a
  true/false choice.
- A general computer algebra system; required forms of expression answers (« Scheitelpunktform »,
  « faktorisiert »): the value is checked, the form is not.
- Exercises that depend on a figure or a measurement on the page.
- Checking in voice (cards created in a voice session, spoken answers): a later spec.
- Graded class test analysis and correction review (follow-ups named in spec 022).
