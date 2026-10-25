# Installation and recovery

[Back to the overview](../README.md)

## Install the complete set

Requires **Python 3.9 or newer**, with no third-party Python packages.
macOS is the validated platform. Clone the versioned release:

```sh
git clone --branch v0.1.0 https://github.com/sgjche/codex-adaptive-workflow.git
cd codex-adaptive-workflow
```

Or download and extract the source ZIP from the v0.1.0 GitHub release.
All shell commands in this guide run from the repository or extracted release
root, not from the `docs/` folder:



```sh
python3 workflow.py validate
python3 workflow.py plan --mode selective
python3 workflow.py install --mode selective
python3 workflow.py verify
```

`plan` is read-only. The `install` command explicitly authorizes installing all
four skills and merging the shared policy. Choose `--mode manual` instead to
keep the three process skills explicit-only. Conversation Alignment remains
available for substantive project work in either mode. A later `install` with
another mode creates a reversible update; an identical reinstall is a no-op.

Installed locations:

- Four skill folders in `~/.agents/skills/`, the documented user skill location.
- One marked policy block in the selected Codex home's `AGENTS.md`.
- Private backup receipts and installation state in that Codex home's
  `codex-adaptive-workflow/` directory.

The default Codex home is `CODEX_HOME` when configured, otherwise `~/.codex`.
`--codex-home` selects another dedicated directory. `--home` selects a different
destination user home and defaults its Codex home to `<home>/.codex`; this
explicit test destination does not inherit the caller's `CODEX_HOME`.

Existing instructions and file permissions are preserved. The installer
refuses conflicting skill folders in either user skill location, older
unmanaged workflow policy blocks, nonempty global overrides, symlinks, and
locally edited managed files. It never edits `config.toml`, project briefs,
credentials, chat history, or unrelated skills. Existing unmanaged copies need
an explicit migration; this release does not silently adopt them.

Codex detects skill changes automatically. If availability or instructions look
stale, restart Codex and reopen the existing chat. Project overrides, disabled
skills, other profiles, or managed settings can still affect behavior; verify
availability in the destination app. `verify` checks installed files and policy,
not the model's decisions or the Desktop picker.

## Roll back

```sh
python3 workflow.py rollback
```

This restores the most recent installation's original files and permissions,
or removes files it created. Repeated calls unwind updates in order. Private
backup receipts remain for recovery. Unexpected later edits or added files
inside a managed skill cause refusal before changes; preserve and reconcile
those edits explicitly. There is no force-overwrite option.

Each file replacement is atomic. A caught write failure restores completed
writes when their content is still unchanged. A killed process or power loss
can leave a partial installation: backups were written first, so recover using
the receipt ID from the Codex home's `codex-adaptive-workflow/receipts/` folder:

```sh
python3 workflow.py rollback --receipt RECEIPT_ID
```

A stale `install.lock` blocks another installer. Remove it only after confirming
no installer is running. Recovery is guarded and is not a filesystem-wide
transaction. Do not edit affected files while installation or rollback runs.

## Project setup and validation

Use the [blank brief template](../skills/conversation-alignment/assets/PROJECT_BRIEF.template.md)
inside Conversation Alignment's `assets/` folder. Keep each actual brief and
handoff with its own project. Configure a project
pointer when needed; no personal brief or conversation history is distributed.

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use disposable homes, including paths with spaces, and make no model
calls. File hashes, skill metadata, reference closure, installation, updates,
conflict handling, and rollback are checked. The development validation record
is in [VALIDATION.md](../VALIDATION.md). Automatic selection and announcements remain model-guided;
installation checks do not establish reliable activation or multi-day benefit.
Claude Science and plugin packaging are outside v0.1.0.

For maintainers: run `python3 tools/build_release.py` after intentional source
or documentation changes to regenerate the integrity manifests. Prepare a new
version when making a new release; preserve existing published tags and assets.
Add `--archive ../release.zip` to create a new deterministic ZIP and its SHA-256.
Checksums detect changes; they are not a publisher signature. Keep installation
receipts, personal backups, and private project data outside the source package.

[MIT license](../LICENSE). Existing notices are retained with each skill.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development and release guidance.

Official references: [skills and invocation policies](https://learn.chatgpt.com/docs/build-skills)
and [instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
