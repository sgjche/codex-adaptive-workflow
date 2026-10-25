#!/usr/bin/env python3
"""Portable Codex workflow installer. Python 3.9+, standard library only."""
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import uuid

PACKAGE = 'codex-adaptive-workflow'
NAMES = ('conversation-alignment', 'decision-interview', 'find-unknowns', 'evidence-checkpoint')
BEGIN = '<!-- codex-adaptive-workflow:begin -->'
END = '<!-- codex-adaptive-workflow:end -->'
STATE = 'codex-adaptive-workflow/state.json'
ROOT = Path(__file__).resolve().parent


class WorkflowError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def guard(path):
    """Reject symlinks, including broken links, along a destination path."""
    for part in (path, *path.parents):
        if part.is_symlink():
            # macOS system aliases are allowed; user-controlled links are not.
            if str(part) in ('/tmp', '/var') and str(part.resolve()) == '/private' + str(part):
                continue
            raise WorkflowError('Refusing symlink: ' + str(part))
        if part != path and part.exists() and not part.is_dir():
            raise WorkflowError('Parent is not a directory: ' + str(part))


def canonical(path):
    path = Path(path).expanduser().absolute()
    guard(path)
    return path.resolve()


def read_file(path):
    guard(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise WorkflowError('Expected regular file: ' + str(path))
    if getattr(info, 'st_flags', 0) & 0x40000000:
        raise WorkflowError('Download this cloud placeholder first: ' + str(path))
    return path.read_bytes()


def snapshot(path):
    guard(path)
    if not path.exists():
        return None
    data = read_file(path)
    return dict(data=base64.b64encode(data).decode('ascii'), sha256=digest(data),
                mode=stat.S_IMODE(path.stat().st_mode))


def content(data, mode=0o644):
    return dict(data=base64.b64encode(data).decode('ascii'), sha256=digest(data), mode=mode)


def decode(snap):
    data = base64.b64decode(snap['data'], validate=True)
    if digest(data) != snap['sha256'] or not isinstance(snap['mode'], int) or not 0 <= snap['mode'] <= 0o777:
        raise WorkflowError('Invalid backup bytes or permissions')
    return data


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def ensure_dir(path, created, mode=0o755):
    guard(path)
    if path.exists():
        if not path.is_dir():
            raise WorkflowError('Expected directory: ' + str(path))
        return
    ensure_dir(path.parent, created, mode)
    path.mkdir(mode=mode)
    created.append(path)


def write_snapshot(path, snap, created):
    guard(path)
    if snap is None:
        if path.exists():
            path.unlink()
        return
    data = decode(snap)
    ensure_dir(path.parent, created)
    fd, temporary = tempfile.mkstemp(prefix='.workflow-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            os.fchmod(stream.fileno(), snap['mode'])
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def transact(operations, destination, created):
    """Preflight the whole set; recover completed writes on ordinary errors."""
    work = []
    for path, before, after in operations:
        current = snapshot(path)
        if current != before and current != after:
            raise WorkflowError('Unexpected edit; no files changed: ' + str(path))
        work.append((path, current, before if destination == 'before' else after))
    if destination == 'before':
        work.reverse()
    completed = []
    try:
        for path, current, desired in work:
            if current == desired:
                continue
            if snapshot(path) != current:
                raise WorkflowError('Concurrent edit: ' + str(path))
            write_snapshot(path, desired, created)
            completed.append((path, current, desired))
    except Exception:
        for path, current, desired in reversed(completed):
            if snapshot(path) == desired:
                write_snapshot(path, current, created)
        raise
    return len(completed)


def package_files(root):
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if any(p in ('.git', '__pycache__') for p in relative.parts):
            continue
        if path.is_symlink():
            raise WorkflowError('Package contains a symlink: ' + str(relative))
        if path.is_file() and str(relative) not in ('manifest.json', 'SHA256SUMS'):
            yield relative.as_posix(), path


def validate_package(root):
    manifest = json.loads(read_file(root / 'manifest.json'))
    if manifest.get('package') != PACKAGE or manifest.get('schema') != 1:
        raise WorkflowError('Unsupported package manifest')
    if read_file(root / 'VERSION').decode().strip() != manifest.get('version'):
        raise WorkflowError('Version and manifest disagree')
    actual = {rel: digest(read_file(path)) for rel, path in package_files(root)}
    if actual != manifest.get('files'):
        raise WorkflowError('Package hashes or file inventory changed; use an intact release')
    sums = ''.join(sha + '  ' + rel + '\n' for rel, sha in sorted(actual.items()))
    if read_file(root / 'SHA256SUMS').decode() != sums:
        raise WorkflowError('SHA256SUMS disagrees with manifest')
    directories = {p.name for p in (root / 'skills').iterdir() if p.is_dir()}
    if directories != set(NAMES):
        raise WorkflowError('Expected exactly four skill directories')
    for name in NAMES:
        folder = root / 'skills' / name
        text = read_file(folder / 'SKILL.md').decode()
        front = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        if not front or not re.search(r'^name: ' + re.escape(name) + r'$', front[1], re.M):
            raise WorkflowError('Invalid skill identity: ' + name)
        if not re.search(r'^description: .+', front[1], re.M):
            raise WorkflowError('Missing skill description: ' + name)
        read_file(folder / 'LICENSE')
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            target = (folder / link.split('#')[0]).resolve()
            if folder.resolve() not in target.parents or not target.is_file():
                raise WorkflowError('Missing or escaping skill reference: ' + link)
        if name != 'conversation-alignment':
            yaml = read_file(folder / 'agents/openai.yaml').decode()
            if len(re.findall(r'^  allow_implicit_invocation: true$', yaml, re.M)) != 1:
                raise WorkflowError('Expected selective source metadata: ' + name)
    policy = read_file(root / 'policy/AGENTS.md').decode()
    for marker in ('conversation-alignment', 'adaptive-workflow'):
        if policy.count('<!-- ' + marker + ':start -->') != 1 or policy.count('<!-- ' + marker + ':end -->') != 1:
            raise WorkflowError('Unbalanced shared policy markers')
    return manifest


class Installer:
    def __init__(self, root, home, codex_home=None):
        self.root = canonical(root)
        self.home = canonical(home)
        self.codex = canonical(codex_home if codex_home is not None else self.home / '.codex')
        if self.home == self.codex or self.home == Path('/') or self.codex == Path('/'):
            raise WorkflowError('Use distinct home and dedicated Codex directories')
        if self.root == self.home or self.root in self.home.parents or self.root == self.codex or self.root in self.codex.parents:
            raise WorkflowError('Installation destinations must be outside the release folder')
        for name in NAMES:
            folder = self.home / '.agents/skills' / name
            if self.codex == folder or folder in self.codex.parents:
                raise WorkflowError('Codex state must be outside managed skill folders')
        self.state_dir = self.codex / PACKAGE
        self.state_file = self.codex / STATE

    def target(self, entry):
        parts = entry['path'].split('/')
        if any(p in ('', '.', '..') for p in parts):
            raise WorkflowError('Unsafe receipt path')
        if entry['root'] == 'home':
            if len(parts) < 4 or parts[:2] != ['.agents', 'skills'] or parts[2] not in NAMES:
                raise WorkflowError('Unapproved skill destination')
            path = self.home.joinpath(*parts)
        elif entry['root'] == 'codex' and entry['path'] in ('AGENTS.md', STATE):
            path = self.codex.joinpath(*parts)
        else:
            raise WorkflowError('Unapproved receipt destination')
        guard(path)
        return path

    def state(self):
        snap = snapshot(self.state_file)
        if snap is None:
            return None
        state = json.loads(decode(snap))
        if state.get('package') != PACKAGE or state.get('schema') != 1:
            raise WorkflowError('Unrecognized installation state')
        return state

    def receipt(self, identifier):
        if not re.fullmatch(r'[0-9TZ-]+-[0-9a-f]{8}', identifier):
            raise WorkflowError('Invalid receipt identifier')
        data = json.loads(read_file(self.state_dir / 'receipts' / (identifier + '.json')))
        if data.get('schema') != 1 or data.get('package') != PACKAGE or data.get('id') != identifier:
            raise WorkflowError('Unrecognized receipt')
        if data['home'] != str(self.home) or data['codex_home'] != str(self.codex):
            raise WorkflowError('Receipt belongs to another destination; do not move receipts between Macs')
        paths = []
        for entry in data['files']:
            paths.append(self.target(entry))
            for snap in (entry['before'], entry['after']):
                if snap is not None:
                    decode(snap)
        required = {self.state_file, self.codex / 'AGENTS.md'} | {
            self.home / '.agents/skills' / name / 'SKILL.md' for name in NAMES}
        if len(paths) != len(set(paths)) or not required.issubset(set(paths)):
            raise WorkflowError('Incomplete or duplicate receipt targets')
        return data

    def check_owned(self, receipt):
        expected = {self.target(e): e['after'] for e in receipt['files']}
        for path, after in expected.items():
            if snapshot(path) != after:
                raise WorkflowError('Installed file edited; preserve/reconcile it before updating: ' + str(path))
        for name in NAMES:
            folder = self.home / '.agents/skills' / name
            for path in folder.rglob('*'):
                if path.is_symlink() or (path.is_file() and path not in expected):
                    raise WorkflowError('Unowned addition inside installed skill: ' + str(path))

    def check_shadow(self):
        override = snapshot(self.codex / 'AGENTS.override.md')
        if override is not None and decode(override).strip():
            raise WorkflowError('A nonempty AGENTS.override.md shadows the shared policy; resolve it explicitly first')

    def plan(self, mode, identifier='pending'):
        if mode not in ('manual', 'selective'):
            raise WorkflowError('Choose manual or selective mode')
        manifest = validate_package(self.root)
        self.check_shadow()
        state = self.state()
        owned = self.receipt(state['receipt']) if state else None
        if owned:
            self.check_owned(owned)
        for name in NAMES:
            legacy = self.codex / 'skills' / name
            guard(legacy)
            if legacy.exists():
                raise WorkflowError('Duplicate legacy skill; no files changed: ' + str(legacy))
            folder = self.home / '.agents/skills' / name
            guard(folder)
            if not owned and folder.exists():
                raise WorkflowError('Existing unowned skill; no files changed: ' + str(folder))
        fingerprint = digest(json_bytes(manifest))
        if state and all(state.get(k) == v for k, v in dict(version=manifest['version'], mode=mode, fingerprint=fingerprint).items()):
            return dict(status='already-installed', version=manifest['version'], mode=mode, files=[], _ops=[])
        desired = {}
        for relative, source in package_files(self.root):
            if not relative.startswith('skills/'):
                continue
            skill_relative = relative[len('skills/'):]
            data = read_file(source)
            if mode == 'manual' and skill_relative.split('/')[0] != 'conversation-alignment' and skill_relative.endswith('/agents/openai.yaml'):
                data = data.replace(b'allow_implicit_invocation: true', b'allow_implicit_invocation: false')
            desired[('home', '.agents/skills/' + skill_relative)] = content(data)
        before_agents = snapshot(self.codex / 'AGENTS.md')
        agents = decode(before_agents).decode('utf-8') if before_agents else ''
        mode_line = ('The three process skills allow selective automatic use.' if mode == 'selective' else
                     'Decision Interview, Find Unknowns, and Evidence Checkpoint are manual-only; invoke them only on explicit user request.')
        block = BEGIN + '\nVersion: ' + manifest['version'] + ' | Mode: ' + mode + '\n' + mode_line + '\n\n'
        block += read_file(self.root / 'policy/AGENTS.md').decode() + END + '\n'
        if owned:
            if agents.count(BEGIN) != 1 or agents.count(END) != 1:
                raise WorkflowError('Managed policy block missing or duplicated')
            start = agents.index(BEGIN)
            end = agents.index(END) + len(END)
            if agents[end:end+1] == '\n':
                end += 1
            agents = agents[:start] + block + agents[end:]
        else:
            if any(marker in agents for marker in (BEGIN, END, '<!-- conversation-alignment:', '<!-- adaptive-workflow:')):
                raise WorkflowError('Existing workflow policy has no installer receipt; reconcile it explicitly first')
            separator = '' if not agents or agents.endswith('\n\n') else ('\n' if agents.endswith('\n') else '\n\n')
            agents += separator + block
        desired[('codex', 'AGENTS.md')] = content(agents.encode(), before_agents['mode'] if before_agents else 0o644)
        new_state = dict(package=PACKAGE, schema=1, version=manifest['version'], mode=mode,
                         fingerprint=fingerprint, receipt=identifier)
        desired[('codex', STATE)] = content(json_bytes(new_state), 0o600)
        keys = set(desired)
        if owned:
            keys.update((e['root'], e['path']) for e in owned['files'])
        entries = []
        for root, relative in sorted(keys, key=lambda k: (k == ('codex', STATE), k)):
            entry = dict(root=root, path=relative)
            path = self.target(entry)
            entry.update(before=snapshot(path), after=desired.get((root, relative)))
            entries.append(entry)
        return dict(status='planned', version=manifest['version'], mode=mode,
                    files=[dict(path=str(self.target(e)), action=('keep' if e['before'] == e['after'] else
                          'create' if e['before'] is None else 'remove' if e['after'] is None else 'update')) for e in entries], _ops=entries)

    @contextmanager
    def locked(self, created):
        ensure_dir(self.state_dir, created, 0o700)
        path = self.state_dir / 'install.lock'
        guard(path)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise WorkflowError('Another installer or stale lock exists: ' + str(path))
        inode = os.fstat(fd).st_ino
        try:
            os.write(fd, str(os.getpid()).encode())
            yield
        finally:
            os.close(fd)
            if path.exists() and path.lstat().st_ino == inode:
                path.unlink()

    def install(self, mode, dry_run=False):
        plan = self.plan(mode)
        if dry_run or plan['status'] == 'already-installed':
            return {k: v for k, v in plan.items() if k != '_ops'}
        created = []
        with self.locked(created):
            identifier = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
            plan = self.plan(mode, identifier)
            if plan['status'] == 'already-installed':
                return {k: v for k, v in plan.items() if k != '_ops'}
            entries = plan['_ops']
            receipt = dict(package=PACKAGE, schema=1, id=identifier, home=str(self.home), codex_home=str(self.codex),
                           version=plan['version'], mode=mode, files=entries)
            receipt_path = self.state_dir / 'receipts' / (identifier + '.json')
            # Record backups before any payload or instruction file changes.
            write_snapshot(receipt_path, content(json_bytes(receipt), 0o600), created)
            operations = [(self.target(e), e['before'], e['after']) for e in entries]
            changed = transact(operations, 'after', created)
        return dict(status='installed', version=plan['version'], mode=mode, changed_files=changed, receipt=identifier)

    def verify(self):
        self.check_shadow()
        state = self.state()
        if not state:
            return dict(status='not-installed')
        self.check_owned(self.receipt(state['receipt']))
        return dict(status='verified', version=state['version'], mode=state['mode'], receipt=state['receipt'])

    def rollback(self, identifier=None):
        state = self.state()
        if identifier is None:
            if not state:
                return dict(status='not-installed')
            identifier = state['receipt']
        receipt = self.receipt(identifier)
        entries = receipt['files']
        state_entry = next(e for e in entries if self.target(e) == self.state_file)
        prior = json.loads(decode(state_entry['before'])) if state_entry['before'] else None
        parent_id = prior['receipt'] if prior else None
        if state and state['receipt'] not in (identifier, parent_id):
            raise WorkflowError('Roll back the most recent installation first')
        if all(snapshot(self.target(e)) == e['before'] for e in entries):
            return dict(status='already-rolled-back', receipt=identifier)
        # Added files are user work too; do not remove part of a changed skill.
        expected_paths = {self.target(e) for e in entries}
        for name in NAMES:
            for path in (self.home / '.agents/skills' / name).rglob('*'):
                if path.is_symlink() or (path.is_file() and path not in expected_paths):
                    raise WorkflowError('Unowned addition blocks rollback: ' + str(path))
        created = []
        with self.locked(created):
            changed = transact([(self.target(e), e['before'], e['after']) for e in entries], 'before', created)
        # Delete only empty directories inside managed skills; keep receipts.
        for name in NAMES:
            folder = self.home / '.agents/skills' / name
            if folder.exists():
                for directory in sorted((p for p in folder.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True) + [folder]:
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
        return dict(status='rolled-back', receipt=identifier, changed_files=changed,
                    restored_version=prior['version'] if prior else None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('validate', 'plan', 'install', 'verify', 'rollback'))
    parser.add_argument('--mode', choices=('selective', 'manual'))
    parser.add_argument('--home', help='Destination user home; defaults to the current user home')
    parser.add_argument('--codex-home', help='Dedicated Codex directory; otherwise CODEX_HOME or <home>/.codex')
    parser.add_argument('--dry-run', action='store_true', help='Preview installation without creating any files')
    parser.add_argument('--receipt', help='Recover a named interrupted installation or repeat a rollback')
    args = parser.parse_args(argv)
    if args.command in ('plan', 'install') and args.mode is None:
        parser.error('--mode selective or --mode manual is required')
    try:
        if args.command == 'validate':
            manifest = validate_package(ROOT)
            result = dict(status='valid', package=PACKAGE, version=manifest['version'], checked_files=len(manifest['files']))
        else:
            home = args.home if args.home else Path.home()
            codex = args.codex_home or (os.environ.get('CODEX_HOME') if args.home is None else None)
            installer = Installer(ROOT, home, codex)
            if args.command == 'plan':
                result = installer.install(args.mode, dry_run=True)
            elif args.command == 'install':
                result = installer.install(args.mode, dry_run=args.dry_run)
            elif args.command == 'verify':
                result = installer.verify()
            else:
                result = installer.rollback(args.receipt)
        print(json.dumps(result, indent=2))
        return 0
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
