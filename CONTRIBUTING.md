# Contributing

Thanks for helping make Codex Adaptive Workflow more useful and less intrusive.
The aim is a small set of checks that support user-guided work.

## Useful contributions

- A sanitized example of missed activation, repeated questions, goal drift,
  or a check that added effort without changing the result.
- A clearer skill description or a narrower trigger and skip condition.
- An installer fix with a reproducible case and appropriate regression coverage.
- Documentation, examples, or evidence about a previously untested platform.

Changes should preserve the user's latest explicit direction, accepted work,
and the boundary of the current request. Broad new orchestration, automatic
reviewers, recurring tasks, and mandatory skill sequences need a separate
design discussion.

## Reporting a workflow problem

[Open an issue](https://github.com/sgjche/codex-adaptive-workflow/issues/new) with:

1. Your Codex surface, platform, package version, and selective/manual mode.
2. The task you intended and the relevant constraints.
3. A short sanitized prompt or reproduction.
4. The skill you expected, the notice or behavior you observed, and why the
   difference mattered.
5. What evidence is available and what remains uncertain.

Remove credentials, personal data, private source code, and full chat histories.
A small example is usually more useful than an entire transcript. Keep measured
results separate from hypotheses and anticipated benefits.

## Local development

Clone the repository and use Python 3.9 or newer. No third-party dependencies
are required for the installer or its tests.

```sh
python3 workflow.py validate
python3 -B -m unittest discover -s tests -v
```

Installer tests use disposable destination homes. Do not use your real home as
a test destination.

For a proposed source or documentation change, regenerate the integrity
manifests, then validate and run the relevant checks:

```sh
python3 tools/build_release.py
python3 workflow.py validate
python3 -B -m unittest discover -s tests -v
```

The manifests cover documentation as well as the installed payload. Commit
`manifest.json` and `SHA256SUMS` with changes they describe. Keep test logs,
private receipts, local backups, and actual project briefs outside the package.

## Pull requests

Explain the concrete problem, the resulting behavior, and the evidence used to
check the change. For skill changes, include an example that should trigger the
skill and one that should skip it. Installation tests alone do not establish
model-triggered behavior.

Keep changes focused and preserve original license notices. Existing published
tags and release assets are immutable project references; a future release
should get a new version and its own validation record.

## Documentation changes

`main` may contain unreleased documentation improvements while `VERSION`
continues to identify the latest runtime release. Regenerate the manifests for
those changes. A release version bump and its version-dependent test
expectations belong in an explicit release-preparation change.

The README should explain the intended user benefit, show a first runnable
example, and link to detailed instructions. Avoid unsupported performance
claims, guaranteed activation claims, or badges for checks that do not exist.
