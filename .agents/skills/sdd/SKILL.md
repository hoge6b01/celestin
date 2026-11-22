---
name: sdd
description: Apply Célestin's shared spec-driven workflow when the user asks to create, review, revise, plan, implement, or verify a feature spec. Use the same spec files and decisions as Claude's SDD workflow.
---

# Célestin spec-driven development

Use the repository's `specs/WORKFLOW.md` as the shared source for stages, review gates and file formats. Read `specs/product.md`, `specs/index.md`, the relevant feature specs and review notes, and applicable project instructions. Check the actual code and documentation for the feature; later specs can supersede earlier ones.

Check the current branch, working tree and relevant branch history before editing. The spec or shared workflow may live on another branch: inspect it read-only and make that distinction clear. If `specs/WORKFLOW.md` is absent in the current checkout, look for it on the project's SDD branch, such as `git show feature/023-answer-checker:specs/WORKFLOW.md`. Do not silently switch branches, overwrite changes, or treat a historical spec as current behavior.

Work at the stage the user requested: requirements, design, plan, implementation or verification. Follow the shared workflow's review gates unless the user authorizes another sequence. Review and refinement may be conversational; record agreed decisions, unanswered questions and relevant evidence in the existing spec files or a review note. Do not record a proposal as an approved decision. Respect parked work and distinguish reviewing it from resuming planning or implementation.

Keep Claude and Codex interoperable: use the existing numbered `specs/NNN-<slug>/` files, preserve the project's established file outlines and update `specs/index.md` when the spec's status changes. Carry earlier user decisions forward, identify changes to approved requirements and affected dependent specs, and leave a clear handoff. Do not require Claude's plugin commands in Codex; Claude may use its plugin according to the repository instructions.

For implementation, follow the approved plan, run checks appropriate to the change, update task status and relevant documentation, and report deviations and unrun checks. For verification, compare the implementation with requirements, design and completed tasks, and report findings and evidence without changing the implementation unless the user requests fixes.
