---
name: evidence-checkpoint
description: Check an important milestone or completion claim against the latest agreed outcome and actual evidence. Use for a requested evidence check, conflicting evidence, a suspected shortcut, or acceptance-impacting validation changes; skip routine status recaps and duplicate validation.
license: MIT
---

# Evidence checkpoint

Check whether the current result satisfies the actual request. Use
selectively for an important claim with conflicting evidence, a suspected
shortcut, or acceptance-impacting validation changes. Prefer an ordinary
check when it suffices. Complement Conversation Alignment and the domain
workflow; do not duplicate their checks or add an independent reviewer.

Recover the latest user-endorsed outcome and current turn's scope from the
relevant conversation and configured brief. Explicit later steering can
supersede prompt #1. Keep accepted constraints and artifacts intact. Start
with the brief, relevant decisions, current change, and existing evidence;
retrieve older conversation sections only to resolve a specific ambiguity.

For each material completion criterion, identify the artifact, command result,
retrieved source, or observed interaction supporting it. Distinguish verified,
partial, contradicted, and unavailable evidence. Check the actual result when
practical; a narrative claim or passing helper test alone may not establish
the user-facing outcome. Reuse still-valid checks rather than rerunning them
without a new reason, and disclose gaps instead of assuming they passed.

Look for compromises that weaken the criterion: hidden hardcoding, mocks
presented as real results, omitted edge cases, skipped required validation,
or improvements to a proxy that damage accepted work. An intentional,
clearly labeled prototype or a justified constant is not automatically a
defect. Judge it against the promised deliverable.

If an implementation request already authorizes a routine repair, complete
and verify it. A review-only request authorizes findings, not repairs. Ask for
a user decision only when a consequential tradeoff, scope change, new material
cost, or authorization is actually unresolved; preserve earlier permissions.
Do not ask for blanket approval to deliver a lower-quality result.

Report material findings with evidence and the smallest useful next action.
If aligned, a short conclusion is enough. Do not require a status panel, a
full transcript replay, a separate reviewer, or a menu of next steps on every
reply. Return control after the current authorized request; this checkpoint
does not activate native Goals, follow-up turns, or delegation.
