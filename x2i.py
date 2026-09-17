#!/usr/bin/env python3
"""Experimental Jenna/2.7.4 toolkit. Python 3.10+, standard library only.

Default operation is read-only inspection. Flashing requires a separate, typed
confirmation. The refactored wizard has NOT been tested end-to-end on a fresh
second device. Read README.md and docs/SAFETY.md before using write operations.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
FINGERPRINT = 'Shelly/Jenna/Jenna:11/RD2A.211001.002/vJenna.0a276d5:user/release-keys'
FIRMWARE = '2.7.4-b7b6bc07'
BOOT_SIZE = 0x2800000
VENDOR_BOOT_SHA = '5c9635d64717462a9a595ac5527dd9ade6e23864b6f7e2df735636b685635a81'
FULLY_SHA = '7867b11e830286eb3f9c4521305603f4225f003e49ea27908eb2e18454125368'
ELEVATE = 'me.rapierxbox.shellyelevatev2'
STOCK = 'cloud.shelly.stargate'
MOD = '/data/adb/modules/shelly_x2i_toolkit'
TMP = '/data/local/tmp/shelly-x2i-toolkit'
ARTIFACTS = {
    'vendor': ('JennaUpdateSDIO.zip', 'https://repo.shelly.cloud/firmware/SAWD-3A1XE10EU2/stable/JennaUpdateSDIO.zip',
               'e5e362894448784934b0ddb270ee0bcce8f9fe0ab3b459230384f1208917dd05'),
    'magisk': ('Magisk-v30.7.apk', 'https://github.com/topjohnwu/Magisk/releases/download/v30.7/Magisk-v30.7.apk',
               'e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5'),
    'elevate': ('ShellyElevateV2-3.26170.1325.apk', 'https://github.com/RapierXbox/ShellyElevate/releases/download/v3.26170.1522/ShellyElevateV2-3.26170.1325.apk',
                '9c841ddd1b69df20f8872afe2354b082446cfafcbff77f6f5877a15294522172'),
    'launcher': ('ultra-small-launcher.apk', 'https://blakadder.com/assets/files/ultra-small-launcher.apk',
                 'e5ffe9eab011942556e151cd80e761dd0574d8998ac0ef5717074ddd80abb8d3'),
}
COMPONENTS = ['busybox', 'magisk', 'magiskboot', 'magiskinit', 'magiskpolicy', 'init-ld', 'bootctl',
              'boot_patch.sh', 'util_functions.sh', 'app_functions.sh', 'addon.d.sh', 'stub.apk']


class Stop(RuntimeError):
    pass


def require(condition, message):
    # Safety checks must remain active even with python -O.
    if not condition:
        raise Stop(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def serial_value(value):
    require(bool(re.fullmatch(r'[A-Za-z0-9_-]{4,64}', value)), 'Use a physical USB serial, not an IP/port or shell expression.')
    return value


def dashboard_value(value):
    url = urllib.parse.urlsplit(value)
    require(url.scheme in ('http', 'https') and bool(url.hostname), 'Dashboard must be an http(s) URL.')
    require(not url.username and not url.password and not url.query and not url.fragment,
            'Do not include credentials, tokens, query strings or fragments in the dashboard URL.')
    return value


def confirmed(action, serial):
    phrase = action + ' ' + serial
    require(sys.stdin.isatty(), 'Interactive confirmation required; no unattended --yes mode.')
    require(input('Type exactly "' + phrase + '" to continue: ').strip() == phrase, 'Cancelled; confirmation did not match.')


def recvn(stream, count):
    output = bytearray()
    while len(output) < count:
        part = stream.recv(count - len(output))
        if not part:
            raise EOFError('ADB transport closed')
        output.extend(part)
    return bytes(output)


def request(stream, name):
    payload = name.encode()
    stream.sendall(f'{len(payload):04x}'.encode() + payload)
    status = recvn(stream, 4)
    if status == b'FAIL':
        raise Stop(recvn(stream, int(recvn(stream, 4), 16)).decode(errors='replace'))
    require(status == b'OKAY', 'Unexpected ADB response')


class ADB:
    """Use the current localhost server, avoiding adb 40/41 restart conflicts."""
    def __init__(self, serial):
        self.serial = serial_value(serial)

    def host(self, name):
        with socket.create_connection(('127.0.0.1', 5037), timeout=8) as stream:
            request(stream, name)
            return recvn(stream, int(recvn(stream, 4), 16)).decode()

    def transport(self):
        stream = socket.create_connection(('127.0.0.1', 5037), timeout=10)
        try:
            request(stream, 'host:transport:' + self.serial)
        except Exception:
            stream.close()
            raise
        return stream

    def shell(self, command, timeout=30, check=True):
        with self.transport() as stream:
            stream.settimeout(timeout)
            request(stream, 'shell,v2,raw:' + command)
            out, err = bytearray(), bytearray()
            while True:
                kind, size = struct.unpack('<BI', recvn(stream, 5))
                data = recvn(stream, size)
                if kind == 1:
                    out.extend(data)
                elif kind == 2:
                    err.extend(data)
                elif kind == 3:
                    code = int.from_bytes(data, 'little')
                    result = {'code': code, 'out': out.decode(errors='replace'), 'err': err.decode(errors='replace')}
                    require(not check or code == 0, 'ADB command failed: ' + result['err'][:1000])
                    return result

    def push(self, path, remote):
        require(remote.startswith(TMP + '/'), 'Uploads restricted to toolkit staging directory')
        with self.transport() as stream, Path(path).open('rb') as source:
            stream.settimeout(60)
            request(stream, 'sync:')
            target = (remote + ',33188').encode()  # Regular file, 0644.
            stream.sendall(b'SEND' + struct.pack('<I', len(target)) + target)
            while data := source.read(65536):
                stream.sendall(b'DATA' + struct.pack('<I', len(data)) + data)
            stream.sendall(b'DONE' + struct.pack('<I', int(time.time())))
            kind, size = struct.unpack('<4sI', recvn(stream, 8))
            if kind == b'FAIL':
                raise Stop(recvn(stream, size).decode(errors='replace'))
            require(kind == b'OKAY', 'ADB push failed')

    def capture(self, command, destination):
        destination = Path(destination)
        require(not destination.exists(), 'Refusing to replace a backup/capture: ' + str(destination))
        temporary = destination.with_name(destination.name + '.partial')
        with self.transport() as stream, temporary.open('xb') as output:
            stream.settimeout(60)
            request(stream, 'exec:' + command)
            while data := stream.recv(1024 * 1024):
                output.write(data)
        temporary.rename(destination)

    def reboot(self, target=''):
        require(target in ('', 'bootloader'), 'Unsupported reboot destination')
        with self.transport() as stream:
            request(stream, 'reboot:' + target)
            # Request acknowledgement is enough. Never wait for a rebooting peer.


def parse_first_version(package_dump):
    match = re.search(r'^\s*versionName=(\S+)', package_dump, re.M)
    require(match is not None, 'Could not read installed Shelly version')
    return match.group(1)


def check_identity(info, serial):
    expected = {'ro.serialno': serial, 'ro.product.device': 'Jenna', 'ro.board.platform': 'rk3326',
                'ro.build.version.sdk': '30', 'ro.product.cpu.abi': 'arm64-v8a', 'ro.build.fingerprint': FINGERPRINT}
    differences = {k: {'expected': v, 'actual': info.get(k)} for k, v in expected.items() if info.get(k) != v}
    require(not differences, 'Untested hardware/Android build; refusing writes: ' + json.dumps(differences))
    require(info.get('shelly_version') == FIRMWARE, 'Untested Shelly build; only ' + FIRMWARE + ' is currently allowed')


def validate_boot(path):
    require(2048 < Path(path).stat().st_size <= BOOT_SIZE, 'Boot image size outside the tested 40 MiB partition')
    with Path(path).open('rb') as stream:
        header = stream.read(48)
    require(header[:8] == b'ANDROID!', 'Not a legacy Android boot image')
    require(struct.unpack_from('<I', header, 40)[0] == 2, 'Only the tested boot header v2 is supported')


def owner_templates_valid(owner, admins):
    owner_root, admin_root = ET.fromstring(owner), ET.fromstring(admins)
    require(owner_root.tag == 'root' and len(owner_root) == 2, 'Unrecognised owner template; do not overwrite other policy')
    entry = owner_root.find('device-owner')
    require(entry is not None and entry.get('package') == STOCK, 'Owner is not the factory Shelly app')
    context = owner_root.find('device-owner-context')
    require(context is not None and context.get('userId') == '0', 'Unexpected owner user')
    require(admin_root.tag == 'admins' and len(admin_root) == 1, 'Unexpected admin template')
    require(admin_root[0].get('name', '').startswith(STOCK + '/'), 'Admin is not the factory Shelly app')


def update_preferences(original, changes):
    tree = ET.fromstring(original) if original else ET.Element('map')
    require(tree.tag == 'map', 'Not an Android SharedPreferences map')
    for key, value in changes.items():
        for old in list(tree):
            if old.get('name') == key:
                tree.remove(old)
        if isinstance(value, bool):
            ET.SubElement(tree, 'boolean', name=key, value=str(value).lower())
        elif isinstance(value, int):
            ET.SubElement(tree, 'int', name=key, value=str(value))
        else:
            ET.SubElement(tree, 'string', name=key).text = value
    return ET.tostring(tree, encoding='utf-8', xml_declaration=True)


def is_privileged(package_dump):
    flags = re.search(r'^\s*flags=\[([^\]]*)\]', package_dump, re.M)
    private = re.search(r'^\s*privateFlags=\[([^\]]*)\]', package_dump, re.M)
    return bool(flags and private and 'SYSTEM' in flags.group(1).split() and 'PRIVILEGED' in private.group(1).split())


class Toolkit:
    def __init__(self, args):
        self.args, self.adb = args, ADB(args.serial)
        self.folder = ROOT / '.local' / hashlib.sha256(args.serial.encode()).hexdigest()[:16]
        self.folder.mkdir(parents=True, exist_ok=True)
        self.state_path = self.folder / 'state.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {'serial': args.serial}
        require(self.state.get('serial') == args.serial, 'State belongs to a different device')

    def save(self):
        temporary = self.state_path.with_suffix('.new')
        temporary.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        os.replace(temporary, self.state_path)

    def log(self, name, data):
        path = self.folder / (name + '-' + time.strftime('%Y%m%dT%H%M%S') + '.json')
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def inspect(self, strict=False):
        listing = self.adb.host('host:devices-l')
        require(any(row.split()[:2] == [self.args.serial, 'device'] for row in listing.splitlines()), 'Selected USB device is not online/authorized')
        props = ['ro.serialno', 'ro.product.device', 'ro.board.platform', 'ro.build.version.sdk',
                 'ro.product.cpu.abi', 'ro.build.fingerprint', 'ro.build.version.security_patch', 'sys.boot_completed']
        values = self.adb.shell('; '.join('getprop ' + key for key in props))['out'].splitlines()
        require(len(values) == len(props), 'Unexpected property response')
        info = dict(zip(props, values))
        info['shelly_version'] = parse_first_version(self.adb.shell('dumpsys package ' + STOCK)['out'])
        info['kernel'] = self.adb.shell('cat /proc/version')['out'].strip()
        self.log('inspection', info)
        print(json.dumps(info, indent=2))
        if strict:
            check_identity(info, self.args.serial)
        return info

    def download(self, key):
        name, url, expected = ARTIFACTS[key]
        directory = ROOT / '.local/downloads'
        directory.mkdir(exist_ok=True)
        path = directory / name
        if path.exists():
            require(sha(path) == expected, 'Cached artifact hash mismatch: ' + name)
            return path
        print('Downloading pinned upstream artifact:', name, flush=True)
        partial = path.with_suffix(path.suffix + '.partial')
        require(not partial.exists(), 'Incomplete download exists; inspect/remove this exact partial file before retrying: ' + str(partial))
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'shelly-x2i-root/0.1'}), timeout=45) as response, partial.open('xb') as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                require(total <= 256 * 1024 * 1024, 'Unexpectedly large download')
                output.write(chunk)
        require(sha(partial) == expected, 'Upstream artifact changed! Refusing to use it; do not bypass the hash check.')
        partial.rename(path)
        return path

    def components(self):
        package = self.download('magisk')
        directory = self.folder / 'magisk-components'
        directory.mkdir(exist_ok=True)
        with zipfile.ZipFile(package) as archive:
            for name in COMPONENTS:
                member = 'assets/' + name
                if member not in archive.namelist():
                    member = 'lib/arm64-v8a/lib' + name + '.so'
                (directory / name).write_bytes(archive.read(member))
        return directory

    def install(self, path):
        self.adb.shell('mkdir -p ' + TMP)
        remote = TMP + '/' + path.name
        self.adb.push(path, remote)
        reply = self.adb.shell('pm install -r -g ' + shlex.quote(remote), timeout=90)
        require('Success' in reply['out'], 'Package installation failed: ' + reply['out'])

    def prepare(self):
        self.inspect(strict=True)
        require(not self.state.get('flash_attempted'), 'Flash already attempted. Do not overwrite its evidence; resume with verify/setup.')
        probe = self.root('id', check=False, timeout=10)
        require('uid=0(root)' not in probe['out'], 'Already rooted: use setup/verify, not another boot flash')
        confirmed('PREPARE', self.args.serial)
        vendor, manager = self.download('vendor'), self.download('magisk')
        parts = self.components()
        boot = self.folder / 'vendor-boot.img'
        with zipfile.ZipFile(vendor) as archive:
            boot.write_bytes(archive.read('boot.img'))
        require(sha(boot) == VENDOR_BOOT_SHA, 'Vendor boot member hash mismatch')
        validate_boot(boot)
        self.install(manager)
        self.adb.shell('mkdir -p ' + TMP + '/patch')
        for path in list(parts.iterdir()) + [boot]:
            self.adb.push(path, TMP + '/patch/' + path.name)
        patch = self.adb.shell('cd ' + TMP + '/patch && BOOTMODE=true KEEPVERITY=true KEEPFORCEENCRYPT=true PATCHVBMETAFLAG=false sh ./boot_patch.sh vendor-boot.img', timeout=120)
        self.log('patch', patch)
        candidate = self.folder / ('candidate-' + str(time.time_ns()) + '.img')
        self.adb.capture('cat ' + TMP + '/patch/new-boot.img', candidate)
        validate_boot(candidate)
        self.state.update(prepared=True, candidate=candidate.name, candidate_sha256=sha(candidate), fingerprint=FINGERPRINT, firmware=FIRMWARE)
        self.save()
        print('Patched on the selected device. No partition flashed. Candidate:', candidate)

    def fastboot(self, *args, timeout=15):
        result = subprocess.run([self.args.fastboot, '-s', self.args.serial, *args], capture_output=True, timeout=timeout)
        text = (result.stdout + result.stderr).decode(errors='replace')
        self.log('fastboot', {'args': args, 'code': result.returncode, 'output': text})
        require(result.returncode == 0, 'Fastboot command failed; stop and inspect local logs: ' + text[:1200])
        return text

    def fastboot_identity(self):
        require('serialno: ' + self.args.serial in self.fastboot('getvar', 'serialno'), 'Fastboot serial mismatch')
        require('product: evb_px30' in self.fastboot('getvar', 'product'), 'Unexpected fastboot product')
        text = self.fastboot('getvar', 'partition-size:boot')
        match = re.search(r'partition-size:boot:\s*(0x[0-9a-fA-F]+)', text)
        require(match is not None and int(match.group(1), 16) == BOOT_SIZE, 'Unexpected boot partition size')
        require('has-slot:boot: no' in self.fastboot('getvar', 'has-slot:boot'), 'Unexpected slot layout')

    def flash(self):
        require(self.state.get('prepared'), 'Prepare on this same device first')
        require(not self.state.get('flash_attempted'), 'Flash already attempted. Refusing an automatic reflash; inspect logs and use verify/setup.')
        require(self.args.allow_no_stock_backup, 'Original boot cannot be read on the tested production build. Read SAFETY.md and explicitly pass --allow-no-stock-backup to accept that risk.')
        candidate = self.folder / self.state['candidate']
        require(candidate.parent.resolve() == self.folder.resolve(), 'Invalid candidate path')
        validate_boot(candidate)
        require(sha(candidate) == self.state['candidate_sha256'], 'Candidate changed after preparation')
        print('DANGER: unlock may erase data on other units. This replaces ONLY boot with an OLDER kernel.\nNo exact original boot backup or guaranteed unbrick route is available. A brick is possible.')
        confirmed('FLASH-BOOT-ACCEPT-DATA-LOSS', self.args.serial)
        # Support the deliberate pause needed to bind a bootloader USB driver.
        listing = self.adb.host('host:devices-l')
        if any(row.split()[:2] == [self.args.serial, 'device'] for row in listing.splitlines()):
            self.inspect(strict=True)
            require('uid=0(root)' not in self.root('id', check=False, timeout=10)['out'], 'Already rooted; refusing another boot flash')
            self.adb.reboot('bootloader')
            time.sleep(5)
        self.fastboot_identity()
        self.fastboot('flashing', 'unlock')
        self.fastboot_identity()
        self.state['flash_attempted'] = True
        self.save()  # Persist BEFORE issuing the only partition-write command.
        text = self.fastboot('flash', 'boot', str(candidate), timeout=90)
        require("Writing 'boot'" in text and 'OKAY' in text, 'Boot write response was ambiguous; do not reflash automatically')
        self.state['flashed'] = True
        self.save()
        self.fastboot('reboot')
        print('Boot write completed. If it does not reach Android, power-cycle the complete panel.\nDo not issue getvar all. Do not repeatedly flash. Resume with verify, then setup.')

    def root(self, command, **kwargs):
        return self.adb.shell('/debug_ramdisk/su -c ' + shlex.quote(command), **kwargs)

    def wait_boot(self):
        # Bounded individual checks; progress output instead of silent indefinite waits.
        for attempt in range(45):
            try:
                if self.adb.shell('getprop sys.boot_completed', timeout=4)['out'].strip() == '1':
                    return
            except (OSError, EOFError, Stop):
                pass
            if attempt % 10 == 0:
                print('Waiting for Android boot; USB driver/power reconnection may be needed...', flush=True)
            time.sleep(2)
        raise Stop('Android not ready. Reconnect/cold-power-cycle if appropriate, then resume; do not reflash.')

    def backup(self, remote, name):
        path = self.folder / name
        if not path.exists():
            self.root('test -f ' + shlex.quote(remote))
            self.adb.capture('/debug_ramdisk/su -c ' + shlex.quote('cat ' + shlex.quote(remote)), path)
        return path

    def upload_root(self, content, remote, mode='644'):
        require(remote.startswith(MOD + '/') or remote.startswith('/data/adb/magisk/'), 'Unexpected root upload target')
        local = self.folder / 'upload.tmp'
        local.write_bytes(content)
        self.adb.push(local, TMP + '/upload.tmp')
        self.root('set -e; mkdir -p ' + shlex.quote(remote.rsplit('/', 1)[0]) + '; cp ' + TMP + '/upload.tmp ' + shlex.quote(remote) + '; chown 0:0 ' + shlex.quote(remote) + '; chmod ' + mode + ' ' + shlex.quote(remote) + '; chcon u:object_r:system_file:s0 ' + shlex.quote(remote))

    def prefs(self, package, filename, changes):
        dump = self.adb.shell('dumpsys package ' + package)['out']
        match = re.search(r'^\s*userId=(\d+)', dump, re.M)
        require(match is not None, 'Cannot establish installed app UID')
        uid = match.group(1)
        # Reject shared UID before modifying another app's private preferences.
        owners = self.adb.shell('cmd package list packages --uid ' + uid)['out'].splitlines()
        require(owners == ['package:' + package + ' uid:' + uid], 'Unexpected shared UID')
        remote = '/data/user/0/' + package + '/shared_prefs/' + filename
        self.adb.shell('am force-stop ' + package)
        exists = self.root('test -f ' + remote, check=False)['code'] == 0
        original = self.root('cat ' + remote)['out'] if exists else ''
        before = self.folder / (package + '-preferences-before.xml')
        if exists and not before.exists():
            before.write_text(original, encoding='utf-8')
        local = self.folder / 'preferences.tmp'
        local.write_bytes(update_preferences(original, changes))
        self.adb.push(local, TMP + '/preferences.tmp')
        parent = remote.rsplit('/', 1)[0]
        self.root('set -e; mkdir -p ' + parent + '; chown ' + uid + ':' + uid + ' ' + parent + '; chmod 771 ' + parent + '; cp ' + TMP + '/preferences.tmp ' + remote + '; chown ' + uid + ':' + uid + ' ' + remote + '; chmod 660 ' + remote + '; restorecon -R ' + parent)

    def setup(self):
        self.inspect(strict=True)
        require('uid=0(root)' in self.root('id')['out'], 'Root is not available; approve the Magisk shell prompt if shown')
        require(self.args.kiosk and self.args.dashboard and self.args.fully_apk, 'Setup needs --kiosk, --dashboard and --fully-apk. MQTT/HA login remain manual.')
        require(not self.state.get('setup_started'), 'Setup already started; use finish to resume after reboot, or inspect logs. Do not overwrite the module blindly.')
        fully = Path(self.args.fully_apk).resolve()
        require(fully.is_file() and sha(fully) == FULLY_SHA, 'Only the pinned Fully 1.57.1 APK is supported by this preference recipe')
        require(self.root('test ! -e ' + MOD, check=False)['code'] == 0, 'Toolkit module already exists; refusing replacement')
        require(self.root('test ! -e /system/priv-app/ShellyElevateV2', check=False)['code'] == 0, 'Another system-app promotion exists; do not layer modules')
        print('Setup installs signed apps, backs up selected files, grants declared app permissions, and reboots.')
        print('Remove factory ownership/disable stock apps:', self.args.remove_stock, '| Block stock OTA/security updates:', self.args.block_updates)
        confirmed('SETUP', self.args.serial)
        if self.args.remove_stock:
            owner = self.backup('/system/etc/stargate/device_owner_2.xml', 'vendor-owner.xml')
            admins = self.backup('/system/etc/stargate/device_admins.xml', 'vendor-admins.xml')
            owner_templates_valid(owner.read_bytes(), admins.read_bytes())
            current_owner = self.backup('/data/system/device_owner_2.xml', 'current-owner.xml')
            current = ET.fromstring(current_owner.read_bytes()).find('device-owner')
            require(current is not None and current.get('package') == STOCK, 'Current owner is not the expected factory owner; stop')
            self.backup('/data/system/device_admins.xml', 'current-admins.xml')
        if self.args.block_updates:
            self.backup('/system/bin/check_stargate_update.sh', 'stock-updater.sh')
            self.state['old_ota_setting'] = self.adb.shell('settings get global ota_disable_automatic_update')['out'].strip()
        self.log('before-setup', {'home': self.adb.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'),
                                  'policy': self.adb.shell('dumpsys device_policy'), 'disabled': self.adb.shell('pm list packages -d')})
        self.adb.shell('mkdir -p ' + TMP)
        # Complete Magisk's userspace payload; no direct_install or remount.
        parts = self.components()
        existing = self.root('test -f /data/adb/magisk/magisk', check=False)['code'] == 0
        if existing:
            require('30.7' in self.root('/data/adb/magisk/magisk -v')['out'], 'Different installed Magisk version; stop')
        for path in parts.iterdir():
            self.upload_root(path.read_bytes(), '/data/adb/magisk/' + path.name, '755')
        self.root('chmod 700 /data/adb; export MAGISKBIN=/data/adb/magisk MAGISKTMP=/debug_ramdisk; . /data/adb/magisk/app_functions.sh; env_check "30.7" 30700')
        elevate, launcher = self.download('elevate'), self.download('launcher')
        for path in (elevate, launcher, fully):
            self.install(path)
        self.prefs(ELEVATE, 'ShellyElevateV2.xml', {'liteMode': True, 'settingEverShown': True, 'httpServer': True,
                   'screenSaver': False, 'automaticBrightness': False, 'brightness': 180, 'webviewUrl': self.args.dashboard,
                   'voiceAssistantEnabled': False, 'voiceWakeEnabled': False, 'bluetoothProxyEnabled': False,
                   'switchOnSwipe': False, 'powerButtonAutoReboot': False})
        self.prefs('de.ozerov.fully', 'de.ozerov.fully_preferences.xml', {'startURL': self.args.dashboard,
                   'launchOnBoot': True, 'keepScreenOn': True, 'showActionBar': False, 'showStatusBar': False,
                   'showNavigationBar': False, 'kioskMode': False, 'remoteAdmin': False})
        self.state.update(setup_started=True, remove_stock=self.args.remove_stock, block_updates=self.args.block_updates)
        self.save()
        self.upload_root(b'id=shelly_x2i_toolkit\nname=Shelly X2i local-control setup\nversion=0.1\nversionCode=1\nauthor=Local device owner\ndescription=Opt-in systemless app promotion, factory-owner override and stock update guard.\n', MOD + '/module.prop')
        self.upload_root(elevate.read_bytes(), MOD + '/system/priv-app/ShellyElevateV2/ShellyElevateV2.apk')
        if self.args.remove_stock:
            for name in ('device_owner_2.xml', 'device_admins.xml'):
                self.upload_root((ROOT / 'module' / name).read_bytes(), MOD + '/system/etc/stargate/' + name)
            script = (ROOT / 'module/post-fs-data.sh').read_text().replace('@SERIAL@', self.args.serial)
            self.upload_root(script.encode(), MOD + '/post-fs-data.sh', '755')
        if self.args.block_updates:
            self.upload_root((ROOT / 'module/check_stargate_update.sh').read_bytes(), MOD + '/system/bin/check_stargate_update.sh', '755')
            self.adb.shell('settings put global ota_disable_automatic_update 1')
        for package in (ELEVATE, 'de.ozerov.fully'):
            self.adb.shell('appops set ' + package + ' WRITE_SETTINGS allow')
            self.adb.shell('dumpsys deviceidle whitelist +' + package)
            self.adb.shell('am start -W -n ' + package + '/.MainActivity', timeout=60)
        self.root('set -e; chown -R 0:0 ' + MOD + '; find ' + MOD + ' -type d -exec chmod 755 {} \\;; chcon -R u:object_r:system_file:s0 ' + MOD)
        self.state['module_staged'] = True
        self.save()
        self.adb.reboot()
        self.wait_boot()
        self.finish()

    def finish(self):
        require(self.state.get('module_staged'), 'Setup did not finish staging its module; review logs before making further changes')
        self.inspect(strict=True)
        require('uid=0(root)' in self.root('id')['out'], 'Root did not survive')
        package = self.adb.shell('dumpsys package ' + ELEVATE)['out']
        require(is_privileged(package), 'System-app promotion not active')
        if self.state.get('remove_stock'):
            policy = self.adb.shell('dumpsys device_policy')['out']
            require('Device Owner:' not in policy and 'Profile Owner' not in policy, 'Factory owner remains; do not continue')
            for package in (STOCK, 'cloud.shelly.placeholder'):
                self.root('pm disable-user --user 0 ' + package)
                self.root('am force-stop --user 0 ' + package)
            # Finish ordinary Android setup, WITHOUT creating a new device owner.
            self.adb.shell('am force-stop com.android.managedprovisioning')
            if self.adb.shell('settings get global device_provisioned')['out'].strip() != '1':
                self.adb.shell('am start -W -n com.android.provision/.DefaultActivity')
            self.root('cmd package set-home-activity --user 0 l.l/l.l')
        self.adb.shell('am start -W -n de.ozerov.fully/.MainActivity')
        before = self.adb.shell('cat /proc/sys/kernel/random/boot_id')['out'].strip()
        self.state['verification_before_boot_id'] = before
        self.save()
        self.adb.reboot()
        self.wait_boot()
        self.verify()

    def verify(self):
        info = self.inspect(strict=True)
        root = self.root('id; /debug_ramdisk/magisk -v; cat /proc/sys/kernel/random/boot_id')
        require('uid=0(root)' in root['out'], 'Root not verified')
        require(info['sys.boot_completed'] == '1', 'Android has not finished booting')
        checks = {'root': root, 'policy': self.adb.shell('dumpsys device_policy'),
                  'disabled': self.adb.shell('pm list packages -d'),
                  'home': self.adb.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'),
                  'foreground': self.adb.shell('dumpsys activity activities | grep mResumedActivity', check=False),
                  'services': self.adb.shell('dumpsys activity services ' + ELEVATE),
                  'vendor_crash_log': self.root('logcat -d -b crash -t 100')}
        self.log('verification', checks)
        if self.state.get('module_staged'):
            pkg = self.adb.shell('dumpsys package ' + ELEVATE)['out']
            require(is_privileged(pkg), 'Privileged system app missing')
            require('de.ozerov.fully/.FullyActivity' in checks['foreground']['out'], 'Fully is not foreground; inspect the panel, do not declare startup success')
            require('ServiceRecord{' in checks['services']['out'], 'Elevate service not running')
            if self.state.get('remove_stock'):
                require('Device Owner:' not in checks['policy']['out'], 'Factory device owner returned')
                require(all('package:' + pkg in checks['disabled']['out'] for pkg in (STOCK, 'cloud.shelly.placeholder')), 'Stock app not disabled')
                require('l.l/l.l' in checks['home']['out'], 'Unexpected HOME launcher')
            if self.state.get('block_updates'):
                guard = self.root('cat /system/bin/check_stargate_update.sh')['out']
                require('ShellyRootGuard' in guard, 'Firmware guard not mounted')
            previous = self.state.get('verification_before_boot_id')
            current = self.adb.shell('cat /proc/sys/kernel/random/boot_id')['out'].strip()
            require(previous is not None and previous != current, 'No new boot verified')
            self.state['complete'] = True
        self.state['root_verified'] = True
        self.save()
        print('Root verified.' + (' Kiosk startup and requested policy changes verified after reboot.' if self.state.get('complete') else ''))
        if 'Fatal signal' in checks['vendor_crash_log']['out']:
            print('WARNING: vendor crash log is non-empty; review private verification log (known memtrack issue).')
        print('Logs/backups are PRIVATE:', self.folder)

    def wizard(self):
        if self.state.get('module_staged'):
            self.wait_boot()
            if not self.state.get('complete'):
                self.finish()
            else:
                self.verify()
            return
        require(not self.state.get('setup_started'), 'Setup staging was interrupted; inspect local logs rather than assuming the module is complete')
        if not self.state.get('prepared'):
            self.prepare()
        if not self.state.get('flash_attempted'):
            self.flash()
        self.wait_boot()
        self.verify()
        if self.args.kiosk and not self.state.get('setup_started'):
            self.setup()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', nargs='?', default='inspect', choices=['inspect', 'prepare', 'flash', 'verify', 'setup', 'finish', 'wizard'])
    p.add_argument('--serial', required=True, help='Physical USB serial (never an IP address)')
    p.add_argument('--fastboot', default='fastboot', help='Path to official platform-tools fastboot')
    p.add_argument('--allow-no-stock-backup', action='store_true', help='Explicitly accept the lack of an exact original boot backup')
    p.add_argument('--kiosk', action='store_true', help='Install/promote Elevate and configure Fully (manual MQTT/HA sign-in)')
    p.add_argument('--fully-apk', help='Locally downloaded official Fully Kiosk 1.57.1 APK')
    p.add_argument('--dashboard', help='Your dashboard URL, without credentials/tokens')
    p.add_argument('--remove-stock', action='store_true', help='Block factory owner assignment and disable stock Shelly apps')
    p.add_argument('--block-updates', action='store_true', help='Block identified stock firmware updater, INCLUDING security updates')
    return p


def main():
    args = parser().parse_args()
    try:
        serial_value(args.serial)
        if args.dashboard:
            dashboard_value(args.dashboard)
        if args.kiosk:
            require(bool(args.dashboard and args.fully_apk), '--kiosk requires --dashboard and --fully-apk')
        require(not (args.remove_stock or args.block_updates) or args.kiosk, 'Policy changes require the explicit --kiosk setup')
        toolkit = Toolkit(args)
        getattr(toolkit, args.command)()
    except (Stop, OSError, EOFError, ValueError, ET.ParseError, subprocess.TimeoutExpired) as exc:
        print('STOP:', exc, file=sys.stderr)
        print('No automatic retry/reflash. Review .local/ logs and the resume instructions.', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nInterrupted. If flash was in progress, do not blindly retry; inspect device state.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())
