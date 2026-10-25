"""Installer tests use disposable destination homes only; no model calls."""
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow', ROOT / 'workflow.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
spec = importlib.util.spec_from_file_location('build_release', ROOT / 'tools/build_release.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='codex-workflow-test-')
        self.base = Path(self.temporary.name).resolve()
        self.home = self.base / 'Different User' / 'Home'
        self.home.mkdir(parents=True)
        self.installer = w.Installer(ROOT, self.home)

    def tearDown(self):
        self.temporary.cleanup()

    def inventory(self):
        return {p.relative_to(self.home).as_posix(): w.snapshot(p)
                for p in self.home.rglob('*') if p.is_file() or p.is_symlink()}

    def existing_agents(self, data=b'Local preference without trailing newline'):
        path = self.home / '.codex/AGENTS.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o640)
        return path

    def test_package_integrity(self):
        manifest = w.validate_package(ROOT)
        self.assertEqual(manifest['version'], '0.1.0')

    def test_preview_is_read_only(self):
        self.existing_agents()
        before = self.inventory()
        plan = self.installer.install('selective', dry_run=True)
        self.assertEqual(plan['status'], 'planned')
        self.assertEqual(before, self.inventory())
        self.assertFalse(self.installer.state_dir.exists())

    def test_install_verify_and_exact_restore(self):
        agents = self.existing_agents()
        original = w.snapshot(agents)
        config = agents.parent / 'config.toml'
        config.write_text('model = "existing-setting"\n')
        config_before = w.snapshot(config)
        self.installer.install('selective')
        self.assertEqual(self.installer.verify()['status'], 'verified')
        self.assertTrue(agents.read_bytes().startswith(w.decode(original)))
        self.assertEqual(stat.S_IMODE(agents.stat().st_mode), 0o640)
        self.assertEqual(w.snapshot(config), config_before)
        for name in w.NAMES:
            self.assertTrue((self.home / '.agents/skills' / name / 'SKILL.md').is_file())
        self.assertEqual(self.installer.rollback()['status'], 'rolled-back')
        self.assertEqual(w.snapshot(agents), original)
        self.assertEqual(w.snapshot(config), config_before)
        self.assertFalse((self.home / '.agents/skills/decision-interview').exists())
        self.assertIsNone(self.installer.state())

    def test_fresh_install_rollback_removes_created_agents(self):
        result = self.installer.install('selective')
        self.installer.rollback()
        self.assertFalse((self.home / '.codex/AGENTS.md').exists())
        self.assertEqual(self.installer.rollback(result['receipt'])['status'], 'already-rolled-back')

    def test_reinstall_is_idempotent(self):
        first = self.installer.install('selective')
        before = self.inventory()
        second = self.installer.install('selective')
        self.assertEqual(second['status'], 'already-installed')
        self.assertEqual(before, self.inventory())
        self.assertEqual(self.installer.state()['receipt'], first['receipt'])

    def test_manual_mode_and_rollback_chain(self):
        first = self.installer.install('selective')
        self.installer.install('manual')
        for name in w.NAMES[1:]:
            text = (self.home / '.agents/skills' / name / 'agents/openai.yaml').read_text()
            self.assertIn('allow_implicit_invocation: false', text)
        with self.assertRaises(w.WorkflowError):
            self.installer.rollback(first['receipt'])
        self.installer.rollback()
        self.assertEqual(self.installer.state()['receipt'], first['receipt'])
        for name in w.NAMES[1:]:
            self.assertIn('allow_implicit_invocation: true', (self.home/'.agents/skills'/name/'agents/openai.yaml').read_text())
        self.installer.rollback()
        self.assertIsNone(self.installer.state())

    def test_custom_codex_home(self):
        codex = self.base / 'Custom configuration'
        installer = w.Installer(ROOT, self.home, codex)
        installer.install('selective')
        self.assertTrue((codex / 'AGENTS.md').exists())
        self.assertFalse((self.home / '.codex').exists())
        self.assertEqual(installer.verify()['status'], 'verified')
        installer.rollback()
        self.assertFalse((codex / 'AGENTS.md').exists())

    def test_unowned_and_legacy_skills_block_without_mutation(self):
        for relative in ('.agents/skills/find-unknowns', '.codex/skills/find-unknowns'):
            with self.subTest(relative=relative):
                path = self.home / relative
                path.mkdir(parents=True)
                (path / 'SKILL.md').write_text('Existing personal skill')
                before = self.inventory()
                with self.assertRaises(w.WorkflowError):
                    self.installer.install('selective')
                self.assertEqual(before, self.inventory())
                shutil.rmtree(path)

    def test_shadowing_override_and_old_policy_block(self):
        agents = self.existing_agents(b'<!-- adaptive-workflow:start -->\nExisting workflow\n')
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.install('selective')
        self.assertEqual(before, self.inventory())
        agents.write_text('Ordinary instruction')
        override = agents.parent / 'AGENTS.override.md'
        override.write_text('Overrides global policy')
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.install('selective')
        self.assertEqual(before, self.inventory())

    def test_symlink_destination_is_not_followed(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.home / '.agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(w.WorkflowError):
            self.installer.install('selective')
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.home / '.codex').exists())

    def test_later_edit_blocks_whole_rollback_and_update(self):
        self.installer.install('selective')
        modified = self.home / '.agents/skills/find-unknowns/SKILL.md'
        modified.write_text(modified.read_text() + '\nUser edit\n')
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.rollback()
        self.assertEqual(before, self.inventory())
        with self.assertRaises(w.WorkflowError):
            self.installer.install('manual')
        self.assertEqual(before, self.inventory())

    def test_additional_user_file_blocks_rollback(self):
        self.installer.install('selective')
        (self.home / '.agents/skills/find-unknowns/user-note.md').write_text('Keep me')
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.rollback()
        self.assertEqual(before, self.inventory())

    def test_partial_write_failure_restores_payloads(self):
        agents = self.existing_agents()
        original = w.snapshot(agents)
        real_write = w.write_snapshot
        count = 0
        def fail_once(path, snap, created):
            nonlocal count
            if '/.agents/skills/' in str(path):
                count += 1
                if count == 3:
                    raise OSError('Injected disk write failure')
            return real_write(path, snap, created)
        with mock.patch.object(w, 'write_snapshot', side_effect=fail_once):
            with self.assertRaises(OSError):
                self.installer.install('selective')
        self.assertEqual(w.snapshot(agents), original)
        self.assertIsNone(self.installer.state())
        self.assertFalse(any(p.is_file() for p in (self.home/'.agents/skills').rglob('*')))
        self.assertFalse((self.installer.state_dir / 'install.lock').exists())
        receipt = next((self.installer.state_dir / 'receipts').glob('*.json'))
        self.assertEqual(self.installer.rollback(receipt.stem)['status'], 'already-rolled-back')

    def test_backup_tampering_is_rejected(self):
        installed = self.installer.install('selective')
        path = self.installer.state_dir / 'receipts' / (installed['receipt'] + '.json')
        receipt = json.loads(path.read_text())
        next(e for e in receipt['files'] if e['before'] is None)['after']['data'] = 'dGFtcGVyZWQ='
        path.write_text(json.dumps(receipt))
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.rollback()
        self.assertEqual(before, self.inventory())

    def test_interrupted_install_recovers_from_prepared_receipt(self):
        agents = self.existing_agents()
        original = w.snapshot(agents)
        def interrupt(operations, destination, created):
            for path, before, after in operations[:4]:
                w.write_snapshot(path, after, created)
            raise KeyboardInterrupt('Simulated abrupt stop after durable backup')
        with mock.patch.object(w, 'transact', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.installer.install('selective')
        self.assertIsNone(self.installer.state())
        self.assertNotEqual(w.snapshot(agents), original)
        receipt = next((self.installer.state_dir / 'receipts').glob('*.json'))
        self.assertEqual(self.installer.rollback(receipt.stem)['status'], 'rolled-back')
        self.assertEqual(w.snapshot(agents), original)
        self.assertFalse((self.home / '.agents/skills/conversation-alignment').exists())

    def test_existing_lock_blocks_install_without_changes(self):
        lock = self.installer.state_dir / 'install.lock'
        lock.parent.mkdir(parents=True)
        lock.write_text('another installer')
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.install('selective')
        self.assertEqual(before, self.inventory())

    def test_parent_file_and_overlapping_state_are_rejected(self):
        (self.home / '.agents').write_text('A file occupying the intended directory')
        before = self.inventory()
        with self.assertRaises(w.WorkflowError):
            self.installer.install('selective')
        self.assertEqual(before, self.inventory())
        with self.assertRaises(w.WorkflowError):
            w.Installer(ROOT, self.home, self.home / '.agents/skills/find-unknowns/config')

    def test_receipt_path_traversal_is_rejected(self):
        installed = self.installer.install('selective')
        path = self.installer.state_dir / 'receipts' / (installed['receipt'] + '.json')
        receipt = json.loads(path.read_text())
        receipt['files'][0]['path'] = '../outside'
        path.write_text(json.dumps(receipt))
        with self.assertRaises(w.WorkflowError):
            self.installer.rollback()
        self.assertFalse((self.base / 'outside').exists())

    def test_cli_round_trip_with_spaced_destination(self):
        def run(*args):
            result = subprocess.run([sys.executable, '-I', '-B', str(ROOT/'workflow.py'), *args,
                                     '--home', str(self.home)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertEqual(run('plan', '--mode', 'selective')['status'], 'planned')
        self.assertFalse(self.installer.state_dir.exists())
        self.assertEqual(run('install', '--mode', 'selective')['status'], 'installed')
        self.assertEqual(run('verify')['status'], 'verified')
        self.assertEqual(run('rollback')['status'], 'rolled-back')

    def test_relocated_release_upgrade_and_restore(self):
        first = self.installer.install('selective')
        relocated = self.base / 'Relocated Release'
        shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        (relocated / 'VERSION').write_text('0.1.1\n')
        extra = relocated / 'skills/find-unknowns/references/new-guide.md'
        extra.write_text('An added resource in a simulated later release.\n')
        builder.seal(relocated)
        upgrade = w.Installer(relocated, self.home)
        upgrade.install('selective')
        self.assertEqual(upgrade.verify()['version'], '0.1.1')
        installed_extra = self.home / '.agents/skills/find-unknowns/references/new-guide.md'
        self.assertTrue(installed_extra.exists())
        upgrade.rollback()
        self.assertEqual(self.installer.verify()['version'], '0.1.0')
        self.assertFalse(installed_extra.exists())
        self.assertEqual(self.installer.state()['receipt'], first['receipt'])
        self.installer.rollback()

    def test_modified_release_fails_integrity_check(self):
        altered = self.base / 'Altered Release'
        shutil.copytree(ROOT, altered, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        (altered / 'skills/decision-interview/SKILL.md').write_text('Modified payload')
        installer = w.Installer(altered, self.home)
        with self.assertRaises(w.WorkflowError):
            installer.install('selective')
        self.assertFalse((self.home / '.codex').exists())


if __name__ == '__main__':
    unittest.main()
