# Spec 023 — design proposals for review

> **Superseded in part (22 November 2026):** voice is out of spec 023 and the work is planned in
> three stages; see requirements §12 and §13. This note is kept as history.

Draft for discussion, not an approved design or implementation plan. The user-approved directions
below are incorporated into requirements §10. The agreed decisions from the previous review are in
`specs/023-review.md` and `specs/023-review-followup.md`. Technical proposals still need review
and must be reconciled with the design before planning.

**Historical note:** After `specs/023-review-claude.md`, the user requested reconciliation. The
model-called checking chain, conversation-row-only scope and model-turn transaction in this draft's
submission contract are superseded by requirements §11 and design §§3.9–3.14. The user-approved
interaction and mathematical principles remain; the revised contracts need review before planning.

## 1. Explicit answers linked to a shown exercise — agreed

**Proposal.** Each checkable card offers a dedicated final-answer input tied to its server-issued
exercise ID. The student submits the whole field. A multiple-choice selection submits its option
ID and the card's exercise ID. The server resolves an exercise actually shown in the student's
current conversation and checks the submitted value against its bound checking data. It records
the result with the exercise and the submitted turn, and displays it on that card.

Both the card and ordinary chat support answers (user decision). If a chat answer is not
explicitly submitted through the card, the app proposes the exact answer and exercise for the
learner to confirm or correct before creating a submission (user decision). This makes the
learner's intent and exercise association explicit even if the model selects the candidate. If
extraction or association is uncertain, ask rather than assume. The
model does not extract a substring and claim it is the student's final answer. A retry is a new
submission. Old, unbound, stale or foreign exercises produce no verdict. Stored results replay on
their original card; older choice cards show a past selection only if it was actually stored.

For voice, propose a visible, editable transcript associated with the exercise and explicit
confirmation before checking. A voice transcript can be wrong, so merely receiving it from the
browser does not establish that the learner intended that answer. Exact voice interaction and
accessibility still need design review.

Variants are checkable only when all task-bearing content shown to the learner is generated from
or reliably verified against the bound checking data; an extra generated line does not validate
contradictory model text. Otherwise the card is unbound and no verdict is recorded.

**User decision:** A dedicated answer field on the exercise card is acceptable; multiple-choice
selection, clarification for ambiguous chat messages, and displaying a voice transcript for
confirmation or correction are acceptable. The detailed voice interaction and accessibility
remain to be designed.

**User decision on variants:** For a purely mathematical variant, the app generates the
checkable statement directly from the checking data. A word problem whose agreement with those
data cannot be reliably established may still be posed and discussed, without an automatic
correct/incorrect verdict.

### Proposed submission contract — needs review

- A card submits the learner's complete answer or option together with the exercise ID and
  conversation context. The server checks ownership, the conversation's mode and content
  version, and that this exercise was actually presented there. A valid HMAC alone does not
  establish that an exercise was presented in the current conversation.
- The server creates an immutable submission ID tied to the conversation, exercise and exact
  submitted value. A retry is a separate submission. The tutor can request a check by submission
  ID, but cannot supply or replace its answer text. Unknown, stale or unrelated IDs yield no
  verdict. A duplicated request for the same submission returns the existing result, rather than
  recording it twice. The exact route and transaction boundary remain to be designed.
- A free chat message is not silently converted into a final-answer submission: propose the exact
  answer and exercise for the learner to confirm or correct. Card input submits directly. A
  confirmed speech transcript follows the same submission path; a raw browser-provided transcript
  alone is not a confirmed answer. The voice interaction must remain usable with assistive
  technology and when speech recognition fails.
- In revision, the result and transcript are persisted according to the existing atomic turn
  semantics. Cancellation, retries, page reloads and duplicate requests must not attach a result
  to a different exercise or create a second result. Replaying a card restores its own recorded
  result and source. Lifecycle and cancellation behavior require explicit design review.

**Acceptance examples:** `12` submitted on exercise A cannot become `2` or be attached to B;
if the model proposes the wrong chat candidate, the learner can correct it before checking; an
unconfirmed voice transcript cannot be checked; an exercise ID from a different conversation
cannot be checked; repeating a check for the same submission does not duplicate its result.

## 2. Expression domains — agreed direction

**Proposal.** Preserve domain restrictions from the original expression before simplifying it.
Compare values only after establishing that the relevant domains are the same. Start with a
bounded class for which the comparison and domain equality can be established exactly. If the
domain or equality cannot be established within the supported class and limits, return
`not reliably checkable` rather than a verdict. For example, `(x²−1)/(x−1)` and `x+1` have
different domains over the reals and get no equivalence verdict.

**User decision:** Begin with cases where both domain and equivalence can be determined exactly;
return `not reliably checkable` otherwise. The supported class can be extended later.

**Concrete proposal for design review:** For supported one-variable rational expressions, retain
the nonzero constraints of every division and negative power in the original parse tree before
any cancellation. Use exact polynomial arithmetic for expression equality. Prove equal domains
only when the normalized constraints are provably equivalent; if the procedure cannot prove
that, give no verdict. Equal-looking simplified expressions alone are insufficient. Keep explicit
degree and size limits and return `not reliably checkable` when they are exceeded. The precise
normalization, proof procedure and limits must be specified and tested before planning.

### Proposed proof for the bounded rational class — needs review

Use exact rational coefficients. Convert an expression to a rational value plus domain guards
from the original parse tree: guards inherited from both operands are retained, division adds a
nonzero guard for the divisor, and a negative power adds one for its base. Guard normalization
must preserve exclusions that cancel out of the final value. Reject an always-zero divisor and
unsupported operations as not reliably checkable. Enforce size limits before multiplying or
expanding polynomials.

On the stated exercise domain (default all real numbers), compare rational values by exact cross
multiplication. To establish whether polynomial nonzero guards exclude the same real points,
normalize guard products to square-free rational polynomials and use exact gcd plus certified
real-root counts; do not assume different polynomials imply different real domains. Intersect
with the exercise domain only if its bounds and open/closed endpoints can also be handled
exactly. A proof failure, unsupported restriction or resource limit yields `undecided`.

Examples: `x/x` versus `1` preserves the exclusion at zero and receives no equivalence verdict;
`x` versus `x(x²+1)/(x²+1)` can have equal real domains despite different denominator guards;
two expressions that are equal on the same proven domain may be compared algebraically. Domain
proof and value comparison must both succeed for a correct verdict.

## 3. Complete solutions and rounding — agreed direction

**Proposal.** Exact rational and supported radical cases may be checked when the solver can
establish all relevant solutions. Numerical candidates alone are insufficient for a verdict:
the method must establish completeness and, for approximate answers, an unambiguous rounding.
Repeated roots, close roots, excluded denominator values and rounding boundaries need explicit
verification. If the implementation cannot establish the result within its bounds, return
`not reliably checkable`.

**User decision:** Require a complete, reliable set of relevant solutions before issuing a
verdict. For `x² = 4`, `{−2; 2}` can be checked and `{2}` is incomplete. Apply the same rule to
the specified cubic and quartic cases; without proof of completeness or unambiguous rounding,
return `not reliably checkable`.

**Concrete proposal for design review:** Use exact rational polynomial arithmetic and isolate
real roots in disjoint rational intervals with a certified root-counting method such as Sturm's
theorem. Remove repeated factors for root isolation but preserve them for inequality signs; use
exact polynomial operations to identify roots excluded by original denominators. Count roots
before and after isolation, and refine intervals until a stated rounding is provably unambiguous.
If an excluded root, completeness, or rounding cannot be decided within explicit degree, size and
work limits, return `not reliably checkable`. Exact rational and supported radical solutions
remain exact; approximations never silently become exact keys. The specific arithmetic and root
isolation interfaces, equality of algebraic roots and limits still need detailed validation.

Verification must cover repeated and closely spaced roots, no real roots, excluded roots from
denominators, boundary rounding, timeout/size limits and the empty or all-real solution sets.
For a rational equation, retain all original denominator guards and filter only roots whose
exclusion can be decided exactly. For a polynomial inequality, isolate every distinct real root,
evaluate signs exactly between roots, and determine endpoint inclusion from the operator and the
original domain. If any required relation to an exclusion or rounding boundary remains unresolved,
return `not reliably checkable`; never fill a missing interval from a numerical guess.

## 4. Explicit review labels — agreed

**Proposal.** Preserve an optional review label tied to a pack exercise only when the material
explicitly marks it as review. Carry it with the bound exercise and show it separately in the
revision overview; an absent or uncertain label means ordinary presentation. The learner can
correct the label in the pack. The exact storage and editing contract must be specified without
inferring labels from subject or school year.

**User decision:** Store the label with the pack exercise, carry it to the revision overview,
and make it correctable by the learner. Apply it initially only when the material explicitly
marks the exercise as review.

The practice-test contract remains deferred until spec 022 is resumed.
