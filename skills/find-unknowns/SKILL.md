---
name: find-unknowns
description: Find consequential assumptions and blind spots in a named component, scientific method, or dataset. Use for a requested unknowns check or an important uncertainty that inspection can resolve; skip exhaustive audits and speculative risk catalogues.
license: MIT
---

# Find unknowns

Find uncertainties that could change the next decision. Use selectively
when a consequential assumption needs a bounded investigation; prefer
ordinary inspection when one check suffices. An investigation alone does
not authorize implementing fixes or an independent reviewer.

Anchor the review in the latest endorsed outcome, the current request, and
accepted results. Name one component, method, or data boundary to investigate.
Use the supplied evidence and relevant project context; avoid unrelated files
and a whole-repository scan when a narrower question will do.

Choose the lens that fits: interface/state assumptions, dependencies, actual
user behavior, units and data selection, method identifiability, controls, or
alternative explanations. Do not run every lens or load other skills merely
because they are available.

Start with up to six targeted evidence-gathering calls for the optional scan.
Batch related reads where practical. These are an initial allowance, not a
claim of complete coverage or permission to skip required validation. If the
allowance is insufficient, report the unresolved question and next useful
check instead of expanding silently or declaring success.

Report at most three material findings. For each, give the supporting file,
observation, or source; distinguish an observed defect, an untested assumption,
and a missing user decision. Explain why it could affect the intended result
and name the cheapest check that would distinguish the plausible explanations.
Allow no significant findings; do not invent problems to fill the list.

Do not infer causation from timing or a failed setup, or treat an improved
proxy as proof of the actual result. Preserve accepted outputs while testing a
hypothesis. When a small experiment is useful, read
[the assumption-test guide](references/assumption-test.md); perform it only
when it falls within the current authorization. Otherwise propose it.

Return the bounded findings, coverage limits, and useful next check. A
standalone investigation ends there. Inside an already authorized task,
use the findings to resume that same task; do not launch a full review,
implement a speculative fix, change the project outcome, or automatically
chain further skills. Existing authorization still governs any repair.
