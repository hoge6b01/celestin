# Spec 023 — shared review

This is a working record of the review with the user. The requirements and design under review
are on `feature/023-answer-checker`; they are not present on the current `feature/021-german`
branch. Transfer the agreed decisions into those files when the work is brought together, and
reconcile the index and any affected design or acceptance criteria. Proposals are not decisions.

**Status (22 November 2026):** the agreed decisions below are carried into
`023-answer-checker/requirements.md` §7 and the revised `design.md` (decisions D5–D11, open
questions §10). This file stays as the record of the review.

## Agreed: numerical answers

The user agreed that numerical values are exact by default. For example, a key of `5` accepts
`5` and `5,0`, but not `5,4`. A tolerance or rounding rule applies only when the exercise or
its answer key explicitly specifies it. This replaces the existing decision in requirements §6.4
that infers tolerance from the number of decimal places in the key. Reconcile the number and
precision rules in requirements, design and tests, including units and converted values.

## Agreed: bind an answer to the exercise

When a checkable exercise is presented, the server records its exercise ID and checking data.
Checking uses that recorded exercise, and the verdict belongs to that exercise rather than
whichever card happens to be latest. If the checking data cannot be reliably associated with
the exercise, the checker gives no correct/incorrect verdict. For model-written variants,
the design must additionally address how the displayed exercise is verified against its
checking data; merely storing both does not prove that they agree.

## Agreed: identify the source of a verdict

When a check compares an answer with a solution taken from the student's material, the app says
that the answer matches or does not match the stored solution. A syntactically valid key does
not prove that the solution was transcribed correctly or that the material itself is correct.
When the checker can also independently compute the solution, it may display a corresponding
computational verdict. The source remains visible to the learner. The design must define how
independent computation is established and what happens when it conflicts with the stored key.

## Agreed: disagreement between stored and computed solutions

If an independently computed solution disagrees with the stored solution, the checker gives no
correct/incorrect verdict for that exercise. The app indicates that the solution needs review;
the stored solution is not overwritten and remains available for the learner to inspect. While
the exercise is open, the notice does not disclose the solution. The design must specify how
to surface the issue and ensure no verdict is recorded for the conflict.

## Agreed: expression equivalence

The checker confirms equivalence only when it can reliably establish it for the kind of
expression being checked. Matching a finite set of sample points alone is not proof. When
equivalence cannot be established, the result is "not reliably checkable" and the tutor guides
without a correct/incorrect verdict. The design will define the supported expression classes,
their domain rules and evidence, including how this outcome reaches the user and spec 022.

## Agreed: multiple choice

Multiple-choice exercises show a correct/incorrect verdict only if the exercise and its answer
key are reliably bound and the checker evaluates the selection. An answer identified as correct
solely by the model does not justify such a verdict; the tutor may still discuss the question
with the learner. This changes existing `check_question` behavior and supersedes design decision
D2's proposal to leave those cards unchanged. The design must cover existing cards and replay.

## Agreed: revision results describe the checked exercise

The revision history records a checker result as the result of the particular exercise, with its
date and source. The learner's self-assessment remains alongside it. A single correct answer does
not automatically mark the whole section as mastered. This changes the proposed mapping from a
single verdict directly to a section-level `solid`, `shaky` or `todo` outcome. Section summaries
for multiple practice-test results belong to the later review of spec 022. The design must define
storage, display and how results affect subsequent revision without implying section mastery.

## Open

The contract with spec 022 and the details of implementing the agreed exercise binding,
multiple-choice behavior, result storage, conflict handling and equivalence checks remain open.
