# Shared spec-driven workflow

This workflow is independent of a particular assistant or plugin. Claude's `sdd` plugin may be used when available; the same stages and files can also be maintained directly by another assistant. The user can override the workflow or its review gates for a specific task.

## Before starting

- Read `specs/product.md`, `specs/index.md`, relevant feature specs, and the current implementation and documentation. Earlier specs may have been superseded by later ones.
- Check the branch and working tree. Specs or implementation may live on different branches; inspect them before choosing a base. Do not switch branches or overwrite work casually.
- Respect a spec's recorded status, including a decision to park it. Discuss resuming it with the user before planning or implementation.
- Identify product invariants, dependencies, existing decisions, and uncertainties. Treat model-written text and existing implementation as evidence to check, not proof of correctness.

## Stages

1. **Requirements:** agree on the problem, scope, user-visible behavior, constraints, acceptance criteria, and open questions in `specs/NNN-<slug>/requirements.md`.
2. **Design:** describe the approach, interfaces, data, failure handling, verification, and any deviations or tradeoffs in `design.md`. Identify decisions that change approved requirements.
3. **Plan:** break the approved design into reviewable tasks and meaningful checks in `tasks.md`, with dependencies and status.
4. **Implement:** follow the plan, verify behavior against acceptance criteria, and update tasks and relevant documentation. Record material deviations and resolve them with the user when they change agreed behavior.
5. **Verify:** review implementation and evidence against the requirements and invariants; record remaining gaps and checks not run.

The user reviews each stage before the next begins, unless they explicitly authorize a different sequence. A review can be a conversation: record the decisions and unresolved questions in the spec so another assistant can continue. Avoid converting a proposal into an approved decision without the user's agreement.

## File outlines

Every spec file uses the same outline, whichever assistant writes it (it is the outline Claude's `sdd` plugin follows). The files are read by coding agents: keep them concise, without filler, estimates or timelines.

**`requirements.md`**
1. Introduction: the feature, its purpose and its value to users.
2. Alignment with the product vision: how it serves `specs/product.md`.
3. Requirements: numbered (R1, R2, …), each a user story (*As a [role], I want [feature], so that [benefit]*) with numbered, testable acceptance criteria.
4. Non-functional requirements: architecture, performance, security, reliability, usability.
5. Out of scope and open questions, when there are any; the user's answers are recorded here as decisions, with their date.

**`design.md`**
1. Overview: the goal and the design at a glance; design decisions that narrow or change the approved requirements are listed here for the user to approve.
2. Architecture: a high-level diagram of the solution.
3. Components and interfaces to add or change.
4. Data models: new and changed entities, DTOs and migrations.
5. Error handling.
6. Testing strategy.
7. Performance considerations.
8. Security considerations.
9. Monitoring and observability.

**`tasks.md`** (the plan, and the status report during implementation)
- Phases, in order. A phase is a testable increment: a goal, a clear target, integration tests where possible, and an action the user can perform to verify its output.
- Tasks within a phase, as checkboxes. A coding task names the unit tests that validate it.
- During implementation, a phase is marked complete only once its tests and verification pass; deviations from the design are recorded here and reported to the user.

**Verification report** (stage 5; changes nothing)
- A code review of the diff, and a check of the implementation against every acceptance criterion, the design, and the tasks marked complete.
- One consolidated list of findings, ordered by criticality, then effort; each with criticality (critical / high / medium / low), effort (low / medium / high), source and a concise description.
- An opinionated recommendation: what to fix now, what can wait, and why.

**Review notes** (optional): a review of a spec by another assistant or person goes in `specs/NNN-review.md` until its agreed decisions are carried into the spec's files; it separates agreed decisions from proposals and open questions.

## Maintaining specs

- Keep `specs/index.md` current about stage, implementation status, review and verification gaps. Keep the product brief and functional documentation aligned when behavior changes.
- When revising an existing spec, preserve its history and decisions; distinguish proposed changes from agreed ones and identify affected later specs. Do not rewrite completed implementation as if it were already verified against new requirements.
- Keep acceptance criteria testable, including edge cases, failure states and limitations. Tests should substantiate behavior rather than merely reproduce implementation details.
- Use the existing numbering and `requirements.md` / `design.md` / `tasks.md` convention where applicable. Some existing specs document user-approved exceptions to this format; retain those records.
- For handoff, leave enough context in the files to identify the current branch, stage, decisions, outstanding questions and verification evidence. Git records branch history; avoid embedding a transient branch name as a permanent requirement.
