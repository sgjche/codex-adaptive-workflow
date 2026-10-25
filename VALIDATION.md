# v0.1.0 validation record

Prepared locally on 17 October 2026. Runtime tests used Python 3.9.6 on macOS
with Apple Silicon. The installer uses the standard library only.

**21 installer tests passed.** They cover read-only preview, installation and
verification, exact restoration of original bytes and permissions, preservation
of unrelated configuration, clean uninstall, idempotent reinstall, manual mode,
rollback ordering, custom Codex homes, duplicate/unowned skills, global
overrides, old policy blocks, symlinks, parent-path conflicts, later edits,
added user files, caught write failure, abrupt interruption recovery, locks,
backup corruption, receipt traversal, CLI paths with spaces, relocated-package
upgrade to a simulated later release, and package tampering.

All **four skills passed the official Skill Creator quick validator** during
preparation. Their bodies, metadata, licenses, and bundled resources were copied
without changes from the working installation. The shared policy omits the
source machine's unrelated preferences and wraps one long line for portability.

The package's `validate` command checks release inventory and hashes, version,
skill identity and descriptions, selective source metadata, relative skill
references, and policy markers. It is not a general YAML validator. The official
validator and its temporary development dependency are not needed for use.

The release preparation also checks an extracted ZIP at a different path with
spaces: validate, read-only preview, selective install, verify, manual-mode
update, rollback to selective, and rollback to the initial state. All writes
for these checks are confined to disposable destination homes. Release ZIP and
individual source files have SHA-256 manifests.

The source Mac's global instructions, project brief, configuration, four live
skill folders, and existing manual skill metadata are tracked separately as
21 preserved paths. No live installation or GitHub upload is part of this
release preparation. Private path-level preservation receipts stay outside
the portable archive.

These checks establish packaging and installer behavior. They do not establish
reliable model-triggered selection, guaranteed notices, Desktop picker behavior,
compaction recovery, or improved outcomes on multi-day tasks. A second-Mac acceptance check passed on 17 October 2026 with Python 3.14.4:
installation, verification, exact rollback, reinstallation, and final
verification succeeded. All 36 pre-existing unrelated skill entries remained
unchanged. This was an installer check, not a model-activation test. Linux,
Windows, Claude Science, and a plugin wrapper have not been tested in this release.

Run the included tests with `python3 -B -m unittest discover -s tests -v`.

## Public source preparation

The first public v0.1.0 source was prepared on 25 October 2026. Publication
updates the installation instructions and this historical validation record.
The four skill payloads, shared policy, installer, tests, and build script
remain byte-for-byte identical to the previously validated portable package.
The public source has regenerated integrity manifests; its hashes therefore
differ from the original private-transfer archive. Both describe their own
exact file inventories. Personal briefs, machine-specific receipts, private
paths, credentials, and conversation logs are excluded.
