#!/usr/bin/env python3
"""Seal file hashes; optionally create a deterministic ZIP outside the release."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow', ROOT / 'workflow.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def seal(root):
    files = {rel: workflow.digest(workflow.read_file(path)) for rel, path in workflow.package_files(root)}
    manifest = dict(schema=1, package=workflow.PACKAGE,
                    version=(root / 'VERSION').read_text().strip(), files=files)
    (root / 'manifest.json').write_bytes(workflow.json_bytes(manifest))
    (root / 'SHA256SUMS').write_text(''.join(sha + '  ' + rel + '\n' for rel, sha in sorted(files.items())))
    workflow.validate_package(root)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', help='New output ZIP path, outside the release directory')
    args = parser.parse_args()
    manifest = seal(ROOT)
    result = dict(version=manifest['version'], sealed_files=len(manifest['files']))
    if args.archive:
        target = Path(args.archive).expanduser().resolve()
        if ROOT == target or ROOT in target.parents or target.exists():
            raise workflow.WorkflowError('Archive must be new and outside the release directory')
        prefix = workflow.PACKAGE + '-v' + manifest['version']
        with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in sorted([*manifest['files'], 'manifest.json', 'SHA256SUMS']):
                info = zipfile.ZipInfo(prefix + '/' + relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, workflow.read_file(ROOT / relative))
        sha = workflow.digest(target.read_bytes())
        target.with_suffix(target.suffix + '.sha256').write_text(sha + '  ' + target.name + '\n')
        result.update(archive=str(target), sha256=sha)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
