# Spec 022 — Practice test: a timed test over chosen chapters, checked mechanically

Status: requirements only, parked by the owner (22 November 2026). Not to be designed or built
until the owner resumes it.

## 1. Introduction

A fourth way to work on a course. The student picks the chapters a coming test covers, sets a
duration, and sits a practice test: a fixed sheet of questions drawn from those chapters, answered
without Célestin's help and without hints. When the student hands it in (or the time is up), every
answer that can be checked mechanically is checked by code, not by the model; the rest is
self-assessed against the course's own wording. The result is shown per section and feeds the
révision record (spec 020), so the next révision and the open path start from what the test showed.

Value: the student learns *before* the real test what holds under test conditions (no help, time
pressure, mixed chapters), with a verdict they can trust, and is sent to the sections to work.

### 1.1 What « mechanical check » means here

A verdict computed by deterministic code from the student's final answer and an answer key, with
no model judging the answer. In scope for this spec:

| Answer kind | Check |
| --- | --- |
| Choice | the chosen option id equals the key's (`CheckQuestionCard.correct_option_id` already holds one) |
| Number | equal to the key within a stated tolerance or rounding, read in the course's notation (`,` or `.` decimal, thousands spacing, `%`), optional unit compared to the key's unit |
| Expression | equivalent to the key: both parsed by the closed grammar of `domain/expression.py` and evaluated at sample points of a stated domain; the key's form may also be required (e.g. « factorised ») when the item says so |
| Interval / set of solutions | same bounds and same open/closed ends, read in the course's notation (`]a ; b[`, `(a, b)`, …) |
| Point / pair | same coordinates, read in the course's notation (`P(2 \| −1,5)`, `(2, −1.5)`) |
| Exact text from a closed list | a vocabulary word or a unit from the pack, after normalising case, spaces and accents |

Anything else (a definition to recite, a justification, a derivation, a drawn graph, a proof) is
not mechanically checkable and is self-assessed (R6).

## 2. Alignment with product vision

- Job « Do I actually know this? » (brief §4) and the student's motivation, the next test (§3.1).
- Principle 4, *it never grades from impression*: this spec is the first to issue verdicts, and
  only through a checker. Brief §12.1 (checking outside maths) is partly answered here for the
  answer kinds of §1.1.
- Spec 020 D3: « When a mechanical checker exists, it feeds the same record. » This spec is that
  checker and that feed.
- Principle 2 and 3: items come from the student's material (pack), and no answer is shown while
  the test is open.
- Principle 8: the student chooses chapters, duration and when to hand in; the test does not move
  the path.

## 3. Requirements

### R1. Start a practice test

As a student, I want to start a practice test on the chapters my coming test covers, so that I
rehearse under test conditions.

1. A course page action opens a chooser of the course's ready chapters (as révision's, spec 020),
   at least one chapter required.
2. The student chooses a duration from a short list (e.g. 15, 30, 45, 60, 90 minutes) or « no
   limit ».
3. The student may choose the share of items per chapter, default even; the number of items
   follows from the duration.
4. Starting is refused with a message when the chosen chapters offer no checkable item and no
   self-assessable item.
5. One live practice test per student and course; starting another closes the live one.
6. A daily quota per student bounds the number of tests started (setting, like
   `REVISION_SESSIONS_PER_DAY`).

### R2. The test sheet

As a student, I want a fixed sheet of questions, so that I know the whole test and can manage my
time.

1. The sheet is composed once, at the start, and does not change while the test is open.
2. Items come only from the chosen chapters' packs: their « typical exercises » (pack §6) with
   their answers, their definitions and vocabulary, and variants of those exercises.
3. Every item names, for the record, the chapter and the section it belongs to; the sheet does not
   show it to the student (recognising which notion to use is part of the test).
4. Every item is marked *checked* (it has an answer kind of §1.1 and a key) or *self-assessed*.
5. Items are mixed across the chosen chapters.
6. The sheet's notation, wording and language are the course's (spec 011): an item uses the
   pack's notation and vocabulary.
7. The sheet is stored, so a reload or another device shows the same sheet, answers and remaining
   time.

### R3. Answer keys never come from the model's word alone

As a student, I want every verdict to be right, so that I can trust the result.

1. A key is the pack's « Antwort » for an exercise taken as it is, or a value the checker computes
   from the item's own data (a variant states its parameters and the course's expression; the code
   evaluates it).
2. A key the model asserts and the code cannot derive or confirm is not a key: the item is
   self-assessed, or it is dropped from the sheet.
3. An exercise whose pack answer is « not corrected in the material », or listed under « points to
   check » (pack §7), is not a checked item.
4. Composing a sheet whose keys fail these rules is refused and repaired a bounded number of
   times, as authoring stages are (spec 005); a sheet that cannot be repaired fails with a message,
   and nothing is recorded.

### R4. Test conditions

As a student, I want the test to behave like a real one, so that its result means something.

1. While the test is open, there is no hint, no explanation, no worked example and no reveal;
   Célestin does not converse about the items. A question the student types to Célestin is
   answered only with a one-line reminder that help comes after handing in.
2. A visible timer counts down when a duration was chosen; at zero the sheet is handed in as it
   is.
3. The student can hand in early, after a confirmation.
4. Each item has a final-answer field typed by the student; a checked item also accepts an
   optional working field. A photographed working can be read through the existing work-reading
   route (`POST /api/courses/{id}/work`): the student corrects the reading, and only text is
   kept.
5. Answers are saved as they are typed, so nothing is lost on a reload or a dropped connection;
   the timer runs on the server's clock, not the browser's.
6. An unanswered item counts as unanswered, not as wrong, in the report, and as « à revoir » in
   the record (R7).

### R5. Mechanical checking

As a student, I want my answers checked by the code, so that a verdict never depends on the
model's impression.

1. Every checked item is checked when the sheet is handed in, by the checker of §1.1, with the
   course language's notation tables (`by_language`).
2. The verdict of a checked item is one of: correct, incorrect, unreadable (the answer cannot be
   parsed as the item's kind). Unreadable tells the student what form was expected; it is not
   counted as incorrect.
3. The checker is deterministic and runs without a model call; the same answer and key always give
   the same verdict.
4. The checker is one module with a case table per answer kind and per course language, tested
   like the board's notation tables (`notation_cases.json`).
5. The model never changes a verdict. Célestin may comment on it afterwards (R8), never overrule
   it.

### R6. Self-assessed items

As a student, I want items the code cannot check to count too, so that definitions and reasoning
are part of the test.

1. After hand-in, each self-assessed item shows the course's own wording or method from the pack,
   beside the student's answer.
2. The student marks it « acquis », « fragile » or « à revoir », as in révision (spec 020 D3).
3. The report keeps self-assessed results visibly apart from checked ones.

### R7. Report and record

As a student, I want a result per section, so that I know what to work on next.

1. The report lists per chapter and section: checked items correct / incorrect / unreadable /
   unanswered, and self-assessed items with their mark.
2. A summary per chapter: the share of checked items correct. No school grade is computed.
3. Each section tested gets one result in `revision_results` (spec 020), marked as coming from a
   practice test (distinct from a révision self-assessment): all of its checked items correct →
   `solid`; some correct → `shaky`; none correct or unanswered → `todo`; a section with only
   self-assessed items takes the student's worst mark.
4. The next révision's opening and « Bilan », and the course page, show these results with their
   source (test or self-assessment) and date.
5. Each weak section links to its parcours section and, when done, to its cahier.
6. Results are recorded only when the sheet is handed in; a test closed without hand-in records
   nothing.

### R8. Correction with Célestin

As a student, I want to go through my mistakes with Célestin after the test, so that I understand
them.

1. After hand-in, the student can open a correction conversation on the test: Célestin sees the
   sheet, the answers, the verdicts and the keys.
2. The usual tutoring rules apply again: questions and hints first; the key may be shown since
   the test is over.
3. The correction does not change a verdict or a recorded result; a new self-assessment in the
   correction is a new révision-style result.

### R9. Past tests

As a student, I want to see my past practice tests, so that I see my progress over time.

1. The course lists its past practice tests: date, chapters, duration, summary per chapter.
2. A past test reopens read-only: sheet, answers, verdicts, keys, marks.
3. Deleting the course, a chapter or the account deletes its tests and their results.

## 4. Non-functional requirements

### Architecture
- A mode and a tool set on the existing machinery (spec 020 D1): a value in `domain/mode.py`, its
  prompt files in every course language, a row in `_MODE_TOOLS`; no second turn loop.
- Rules live in the tools and the checker, never in prompt text: no-help while open, keys, verdicts
  and recording are enforced by code.
- The checker lives in `domain/` or `services/` without any model or SDK import; nothing above
  `app/providers/` imports `openai`.
- Every per-language rule of the checker is a `by_language` table; French behaviour of existing
  modes is byte-identical.
- The SSE contract gains only the events this mode needs; the frontend types and the design
  document change with it.

### Performance and cost
- Composing a sheet is one bounded model call (or a bounded repair loop), cached on the chosen
  chapters' packs like révision's prefix.
- Checking is local and instant; handing in makes no model call.
- `REVISION_MAX_PACK_CHARS`-like bound on the chosen packs.

### Security and privacy
- Every route declares its roles (`require_roles`); a test belongs to the student who owns the
  course (404 otherwise).
- Sheets, answers and results are rows owned by the student; logs and the usage ledger carry ids,
  counts and durations, never answers or items (spec 015).
- The timer and hand-in are enforced server-side; the browser cannot extend a test or change a
  verdict.

### Reliability
- An answer saved is never lost by a reload, a dropped connection or a server restart.
- A provider failure while composing leaves no half-built test and no result.
- The checker's case tables pin its behaviour per language; a change to notation parsing changes
  the table in the same commit.

### Usability
- Interface copy in French, English, Dutch and German (spec 010, 017, 021); the sheet in the
  course's language.
- The expected answer form is shown per item (« number », « interval », « expression ») with an
  example in the course's notation.
- Works at phone width; the timer stays visible while scrolling.

## 5. Out of scope

- A school grade (Note, points out of 20) — open question.
- Voice during a test.
- Checking drawn graphs, proofs, free-text justifications (brief §11).
- Tests across several courses.
- Follow-up candidates, each its own spec:
  - **Graded class test analysis**: the student photographs a test written and marked in class;
    its items and the teacher's marks are mapped to the course's sections and feed the same
    record, so révision and the path target what the class test showed.
  - **Correction review**: on such a photographed class test, the checker of §1.1 flags items
    whose mark disagrees with a mechanical check, as points to ask the teacher about (never as a
    verdict on the teacher's correction).

## 6. Open questions

1. A school grade: should the report offer one, on which scale per country (FWB /20, NRW 1–6)?
2. Variants: may the sheet hold model-written variants of exercises at all, or only the pack's
   exercises as they are plus choice questions, until the checker can confirm a variant's key?
3. Partial credit for multi-step items: one final answer per item, or several checked sub-answers?
4. Should a test date on the course (brief §12.6) propose a practice test a few days before?
