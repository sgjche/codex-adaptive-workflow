# Worked examples

[Back to the overview](../README.md)

These examples illustrate how to use the existing skills. They are not benchmark
results or a promise that the model will always select the right procedure.
Run the prompts in Codex chat, not your terminal.

## Choose by the missing piece

| Missing piece | Smallest useful response |
| --- | --- |
| The latest agreed outcome or a previously accepted constraint | Conversation Alignment |
| A consequential choice only the user can make | A focused question; Decision Interview when a bounded interview is useful |
| A consequential fact that can be investigated | Ordinary inspection; Find Unknowns when a bounded investigation is useful |
| Evidence for an important completion claim | An ordinary check; Evidence Checkpoint when the claim or validation needs closer examination |

Do not invoke all four merely because a task is large. A file rename, a settled
choice, or a straightforward calculation may need none of the optional skills.

## 1. Resume a project after a break

**Situation:** a parser refactor has continued over several chats. The accepted
CSV schema and example outputs must be preserved.

```text
$conversation-alignment
Resume the parser refactor using PROJECT_BRIEF.md. Recover the latest agreed
outcome, accepted CSV schema, and current checkpoint. Continue only the next
change we already approved. Preserve the accepted example outputs.
```

**What to expect:** the agent reads the brief and relevant context, distinguishes
the intended outcome from the current implementation, and uses the accepted
constraints while continuing the authorized work. Routine checks can stay quiet.

**Keep it useful:** the brief should identify completion evidence, protected
results, verified state, and unresolved questions. Update it for material
decisions rather than recording every turn. A later explicit instruction can
change the outcome; a hypothetical option does not.

## 2. Resolve a consequential design choice

**Situation:** an application may need to work offline, but the agent is about
to choose a storage architecture before that requirement is settled.

```text
$decision-interview
Before we choose storage for this app, clarify the user choices that could
change the design. Inspect the current project first. Ask only about
consequential preferences, with two or three options and a recommendation.
Stop after the decision summary; do not implement yet.
```

**What to expect:** a small interview focused on preferences such as required
offline behavior or acceptable data retention. Facts already available in the
project should be inspected rather than turned into questions.

**Skip it when:** an ordinary question is enough or the user already settled
the choice. The skill does not reopen a decision just because another design
is possible.

## 3. Check an assumption in a scientific pipeline

**Situation:** a conversion pipeline splits measurements into runs. A unit or
run-boundary assumption could affect the exported results.

```text
$find-unknowns
Review only the run-splitting and unit assumptions in this converter. Use the
source format notes, parser, and a representative fixture. Report at most
three consequential findings with evidence and the cheapest useful check.
Preserve accepted outputs and do not implement fixes.
```

**What to expect:** a bounded investigation that distinguishes observed defects,
untested assumptions, and missing user decisions. Findings might concern a unit
conversion or how a boundary is identified, but “no significant findings” is a
valid result.

**Keep the boundary clear:** review-only scope ends with findings. A proposed
experiment or repair is not permission to perform it. This skill complements
the domain's scientific and data-validation workflow.

## 4. Get out of a debugging loop

**Situation:** repeated local patches suppress an error, but the end-to-end
operation still fails.

```text
$find-unknowns
Investigate the assumption behind the repeated retries in the import flow.
Our agreed outcome is that a user can import the supplied file and inspect
the resulting records. Focus on the parser-to-storage boundary, preserve
accepted behavior, and identify what new evidence would change the approach.
Do not broaden this into a repository-wide review.
```

**What to expect:** the agent checks a named boundary rather than cataloguing
every possible risk. It should explain which findings could change the next
action and where the evidence remains incomplete.

**Skip another scan when:** no new evidence or hypothesis makes it useful.
Repeating the same procedure is not itself progress.

## 5. Check a delivery claim before sharing

**Situation:** an export command reports success. The requested deliverables
also include a combined overview, separate run files, and a source-derived
count check.

```text
$evidence-checkpoint
Review the delivery claim against our agreed brief. The required outputs are
the combined overview, per-run files, and source-derived count reconciliation.
Use existing valid checks, inspect the actual artifacts where needed, and
separate verified results from gaps. Review only; do not modify files.
```

**What to expect:** the agent connects each material criterion to an artifact,
command result, or observed interaction. A successful helper command is useful
evidence, but it may not establish that the full requested delivery exists.

**Keep claims proportional:** an installer check proves packaging behavior;
a mock interaction does not prove a real integration. A clearly labelled
prototype is acceptable when that is what was requested.

## A short project brief

The [full template](../skills/conversation-alignment/assets/PROJECT_BRIEF.template.md)
includes space for provenance and changes to the outcome. A concise brief might
start like this:

```markdown
# Project brief: measurement import

## Outcome
Import the supplied measurement files and produce traceable per-run exports.

## Completion evidence
- Representative files import successfully.
- Exported row counts reconcile with the source.
- Accepted CSV columns and example outputs are preserved.

## Accepted decisions and constraints
- Preserve the existing CSV schema.
- Keep a combined aligned export alongside the separate run files.

## Verified project state
- The supplied fixture parses; boundary handling still needs confirmation.

## Open questions
- Whether the final source record belongs to the last run is unverified.
```

Use decisions from your own project. Do not treat an example brief as authority
to expand a task.

## What selective activation looks like

In selective mode, a process skill is instructed to send one short notice when
it starts, for example:

> Skill: Evidence Checkpoint — checking whether the delivered files cover the agreed output list.

Conversation Alignment stays quiet during routine alignment. Notices identify
an invocation; they are not proof that its findings are correct. You can still
explicitly invoke a skill in either mode.

## Switching to manual process skills

From the same package version used for your installation:

```sh
python3 workflow.py plan --mode manual
python3 workflow.py install --mode manual
python3 workflow.py verify
```

The mode change is reversible. An existing unmanaged installation or later
local edits can require reconciliation; see the
[installation guide](INSTALLATION.md).
