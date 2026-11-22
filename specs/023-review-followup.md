# Spec 023 — follow-up review

These decisions were made while `feature/021-german` was checked out and are incorporated in
requirements §9 and the revised design. The implementation details remain to be designed and
reviewed before planning.

## Agreed: expression domains

If two expressions have different domains, the checker should not give an equivalence verdict.
For example, `(x²−1)/(x−1)` is undefined at `x = 1`, while `x+1` is defined there. The tutor may
explain the difference. This supersedes the design's proposed common-domain equivalence (D8).
The design must specify the relevant domain for the exercise, how equality of domains can be
established reliably, and how to handle cases that cannot be established without a verdict.

## Agreed: identify the learner's answer

The checker checks only an unambiguously delimited answer from the learner. A substring alone is
not sufficient: given "Meine Antwort ist 12", the model must not select the contained `2` as
the answer. If the intended answer is ambiguous, the tutor asks for clarification rather than
issuing a verdict. This supersedes the substring check in design §3.10. The design must cover
text, multiple-choice selections and voice transcripts, as well as how the answer is associated
with the bound exercise.

## Agreed: completeness and rounding of computed solutions

For computed solutions, including equations of degree three or four, issue a verdict only when
the checker can reliably establish that it has found all relevant solutions and any required
rounding is unambiguous. Otherwise return "not reliably checkable" and give no correct/incorrect
verdict. Keep the textbook-derived requirements for supported equation types; the design must
state how completeness and rounding are established and include difficult cases in verification.

## Agreed: replay of older multiple-choice cards

On reopening a previously stored multiple-choice card, show the question and the learner's
selection when available, but no correct/incorrect marking unless there is a trustworthy checker
result. A model-selected answer alone does not justify a verdict. The design must describe
backward-compatible replay and avoid presenting missing historical selections as recorded facts.

## Agreed: multiple-choice feedback

Without a trustworthy checker result, omit the model-authored automatic feedback on a
multiple-choice selection; the learner may still discuss the question with the tutor. When a
checker result is available, the app shows its verdict and source. The design must account for
new and previously stored cards and preserve the rule that a model-selected option alone is not
a verified verdict.

## Agreed: review exercises from earlier material

When the student's material explicitly labels exercises as review of earlier material, retain
that label so the revision overview can present them separately from exercises of the current
chapter. Without an unambiguous label, treat them like other exercises. The design must specify
how the label is represented and carried to the overview without inferring it from the model's
assumptions.

## Agreed: unspecified rounding such as "Runde sinnvoll"

If the material does not state a concrete rounding rule and its model solution does not make the
rule unambiguous, do not automatically judge the required rounding. The tutor may discuss the
answer, but the checker gives no correct/incorrect verdict for that rounding. This refines the
textbook decision in requirements §8.1: a vague instruction alone must not be converted into an
invented precision. The design must distinguish explicit rules, unambiguous evidence in a marked
model solution, and an unresolved rule.

## Agreed: displayed variants and checking data

A variant receives an automatic verdict only if its displayed task and checking data reliably
agree; otherwise it remains ungraded. For purely mathematical variants the application may
generate the checkable statement directly from the checking data. Merely adding a generated task
line beside potentially contradictory model-written text does not establish agreement. The design
must specify what context can be displayed, how agreement is established, and failure behavior.
