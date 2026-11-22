# Spec 023 — reconciliation of Claude's review

> **Superseded in part (22 November 2026):** voice is out of spec 023 and the work is planned in
> three stages; see requirements §12 and §13. This note is kept as history.

The user requested that the specs be revised and extended after `023-review-claude.md` was
discussed. The following records what was incorporated; it does not approve the final design or
authorize planning and implementation. The original review and previous decision records are
preserved.

1. **Direct checking:** A learner-confirmed submission is checked immediately by the server;
   submission, transcript and, in revision, the per-exercise result commit atomically. It does
   not depend on a model tool or a subsequent model turn. This changes the earlier 023 rule that
   the checker result waits for the model-turn transaction; spec 020's self-assessment rule stays.
2. **Stored presentations:** Text cards become eligible with the stored turn, not when streamed;
   stopped parcours turns may be retained by the existing report mechanism but cannot introduce a
   forged checkable binding. The voice tool path needs trusted persistence and reconciliation.
3. **Rollover and scope:** An eligible parcours card can survive a capped row and section return
   in the same owner/chapter/section/version/mode. A closed or replaced revision run is not
   silently reopened; the current code returns `RevisionFull` instead of automatically rolling it
   over. Ownership, reset, scope and content-version checks remain mandatory.
4. **Voice stays in scope:** The earlier agreement on voice confirmation is preserved. Retaining
   it requires changes to server-side voice presentation and report reconciliation; moving it to
   a later spec was not adopted. Voice in revision remains out of scope.
5. **Streaming:** The checker-result buffer tied to a model turn is removed. A committed learner
   result is not undone by a later failed model turn; `record_result` keeps its existing semantics.
6. **Retry safety:** Submission-side idempotency remains necessary for duplicate calls and lost
   responses, even though the model no longer calls the checker. Failures must not create partial
   transcript or result records.
7. **Mathematics:** Supported stated domain restrictions are intersected with the expression's
   original domain. Algebraic root rounding needs a unique isolated root and certified boundary
   treatment. Supported surds and bounded rational linear π forms have exact/certified behavior;
   unsupported inputs and exhausted limits produce no verdict. The plotting parser currently uses
   floats for literals, so the checker must preserve numeric lexemes for exact arithmetic.
8. **Scope and plan:** Chat, voice, revision and review labels remain in scope. Phases can be
   considered after the revised design review; the suggested 023a/b/c split is not an approved
   plan. Spec 022 remains parked and its integration is deferred.

The concrete voice session/report contract, persistence and concurrency details, exact arithmetic
interfaces and bounds, and label representation remain explicitly open in design §10.
