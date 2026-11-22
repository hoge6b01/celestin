# Spec 023 — decision log

The owner's decisions on spec 023, in the order they were taken (22 November 2026). Until the
consolidation of `requirements.md` and `design.md` (§14) these were sections §6–§13 of
`requirements.md`; the review notes in `specs/023-review*.md` and `specs/023-design-proposal.md`
refer to them by these numbers. Later sections refine or supersede earlier ones where they say
so. The current rules are stated in `requirements.md` and `design.md`; this file is the history.

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
   angegeben ist ») counts as stated. « Runde sinnvoll » alone is not a concrete rule: if the
   material and marked solution do not establish one unambiguously, do not grade the rounding
   (§9). Rounding to tens, hundreds or thousands is a rule too. Without any of these, §7.1 holds: exact. (About 45 % of the solutions
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

## 9. Follow-up review decisions

The user agreed to the decisions recorded in `specs/023-review-followup.md`. They refine §§7–8:

1. Different or not reliably established expression domains give no equivalence verdict; the
   relevant exercise domain and preserved exclusions must be specified.
2. The learner's answer must be unambiguously delimited and bound to the exercise; ask when
   uncertain. A substring match is insufficient, including for text, selections and voice.
3. Computed solutions yield a verdict only when all relevant solutions and any rounding can be
   established reliably; otherwise return not reliably checkable.
4. Old multiple-choice cards retain the question and any recorded selection, but no unverified
   correctness mark or model-authored automatic feedback. A checker verdict shows its source.
5. Exercises explicitly labelled as review retain the label so the revision overview can show
   them separately. Do not infer a label where the material is ambiguous.
6. A vague rounding instruction without an unambiguous rule gives no rounding verdict.
7. A variant is checked only if the displayed task and its checking data reliably agree; merely
   adding a computed task line next to unverified model text does not establish agreement.

Implementation details and verification evidence for these decisions need design review before
planning; the contract with spec 022 is deferred until that spec is resumed.

## 10. Subsequent design review decisions

The user agreed to the directions documented in `specs/023-design-proposal.md`:

1. Use a dedicated answer field on the checkable card; bind choice selections to that card. Also
   allow answers in chat, showing the proposed answer and exercise for confirmation or correction
   before checking. For voice, show the recognized answer for confirmation or correction. The
   detailed voice and accessibility interaction remains to be designed. (Voice superseded by §12.1.)
2. Begin expression checking with cases where the relevant domain and equivalence can both be
   determined exactly. Unsupported or uncertain cases have no verdict; the class can grow later.
3. Require a complete, reliable set of solutions and unambiguous rounding before a verdict,
   including for cubic and quartic equations.
4. Store an explicitly marked review label with the pack exercise, show it in the revision
   overview, and allow the learner to correct it (the correction is stored outside the pack,
   §13.7). Do not infer the label from ambiguous material.
5. Generate the checkable statement of a purely mathematical variant from its checking data. A
   word problem whose agreement with those data cannot be reliably established can still be
   posed and discussed without an automatic verdict.

The draft's proposed algorithms, message contracts and implementation details remain for design
review; these decisions do not approve an implementation plan.

## 11. Reconciliation of Claude's review

At the user's request the design incorporates `specs/023-review-claude.md` with these decisions:

1. Direct server checking and atomic recording on confirmed submission replace the model's
   `check_answer` call and the requirement to wait for a successful model turn. The existing
   spec 020 transaction for self-assessments is unchanged. Confirmation, ownership and idempotency
   remain required. A later model failure cannot erase an already committed learner action.
2. Text-turn presentations become eligible only when stored with their card. Parcours rollover
   and section return do not invalidate eligible presentations; resets, content changes, closed
   revision runs and cross-user/cross-mode use do. Voice presentations are persisted by the trusted
   server before submission and reconciled with the reported transcript. Voice checking remains in
   scope; revision voice remains out of scope. (Voice superseded by §12.1.)
3. A supported explicitly stated answer domain can be checked against the required domain; an
   unsupported or ambiguous domain gives no verdict. Certified algebraic root rounding must
   establish the relevant root and rounding boundary exactly; resource exhaustion is inconclusive.
   Exact supported surds and bounded rational linear forms in π cover common geometry cases;
   rounding π requires certified rational bounds, and unsupported forms give no verdict.
4. Work may be phased, but chat, voice confirmation, revision results and review labels remain in
   scope (voice superseded by §12.1; phases fixed by §12.2). `specs/023-review-claude.md` retains the original review; the updated design still needs
   review before a task plan or implementation.

## 12. Scope decisions (owner, 22 November 2026, after `specs/023-review-reconciliation.md`)

1. **Voice checking moves to a later spec.** This spec checks only answers given through a card's
   field, a choice card, or a confirmed chat candidate, on cards presented in stored text turns.
   Cards created in a voice session are shown unbound; spoken answers are not confirmed or
   submitted. The later spec takes over the server-side recording of voice presentations at
   `/api/voice/tool` and their reconciliation with `/api/seance/report`. Révision has no voice.
2. **Three planning stages**, each shippable on its own, in this order:
   - **023a**: keys and authoring, the exact checker, stored presentations, the card answer field
     and bound choice cards, direct checking on submission, verdict display and replay, in the
     parcours (and révision display, without its record);
   - **023b**: the révision record per exercise (`exercise_results`) and the review labels;
   - **023c**: chat candidates with `propose_answer` and the learner's confirmation.

## 13. Decisions on the second ChatGPT review (owner, 22 November 2026; `specs/023-review-chatgpt-2.md`)

1. **F1, stage boundary.** In 023a a révision verdict lives on its card and in the transcript (with
   replay and the tutor's next-turn context), with no per-exercise record and no Bilan entry. 023b
   adds `exercise_results` for new submissions only; earlier submissions are not imported.
2. **F2, card activation.** A checkable card's answer field becomes active only on a dedicated
   « turn stored » signal that names its exercise IDs and is sent only after the turn's store
   succeeded; `turn.end` alone never activates it. On a failed store the field stays disabled; on
   reload the stored state decides. Cards in a stopped turn that the browser reports afterwards
   stay unbound.
3. **F3, chat candidates (023c).** The server assigns the learner's message an ID when the turn
   starts. `propose_answer` refers to that message; the candidate text comes only from it, never
   from the model, and the proposal becomes active only once the turn is stored (§13.2).
4. **F4, choice cards in every mode** belong to stage 023a: old stored fields are still read but
   ignored; no choice is coloured without a checker verdict in any mode.
5. **F5, voice wording.** What counts is where a card was **created** (R3.8). The earlier voice
   concept is kept in a design appendix as input for the later voice spec; the earlier notes that
   keep voice in scope are marked as superseded by §12.
6. **F6, tutor prose.** « No verdict without the checker » in Célestin's free text is measured tutor
   behaviour (prompt rule plus real-model probes with a pass threshold), like today's rule; only the
   verdict on the card, with its source, is authoritative, and the interface says so.
7. **F7, review labels.** The learner's correction of a review label is stored outside the pack,
   as a per-exercise override; it does not change the pack's content version and so does not reset
   progress.
8. **F8, exact parsing**: R2.6.
9. **Dictation** into the composer is text input (R3.8).

## 14. Decisions on the third ChatGPT review and consolidation (owner, 22 November 2026; `specs/023-review-chatgpt-3.md`)

The owner judged the remaining findings to be details, not objections, and followed Claude's
recommendation:

1. **N1–N5 are corrections, made in the consolidated design**: `propose_answer` refers to the
   running turn's learner message and becomes active with `turn.stored`; a card whose révision is
   closed in the same turn is stored but not eligible (shown as unavailable, « this révision is
   full »); reported stopped-turn cards are never bound; `turn.stored` carries `exercise_ids`
   (023a, may be empty) and `message_id` (023c, null without a learner message); révision
   transaction wording is qualified by stage; the choice card has a declaration model without the
   legacy fields and a lenient reading model for stored and reported cards.
2. **N6, N7 (label overrides, `exercise_results` versions and deletion)** are decided when stage
   023b is planned. Claude's recommendation for then: an override belongs to one content version
   (any pack change discards it; a progress reset keeps it; the learner can return to the
   material's label); `exercise_results` mirror `revision_results` (content version stored, reads
   at the current version, cascades on account, course, chapter; `SET NULL` on conversation).
3. **N8 (probe metric)** is decided when the checker probes are written: semantic judgment of
   paraphrased verdicts, a denominator and a pass threshold per language.
4. **Consolidation.** `requirements.md` and `design.md` are rewritten as the current state, with
   the stage of each part (023a, 023b, 023c); §§6–13 move here unchanged. No further review round:
   the next step is the plan for stage 023a only.
