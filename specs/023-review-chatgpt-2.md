# Spec 023 — second ChatGPT/Codex review

Review of commit `905659d` on `feature/023-answer-checker`, against requirements, design,
the existing application and `specs/WORKFLOW.md`. This is a review, not a plan or an
implementation. Findings, proposals and questions below are not owner decisions.

## Decisions and baseline

- The owner's current decision is authoritative: requirements §12.1 defers checking spoken
  answers and cards created in voice sessions; §12.2 fixes three independently shippable stages.
  The superseded voice wording in requirements §§10–11 is retained as history and explicitly
  marked as superseded. The old Claude review and reconciliation note are historical records.
- The direction agreed earlier remains: directly check an explicitly confirmed learner submission
  against a stored presentation, preserve source and per-exercise results, and return no verdict
  when an answer cannot be checked reliably. The later voice decision narrows that direction.
- Commits `dd27d3a` and `b08c223` match the previously reported working-tree change summary and
  the decisions and design changes made in our conversation: requirements §§10–11, the revised
  design, index, design proposal and reconciliation note. The recorded earlier diff statistics
  agree (design 653 lines, requirements 126, index 2; proposal 160 additions; reconciliation
  note 37 additions). I did not retain a separate hash or byte-for-byte snapshot of the prior
  uncommitted files, so that evidence does not independently prove every byte is identical.
  `5e00cde` also adds Claude's review; `905659d` makes the subsequent §12 changes.

## Findings

### F1 — High, medium effort: 023a revision behavior conflicts with the full transaction contract

[Requirements §12.2](023-answer-checker/requirements.md#L427) says 023a includes revision
display **without** its record, leaving `exercise_results` to 023b. Yet
[requirements R5.3](023-answer-checker/requirements.md#L218) and
[design §§3.10, 3.13](023-answer-checker/design.md#L439) say a revision submission, transcript
and recordable `exercise_results` commit together. An implementation of the full design cannot
ship 023a without the 023b table. The spec does not yet state whether 023a keeps a per-submission
verdict in the transcript, what the learner sees on reload, what the tutor receives on the next
turn, or how 023b treats earlier submissions. This is a stage-boundary gap, not a reason to assume
023a should create the revision record early.

### F2 — High, medium effort: card activation needs a reliable store-success acknowledgement

[Design §3.9](023-answer-checker/design.md#L402) requires the field to stay disabled until the
card and presentation are stored, but does not define the success signal or correlation between
the streamed card and the persisted presentation. In the current
[SSE controller](../backend/app/api/sse.py#L82), `on_complete` can fail, an error is sent, and the
`turn.end` event is nevertheless sent afterwards. Treating `turn.end` alone as proof of storage
could enable a card that the server refuses, or leave a valid card disabled after reconnect. The
stopped-parcours report path can also retain a partial turn, so its activation and rejection of
forged bindings need an explicit contract. §10.1 mentions schemas and replay generally, but not
this success/failure signal and partial-report boundary specifically.

### F3 — High, medium effort: 023c references a stored message that does not yet exist during the turn

[Design §3.10](023-answer-checker/design.md#L430) proposes
`propose_answer(exercise_id, message_id)` and says the candidate is the server-recorded learner
message. The current [LearnerEntry](../backend/app/api/schemas/chat.py#L27) has no message ID;
[chat.py](../backend/app/api/routes/chat.py#L47) adds the incoming message to the model input and
stores it only after the turn. During the tool call there is therefore no specified persisted
message ID to resolve. It is also unspecified how a candidate survives cancellation, refresh,
row rollover or a failed store without allowing the model to substitute text or reveal a key.
§10 does not call out this dependency of 023c explicitly.

### F4 — High, medium effort: global choice-card compatibility is not assigned to a stage

[Requirements R4.3](023-answer-checker/requirements.md#L202) excludes model-derived choice
verdicts in **every** mode. 023a names bound choices in parcours and revision display, while
[design D9](023-answer-checker/design.md#L71) removes `correct_option_id` and `feedback` from
the shared card. The current [shared frontend renderer](../frontend/src/components/celestin/whiteboard.tsx#L150)
uses both to colour answers and show feedback; the shared backend schema also requires them
([board.py](../backend/app/domain/board.py#L202)). Text discussion, voice-created unbound cards,
old stored cards and notebook replay therefore need an explicit transitional wire and UI contract.
Otherwise 023a may ship false verdicts, fail to parse cards, or break a mode outside its named
features. `voice bridge: unchanged` alone does not prove the shared card contract stays compatible.

### F5 — Medium, low effort: active text still implies voice checking

§12.1 correctly says cards **created** in voice sessions are unbound, while stored text-turn
cards can remain usable. However:

- [Index row 023](index.md#L32) still advertises `card/chat/voice submissions` even while its
  status says voice was deferred.
- [Design §4](023-answer-checker/design.md#L578) still requires authoritative voice-card entries
  during report reconciliation; [§5](023-answer-checker/design.md#L592) mentions voice storage
  failure, and [§3.9](023-answer-checker/design.md#L407) retains a future voice algorithm ending
  with an instruction to define it in §10 before planning. The latter conflicts with §10.2's
  explicit deferral.
- [Design §6](023-answer-checker/design.md#L633) still lists chat/voice confirmation and an
  editable transcript as frontend coverage for this spec. The `voice` source in
  [§3.10](023-answer-checker/design.md#L439) is called reserved rather than part of the accepted
  list, but its rejection in this version is not an explicit acceptance criterion.
- [Requirements R3.8](023-answer-checker/requirements.md#L187) says a card *shown* during a
  voice session is not checkable, then permits a stored text-turn card while voice runs. The later
  decision in [§12.1](023-answer-checker/requirements.md#L422) says a card *created* in a voice
  session is unbound. [Design §6](023-answer-checker/design.md#L626) repeats the broader wording.
  The distinction matters for a previously created text card still visible during a voice session.

The old [reconciliation note](023-review-reconciliation.md#L19) and
[design proposal](023-design-proposal.md#L30) also say voice is in scope without mentioning §12;
they should be identifiable as historical rather than read as the current decision. Requirements
§§10–11 do explicitly mark the superseded voice decisions, so they are not the same problem.

### F6 — Medium, medium/high effort: the no-unverified-verdict promise lacks an enforcement boundary

[Requirements R4.1](023-answer-checker/requirements.md#L191) asks the tutor never to declare a
correctness verdict without the checker. [Design §3.14](023-answer-checker/design.md#L510)
addresses this through prompt instructions, while [§8](023-answer-checker/design.md#L648)
correctly acknowledges that free model prose can leak material solutions. The current system
streams tutor prose; this design does not establish how an invented correctness statement in that
prose is prevented or how violations are detected. This inherited constraint matters as soon as
023a advertises trustworthy verdicts; §10 does not explicitly classify it as a design decision or
measurement limitation. A real-model probe alone is evidence, not a guarantee.

### F7 — Medium, medium effort: review-label editing may reset the evidence it labels

[Requirements §10.4](023-answer-checker/requirements.md#L389) makes a label editable in the
pack; [design §3.17](023-answer-checker/design.md#L564) places it in the revision overview.
Today [saving a pack](../backend/app/api/routes/courses.py#L450) adopts a new content version and
[every adopted change deletes chapter progress](../documentation/chapters.md#L194). Spec 023
also invalidates presentations on content change. It does not say whether correcting only a label
should reset progress, close revision, invalidate checker results or keep them associated with the
new label. §10.4 mentions label syntax and validation but omits this lifecycle and user-visible
consequence, which affects whether 023b is independently usable.

### F8 — Medium, low/medium effort: requirements still require the float parser for exact answers

[Requirements R2.6](023-answer-checker/requirements.md#L149) says to reuse
`domain/expression.py`'s `parse`, whereas [design §3.6](023-answer-checker/design.md#L267)
correctly notes that it converts numeric literals to `float` and calls for preserving lexemes.
The [current parser](../backend/app/domain/expression.py#L223) does exactly that conversion.
§10.3 notes the interface is open, but the requirements/design boundary should be reconciled so
023a cannot satisfy the wrong contract and lose exactness.

## Proposals for review — not decisions

1. **F1:** Specify a stage-by-stage capability and data contract. In 023a explicitly distinguish
   the stored transcript/visible replay from the deferred `exercise_results` record and Bilan;
   specify whether 023b imports or deliberately leaves earlier attempts unaggregated. Validate
   installation, upgrades, rollback and old transcript replay at each stage.
2. **F2–F4:** Define a correlated, server-authoritative card-store success signal (including
   stopped-turn reports and duplicate sends); define an unambiguous source-message identity and
   confirmation lifecycle; and assign shared choice-card wire compatibility and model-verdict
   removal in every affected mode to 023a. Cover current sessions and old stored cards.
3. **F5:** Correct active voice references and clarify that text-created cards remain checkable
   during a voice session, while voice-created or reported cards cannot acquire a binding. Mark
   earlier review notes as superseded by §12 without erasing their history.
4. **F6:** Decide whether R4 is a mechanically enforced guarantee or a measured tutor behavior;
   document what runs on every response, failure behavior, and the evidence and limits for any
   model-dependent statements. Preserve the agreed checker and answer-withholding invariants.
5. **F7–F8:** Resolve label-only edits, content-version/progress consequences, migration and
   historical result display; align the exact parser contract and tests with the existing float
   parser's actual behavior.

## Open questions for the owner and design

1. Does 023a's revision display need transcript replay of each checked answer while deliberately
   omitting the per-exercise revision record? Should 023b import those earlier answers or only
   record new attempts?
2. When correcting just a review label, is the current full pack-edit reset acceptable, or should
   labels be editable without resetting progress? The latter changes today's content lifecycle.
3. Does the voice exclusion cover text dictated into the normal composer and manually corrected
   before sending? The current [dictation flow](../frontend/src/components/celestin/composer.tsx#L95)
   inserts text into the ordinary editable draft, while realtime voice is a separate session.
   Clarify the intended boundary and required provenance before specifying tests.
4. What exact acknowledgement, message identity, ordering and retry behavior should connect
   text streaming, stopped-turn reporting, submissions and the 023c confirmation UI?
5. How should the product state the limit of model-generated prose versus the mechanically
   computed checker outcome, and what enforcement or measurable acceptance threshold is required?

## Review verification

- Reviewed `905659d` and the commits since `e673498`, the shared workflow and skill, 023
  requirements/design/index, prior review notes and the relevant current chat, SSE, séance,
  revision, choice-card, dictation, parser and pack-edit code.
- This is a specification and code-reading review. No application code was changed and no test
  suite was run. The findings do not assert that the unimplemented checker currently fails.
