import argparse
import copy
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

SOURCE = Path(__file__).resolve().parents[1] / 'x2i.py'
spec = importlib.util.spec_from_file_location('x2i', SOURCE)
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
SERIAL = 'TESTUSB1234'


def identity():
    return {'ro.serialno': SERIAL, 'ro.product.device': 'Jenna', 'ro.board.platform': 'rk3326',
            'ro.build.version.sdk': '30', 'ro.product.cpu.abi': 'arm64-v8a',
            'ro.build.fingerprint': x.FINGERPRINT, 'shelly_version': x.FIRMWARE}


def make_boot(path, size=4096, version=2):
    data = bytearray(size)
    data[:8] = b'ANDROID!'
    struct.pack_into('<I', data, 40, version)
    path.write_bytes(data)
    return path


class ValidationTests(unittest.TestCase):
    def test_serial_usb_only(self):
        self.assertEqual(x.serial_value(SERIAL), SERIAL)
        for bad in ['192.0.2.1:5555', '../unit', 'a;reboot', 'x\nroot', '', 'a' * 65]:
            with self.subTest(bad=bad), self.assertRaises(x.Stop):
                x.serial_value(bad)

    def test_dashboard_no_embedded_credentials_or_tokens(self):
        self.assertEqual(x.dashboard_value('http://homeassistant.local:8123/lovelace/0'), 'http://homeassistant.local:8123/lovelace/0')
        for bad in ['file:///data', 'https://user:secret@example.invalid/', 'https://example.invalid/?token=test',
                    'https://example.invalid/#credential', 'http://', 'javascript:alert(1)']:
            with self.subTest(bad=bad), self.assertRaises(x.Stop):
                x.dashboard_value(bad)

    def test_exact_build_allowed(self):
        x.check_identity(identity(), SERIAL)

    def test_each_identity_mismatch_rejected(self):
        for key in identity():
            data = identity()
            data[key] = 'different'
            with self.subTest(field=key), self.assertRaises(x.Stop):
                x.check_identity(data, SERIAL)

    def test_marketing_version_is_not_enough(self):
        data = identity()
        data['shelly_version'] = '2.7.4-otherbuild'
        with self.assertRaises(x.Stop):
            x.check_identity(data, SERIAL)

    def test_first_package_version_not_hidden_system_copy(self):
        self.assertEqual(x.parse_first_version('Packages:\n versionName=2.7.4-b7b6bc07\nHidden system packages:\n versionName=2.6.0-old'), x.FIRMWARE)

    def test_missing_version_rejected(self):
        with self.assertRaises(x.Stop):
            x.parse_first_version('no package')

    def test_privileged_flags_require_real_tokens(self):
        self.assertTrue(x.is_privileged(' flags=[ SYSTEM UPDATED_SYSTEM_APP ]\n privateFlags=[ PRIVILEGED ]'))
        self.assertFalse(x.is_privileged(' flags=[ HAS_CODE ]\n privateFlags=[ NOT_PRIVILEGED ]\n android.permission.SYSTEM_ALERT_WINDOW'))
        self.assertFalse(x.is_privileged(' flags=[ UPDATED_SYSTEM_APP ]\n privateFlags=[ PRIVILEGED ]'))

    def test_checks_survive_python_optimization(self):
        code = ('import importlib.util; s=importlib.util.spec_from_file_location("x",' + repr(str(SOURCE)) + '); '
                'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.serial_value("not:a:usb:serial")')
        result = subprocess.run([sys.executable, '-O', '-c', code], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Use a physical USB serial', result.stderr)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_boot_valid(self):
        x.validate_boot(make_boot(self.root / 'boot.img'))

    def test_boot_wrong_header(self):
        with self.assertRaises(x.Stop):
            x.validate_boot(make_boot(self.root / 'boot.img', version=3))

    def test_boot_wrong_magic(self):
        target = make_boot(self.root / 'boot.img')
        target.write_bytes(b'WRONG!!!' + target.read_bytes()[8:])
        with self.assertRaises(x.Stop):
            x.validate_boot(target)

    def test_boot_size_limit(self):
        with patch.object(x, 'BOOT_SIZE', 3000), self.assertRaises(x.Stop):
            x.validate_boot(make_boot(self.root / 'boot.img'))

    def test_preferences_preserve_unrelated_data_and_types(self):
        original = '<map><string name="unrelated">keep</string><boolean name="launchOnBoot" value="false" /></map>'
        tree = ET.fromstring(x.update_preferences(original, {'launchOnBoot': True, 'brightness': 180, 'url': 'http://example.invalid/a&b'}))
        self.assertEqual(tree.find("string[@name='unrelated']").text, 'keep')
        self.assertEqual(len(tree.findall("boolean[@name='launchOnBoot']")), 1)
        self.assertEqual(tree.find("boolean[@name='launchOnBoot']").get('value'), 'true')
        self.assertEqual(tree.find("int[@name='brightness']").get('value'), '180')
        self.assertEqual(tree.find("string[@name='url']").text, 'http://example.invalid/a&b')

    def test_preferences_new_map(self):
        self.assertEqual(ET.fromstring(x.update_preferences('', {'liteMode': True})).tag, 'map')

    def test_preferences_refuse_non_map(self):
        with self.assertRaises(x.Stop):
            x.update_preferences('<other/>', {'test': True})

    def test_owner_exact_factory_template(self):
        owner = '<root><device-owner package="cloud.shelly.stargate"/><device-owner-context userId="0"/></root>'
        admins = '<admins><admin name="cloud.shelly.stargate/Receiver"/></admins>'
        x.owner_templates_valid(owner, admins)
        for invalid in [owner.replace('cloud.shelly.stargate', 'another.owner'), owner.replace('userId="0"', 'userId="10"'),
                        owner.replace('</root>', '<extra/></root>')]:
            with self.subTest(value=invalid), self.assertRaises(x.Stop):
                x.owner_templates_valid(invalid, admins)
        with self.assertRaises(x.Stop):
            x.owner_templates_valid(owner, '<admins><admin name="another.owner/Receiver"/></admins>')


class WireTests(unittest.TestCase):
    def test_partial_socket_reads(self):
        sock = Mock()
        sock.recv.side_effect = [b'a', b'bc', b'd']
        self.assertEqual(x.recvn(sock, 4), b'abcd')

    def test_closed_socket_detected(self):
        sock = Mock()
        sock.recv.side_effect = [b'a', b'']
        with self.assertRaises(EOFError):
            x.recvn(sock, 2)

    def test_adb_failure_is_not_success(self):
        sock = Mock()
        sock.recv.side_effect = [b'FAIL', b'0006', b'denied']
        with self.assertRaisesRegex(x.Stop, 'denied'):
            x.request(sock, 'host:devices-l')

    def test_push_cannot_target_system_directly(self):
        with self.assertRaises(x.Stop):
            x.ADB(SERIAL).push(Path('not-used'), '/system/app/anything.apk')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(x, 'ROOT', Path(self.tmp.name))
        self.root_patch.start()
        self.args = argparse.Namespace(serial=SERIAL, fastboot='fastboot', allow_no_stock_backup=True,
                                       kiosk=False, dashboard=None, fully_apk=None, remove_stock=False, block_updates=False)
        self.tool = x.Toolkit(self.args)

    def tearDown(self):
        self.root_patch.stop()
        self.tmp.cleanup()

    def prepare_candidate(self):
        candidate = make_boot(self.tool.folder / 'candidate.img')
        self.tool.state.update(prepared=True, candidate=candidate.name, candidate_sha256=x.sha(candidate))
        self.tool.adb = Mock()
        self.tool.adb.host.return_value = ''  # Already in bootloader; no Android command.
        self.tool.fastboot_identity = Mock()
        self.tool.fastboot = Mock(side_effect=lambda *args, **kwargs: "Writing 'boot' OKAY" if args[0] == 'flash' else 'OKAY')
        return candidate

    def test_flash_only_boot_with_confirmation_and_identity_checks(self):
        candidate = self.prepare_candidate()
        with patch.object(x, 'confirmed') as confirm:
            self.tool.flash()
        confirm.assert_called_once_with('FLASH-BOOT-ACCEPT-DATA-LOSS', SERIAL)
        self.assertEqual(self.tool.fastboot_identity.call_count, 2)
        commands = [call.args for call in self.tool.fastboot.call_args_list]
        self.assertEqual(commands, [('flashing', 'unlock'), ('flash', 'boot', str(candidate)), ('reboot',)])
        self.assertTrue(self.tool.state['flashed'])

    def test_existing_attempt_refuses_reflash(self):
        self.prepare_candidate()
        self.tool.state['flash_attempted'] = True
        with self.assertRaises(x.Stop):
            self.tool.flash()
        self.tool.fastboot.assert_not_called()

    def test_no_stock_backup_ack_is_required(self):
        self.prepare_candidate()
        self.args.allow_no_stock_backup = False
        with self.assertRaises(x.Stop):
            self.tool.flash()
        self.tool.fastboot.assert_not_called()

    def test_candidate_tampering_stops_before_flash(self):
        candidate = self.prepare_candidate()
        candidate.write_bytes(candidate.read_bytes()[:-1] + b'!')
        with self.assertRaises(x.Stop):
            self.tool.flash()
        self.tool.fastboot.assert_not_called()

    def test_ambiguous_flash_marks_attempt_and_does_not_reboot(self):
        self.prepare_candidate()
        self.tool.fastboot.side_effect = lambda *args, **kwargs: 'ambiguous' if args[0] == 'flash' else 'OKAY'
        with patch.object(x, 'confirmed'), self.assertRaises(x.Stop):
            self.tool.flash()
        self.assertTrue(self.tool.state['flash_attempted'])
        self.assertNotIn(('reboot',), [call.args for call in self.tool.fastboot.call_args_list])

    def test_failed_unlock_never_flashes(self):
        self.prepare_candidate()
        self.tool.fastboot.side_effect = x.Stop('unlock rejected')
        with patch.object(x, 'confirmed'), self.assertRaises(x.Stop):
            self.tool.flash()
        self.assertEqual([call.args for call in self.tool.fastboot.call_args_list], [('flashing', 'unlock')])

    def test_fastboot_wrong_product_rejected(self):
        self.tool.fastboot = Mock(side_effect=['serialno: ' + SERIAL, 'product: another_board'])
        with self.assertRaises(x.Stop):
            self.tool.fastboot_identity()

    def test_cached_artifact_corruption_never_uses_network(self):
        directory = Path(self.tmp.name) / '.local/downloads'
        directory.mkdir()
        (directory / x.ARTIFACTS['magisk'][0]).write_bytes(b'wrong')
        with patch('urllib.request.urlopen') as network, self.assertRaises(x.Stop):
            self.tool.download('magisk')
        network.assert_not_called()

    def test_resume_staged_setup_does_not_reflash(self):
        self.tool.state.update(module_staged=True, setup_started=True, prepared=True, flash_attempted=True)
        self.tool.wait_boot, self.tool.finish, self.tool.flash = Mock(), Mock(), Mock()
        self.tool.wizard()
        self.tool.finish.assert_called_once()
        self.tool.flash.assert_not_called()

    def test_interrupted_partial_setup_is_not_assumed_complete(self):
        self.tool.state['setup_started'] = True
        self.tool.flash = Mock()
        with self.assertRaises(x.Stop):
            self.tool.wizard()
        self.tool.flash.assert_not_called()

    def test_completed_wizard_only_verifies(self):
        self.tool.state.update(module_staged=True, complete=True)
        self.tool.wait_boot, self.tool.verify, self.tool.flash = Mock(), Mock(), Mock()
        self.tool.wizard()
        self.tool.verify.assert_called_once()
        self.tool.flash.assert_not_called()

    def test_state_bound_to_device(self):
        self.tool.state['serial'] = 'ANOTHERUSB'
        self.tool.save()
        with self.assertRaises(x.Stop):
            x.Toolkit(self.args)

    def test_wait_boot_rejects_old_completed_boot_until_id_changes(self):
        self.tool.adb = Mock()
        self.tool.adb.shell.side_effect = [
            {'out': '1\n'}, {'out': 'old-boot\n'},
            {'out': '1\n'}, {'out': 'new-boot\n'}]
        with patch.object(x.time, 'sleep') as sleep:
            self.tool.wait_boot(previous='old-boot')
        self.assertEqual(self.tool.adb.shell.call_count, 4)
        sleep.assert_called_once_with(2)

    def test_kiosk_verification_wait_does_not_start_apps(self):
        self.tool.adb = Mock()
        self.tool.adb.shell.side_effect = [
            {'out': 'FallbackHome'}, {'out': ''},
            {'out': 'de.ozerov.fully/.FullyActivity'}, {'out': 'ServiceRecord{test}'}]
        with patch.object(x.time, 'sleep'):
            self.tool.wait_kiosk()
        self.assertTrue(all(call.args[0].startswith('dumpsys ') for call in self.tool.adb.shell.call_args_list))

    def test_confirmation_requires_interactive_stdin(self):
        with patch.object(x.sys.stdin, 'isatty', return_value=False), patch('builtins.input') as prompt, self.assertRaises(x.Stop):
            x.confirmed('FLASH', SERIAL)
        prompt.assert_not_called()

    def test_confirmation_refuses_wrong_serial(self):
        with patch.object(x.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value='FLASH ANOTHERUSB'), self.assertRaises(x.Stop):
            x.confirmed('FLASH', SERIAL)


if __name__ == '__main__':
    unittest.main()
