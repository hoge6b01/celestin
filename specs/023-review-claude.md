# Spec 023 — review by Claude (22 November 2026)

A review of the follow-up work: commit `e673498` (requirements §9) and the then-uncommitted revision
on top of it (requirements §10, the revised `design.md`, `specs/023-design-proposal.md`). It
checks the proposals against how the application stores turns today. **These are proposals, not
decisions.** Items 1, 3, 4 and 9 change agreed requirements or scope and need the owner's
decision; the others are design corrections.

What the follow-up rightly replaced:
- the substring check, by a learner-confirmed submission;
- the HMAC exercise id, by a server-stored presentation;
- common-domain equivalence, by proven domains;
- also the completeness and rounding conditions on computed solutions.

## 1. The model is no longer needed in the checking chain (high; changes R3.2, R3.5, R3.6)

Once the server stores a confirmed submission, it can check it at once. The chain « submission → next
turn → model calls `check_answer(submission_id)` » only adds failure modes (the model does not call
it, calls it late, or names an older submission), and it creates the streaming problem §3.10 tries
to solve with a buffer.

Proposal:
- The submission route checks deterministically and stores the verdict. In révision it writes the
  `exercise_results` row in the submission's own transaction: it is the learner's act, not a model
  turn.
- Célestin receives the verdict and its basis as context on the next turn, never the key.
- For chat and voice candidates, one tool `propose_answer(exercise_id, answer)` shows a confirmation
  chip; the learner's confirmation calls the same route.
- `check_answer`, the streaming buffer and the cross-turn idempotency rules then disappear.

## 2. Presentations are written too early (high)

§3.10 records a presentation « before emitting a checkable card ». A turn is stored in one write
when it ends (`services/conversations.append`, « one write, after the turn ended »). A stopped or
failed turn would leave presentation rows for cards the transcript never held.

Proposal: store presentations in the same end-of-turn transaction as the transcript, and enable a
card's answer field only after the turn is stored.

## 3. Scoping a presentation to one conversation row is too narrow (high)

A conversation row closes when it crosses its caps (`capped`), and parcours séances split when a
turn is stored (spec 018). « A presentation from another conversation, closed conversation … is
refused » would refuse an exercise shown just before such a rollover.

Proposal: scope by user, chapter, section, content version and mode, not by the row.

## 4. Voice is larger than described (medium-high; changes R3.8)

In the parcours, spoken turns reach the server only when the browser reports them afterwards
(`POST /api/seance/report`, spec 018 D3, D7). A card shown during a voice session has no server
record before that report, so a « server-owned presentation » for voice needs new recording at
`/api/voice/tool` time. Révision has no voice at all.

Recommendation: move voice checking to a later spec. The card's answer field stays usable during a
voice session.

## 5. Inconsistent with `record_result` (medium)

Self-assessments are shown live and persisted when the turn is stored. The buffering proposal
would treat checker results differently. Item 1 makes this moot; otherwise follow the existing
`record_result` behaviour.

## 6. Certified rounding is decidable for the algebraic cases (medium)

For a root of a rational polynomial, refine its isolating interval until it excludes the rounding
boundary. If the polynomial vanishes at the boundary, the root is that rational number and is
exact. « Undecided » then arises only from resource limits, which keeps degrees 1–4 cheap.

The expensive part is « Evaluate outside the rational class with a certified interval », which is
general interval arithmetic. The textbooks need two things:
- `√` (Pythagoras): exact by squaring;
- `π` (circles): rational bounds.

Proposal: support only those two and leave everything else not checkable.

## 7. Read a stated domain in the answer (medium)

Under the owner's domain rule, `x + 1` gets no verdict against `(x²−1)/(x−1)`. Grade 9 material
writes the restriction with the simplified term (`x + 1 für x ≠ 1`, `D = ℝ \ {1}`).

Proposal: a reader for such an annotation, so that the answer's domain is the stated one. That
makes exactly these « kürzen » exercises checkable instead of undecided.

## 8. Inconsistencies to fix (low)

- Requirements §1 point 4 and R3.2 still say the tool receives « the student's final answer and the
  recorded exercise's id (plus chapter and section) ».
- R3.6 and the output words in design §3.11 still refer to `unknown_exercise`.

## 9. Scope (recommendation for planning)

023 now covers:
- keys and authoring;
- the exact checker, with root isolation;
- presentation and submission storage and API;
- answer fields and chat confirmation;
- voice;
- the choice-card rework;
- the révision table;
- review labels.

Suggested stages:
- **023a**: checker, keys, the answer field in the parcours;
- **023b**: révision results and review labels;
- **023c**: chat and voice confirmation (or a separate spec).
