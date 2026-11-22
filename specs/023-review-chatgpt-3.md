# Spec 023 — third ChatGPT/Codex review

Review of `f3c7059` on `feature/023-answer-checker`, against requirements, design, the
previous review, the shared workflow and the existing code. This is a design review, not
an implementation plan. The findings, proposals and questions below are not owner decisions.

## Recorded decisions and assessment

Requirements §13 records the owner's decisions on F1–F8 and dictation. The decisions govern
over earlier wording: 023a includes revision verdicts without `exercise_results`; 023b adds
records for new submissions only; and 023c adds confirmed chat candidates. Spoken-answer
checking remains deferred, while dictation into the composer is text input.

| Previous finding | Assessment of the new wording |
| --- | --- |
| F1 | The stage boundary, replay and no-backfill decisions are recorded; some unqualified transaction wording still needs alignment (N4). |
| F2 | `turn.stored` correctly replaces `turn.end` as evidence of successful storage, with reported stopped cards unbound. Activation still needs the scope and stage details in N2 and N3. |
| F3 | A server-assigned message ID and the active-after-store rule are recorded. The source text is still described inconsistently at tool-call time (N1). |
| F4 | All modes and legacy cards are explicitly assigned to 023a. The proposed shared model and declaration need a compatible schema contract (N5). |
| F5 | Creation of a card, rather than an active voice session, determines its voice scope. Voice checking is deferred, voice source is refused, dictation is text, and the earlier documents are marked historical. |
| F6 | The owner chose measured model behaviour and an authoritative card verdict. The proposed measurement needs a clear interpretation (N8). |
| F7 | The correction is an override outside the pack, avoiding a version bump and progress reset. Its identity and lifecycle need clarification (N6). |
| F8 | R2.6 now explicitly preserves exact numeric lexemes for the checker while retaining the plot parser's float behaviour. The exact parser interface remains open in §10.3. |

## Findings

Ordered by severity, then effort. Effort estimates refer to resolving the specification, not to
implementing the feature.

### N1 — High, low effort: 023c still asks for a stored message before it exists

[Design §3.10](023-answer-checker/design.md#L430) assigns the learner message its ID at turn
start and allows `propose_answer` during that turn; [§3.11](023-answer-checker/design.md#L469)
instead says the server supplies the *stored* learner text. In the current
[chat route](../backend/app/api/routes/chat.py#L47), the incoming entry is held in the turn and
stored only at successful completion; [LearnerEntry](../backend/app/api/schemas/chat.py#L27)
has no message ID today. Assigning an ID earlier does not itself store the message. Thus §3.11
cannot literally describe the proposed tool call. The design also needs to say how the proposal,
its message ID and exercise survive the successful store and replay without making an unstored
candidate active. §10.1 names the message ID but does not identify this distinction.

### N2 — High, medium effort: a stored revision card can already be invalid when activated

[Design §3.9](023-answer-checker/design.md#L407) activates cards named by `turn.stored`, but
also invalidates a revision presentation when its run closes. The existing
[conversation append](../backend/app/db/repositories.py#L1420) stores a whole turn and closes
the row as `capped` in that same transaction when a limit is reached; the design explicitly says
there is no automatic revision rollover. A card produced in that turn can therefore be stored
successfully while its revision closes. The spec does not say whether it is named as usable in
`turn.stored`, how the client learns it is no longer eligible, or what the learner sees. Treating
storage alone as sufficient would enable a control the submission service must reject. This can
affect revision display already in 023a, independently of the 023b results table.

### N3 — Medium, low effort: activation and event contracts retain stage and stopped-turn ambiguities

[Design §3.9](023-answer-checker/design.md#L401) first says only validated, stored cards in a
stopped-parcours report become eligible, then says reported stopped cards are *never* bound.
The latter matches §13.2; the earlier sentence can be read as allowing the former. In addition,
[§3.12](023-answer-checker/design.md#L498) gives `turn.stored {exercise_ids, message_id}`
without a stage or nullability rule, whereas [§4](023-answer-checker/design.md#L592) introduces
learner message IDs in 023c. The contract must also account for turns with no learner message.
The current [SSE controller](../backend/app/api/sse.py#L82) sends `turn.end` after an error, so
it remains essential that neither `turn.end` nor a client report impersonates a store success.
§10.1 calls out the event, but leaves these cases implicit.

### N4 — Medium, low effort: unqualified revision transaction statements obscure the 023a boundary

[Design §§3.10–3.11](023-answer-checker/design.md#L444) say a revision submission also writes
`exercise_results` in its transaction; [§3.13](023-answer-checker/design.md#L512) correctly
excludes that record in 023a. Read as a final-state description with an explicit stage exception,
the decisions are compatible, but the unqualified statements and
[verification wording](023-answer-checker/design.md#L642) invite requiring the 023b table in
023a. The 023a contract must include persisted verdict, replay and next-turn context, and 023b
must start recording new submissions without importing old ones, as §13.1 decides.

### N5 — Medium, medium effort: accepting old choice fields does not automatically remove them from the tool declaration

[Design §3.17](023-answer-checker/design.md#L561) says the backend card model accepts old
`correct_option_id` and `feedback` fields as optional and drops them, while the model-facing
declaration no longer has them. Today [the shared card model](../backend/app/domain/board.py#L202)
requires both, and [the tool declaration](../backend/app/services/tools/registry.py#L84) is
generated from the argument model's JSON schema. Merely making fields optional still exposes them
in that schema. The legacy read path, the model-facing declaration and all shared renderers need
compatible but distinct behaviour. Otherwise a valid implementation of one sentence can violate
the other or break old cards. This concerns all modes in 023a, including unbound voice-created
cards; it does not bring voice checking back into scope.

### N6 — Medium, medium effort: label overrides have no policy for reused exercise references

[Design §4](023-answer-checker/design.md#L596) keys an override by owner, chapter and exercise
ref, and ignores it when the ref no longer exists. A pack update can change the meaning of a ref
or remove and later reuse it; the ref may still exist while naming a different exercise. The
current [chapter update](../backend/app/db/repositories.py#L619) increments content version and
resets progress for changed content. Nothing specifies whether an old override follows that ref,
is invalidated, or is mapped to a proven stable identity. It could silently label the wrong task.
The effect of an explicit progress reset and how to remove an override and fall back to the pack
label are also not stated. The existing [§3.15 wording](023-answer-checker/design.md#L543),
“correct the label in the pack”, is ambiguous beside the §13.7 outside-pack decision.

### N7 — Medium, medium effort: version and deletion rules for revision results need a concrete contract

[Design §3.13](023-answer-checker/design.md#L500) lists fields for `exercise_results` but does
not explicitly include chapter content version or specify how the Bilan excludes stale results.
The existing [revision-result read](../backend/app/db/repositories.py#L1681) filters by the
chapter versions in scope. A version could instead be obtained through a retained presentation,
but its retention and deletion rules must support that. [Design §4](023-answer-checker/design.md#L598)
calls for cascades including content reset and session deletion while §10.1 leaves migration and
lifecycle general; it does not say which records survive each operation. Without that distinction,
old answers can appear against changed content or useful results can disappear unexpectedly.
This is a 023b concern; it does not justify a 023a results table.

### N8 — Medium, medium effort: the prose probe's metric needs a semantic boundary

The decision in [requirements §13.6](023-answer-checker/requirements.md#L461) deliberately
chooses measured behaviour, with the card as the authoritative verdict. [Design §3.14](023-answer-checker/design.md#L517)
proposes counting verdict words outside a committed verdict. Word counting alone can miss a
paraphrased judgment and count an innocent quotation; it does not by itself measure the stated
behaviour. The decision expressly leaves the pass threshold until probes are written, so this
review does not require setting a number before planning. §10 could nevertheless name the need
to define the cases, semantic evaluation, denominator and per-language threshold before accepting
the probe as evidence. This preserves the owner's measured-behaviour decision.

## Proposals

These are recommendations for discussion, not changes to the approved requirements or design.

1. **Before planning, resolve N1–N7 in the design and enumerate the remaining contract work in
   §10.** For N1, distinguish the authenticated in-memory turn message at tool-call time from
   the stored message after success; bind proposal, message and exercise on store, retain the
   existing explicit confirmation, and specify replay and old ID-less entries.
2. For N2–N3, specify the stored event's correlation, optional fields by stage, eligible IDs,
   revision-close outcome, failed store, lost acknowledgement/reload and stopped-report handling.
   Remove the contradictory eligibility sentence; do not treat `turn.end` as a success signal.
3. For N4–N5, qualify revision-result statements and verification by stage, and define separate
   legacy-reading and model-facing schema behaviour. Check old cards and shared rendering in
   parcours, discussion, revision, notebook and voice-created unbound cards.
4. For N6–N7, make label override identity, pack-version changes, explicit reset, deletion and
   return to the pack's label explicit. Specify the version used to read results and the lifecycle
   of the result, presentation and transcript across session deletion and content changes. Clarify
   that correction *from the pack view* saves the override, not a pack edit.
5. For N8, record the probe-design work in §10, keeping the threshold decision at probe-writing
   time as already agreed. Cover semantically expressed judgments and all supported languages,
   and distinguish measurement from the authoritative checker result.

The three increments remain coherent in scope and dependency: 023a needs the stored
presentation, checker, submission route and transcript/replay before its fields can work; 023b
builds on those submissions for new per-exercise results and labels; 023c builds on stored
presentations and adds message identity and confirmation. The prescribed order is 023a → 023b
→ 023c. I cannot yet call each release contract fully specified until the cases above are
resolved; this is a review conclusion, not a proposed implementation plan.

## Open questions

1. When a revision reaches its limit in the same turn that presents a checkable card, should the
   card remain usable for a final answer, or should it be shown as unavailable with a clear reason?
   Any change to the current rule that a closed revision invalidates presentations needs owner
   agreement.
2. After a pack edit reuses an exercise ref for changed content, should a previous learner label
   override be discarded, retained, or retained only when exercise identity can be established?
   Should an explicit progress reset also clear overrides? These choices affect learner-visible data.
3. What should happen to 023b exercise results when a revision session is deleted or its chapter
   content changes: delete them, retain them but hide them from the current Bilan, or expose them
   as historical? The answer should be consistent with existing revision data and the desired
   deletion behaviour.

## Evidence and limits

Reviewed the commit diff, §13 and affected active requirements and design sections, the prior
review, workflow and SDD skill, and relevant chat, SSE, shared card/tool and repository code.
This is a static specification and code review: no implementation was changed and no runtime
or real-model probes were run. The detailed parser and route designs remain open as recorded
in design §10.
