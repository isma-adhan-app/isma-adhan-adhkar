#!/usr/bin/env python3
"""Local syntax linter for build/installer.iss.

iscc only runs on Windows (CI), so installer-script typos used to burn a
full CI run to surface. This catches the classes of errors we actually hit:
  - Pascal-style { } comments outside [Code]
  - unknown [Setup] directives
  - invalid Type values in [UninstallDelete] / [Files]
  - unknown Flags in [Run] / [Icons] / [Files]
  - malformed "Key: value" parameter lines
Run before pushing: python tools/check_iss.py  (exit 1 on any error)
"""
import re
import sys

PATH = 'build/installer.iss'

KNOWN_SECTIONS = {
    'Setup', 'Languages', 'Files', 'Dirs', 'Icons', 'Run', 'UninstallRun',
    'UninstallDelete', 'Registry', 'Code', 'Messages', 'Types', 'Components',
    'Tasks', 'CustomMessages', 'InstallDelete', 'INI', 'ThirdParty',
}

SETUP_DIRECTIVES = {
    'AppName', 'AppVerName', 'AppVersion', 'AppPublisher', 'AppCopyright',
    'DefaultDirName', 'DefaultGroupName', 'OutputDir', 'OutputBaseFilename',
    'Compression', 'SolidCompression', 'WizardStyle', 'PrivilegesRequired',
    'PrivilegesRequiredOverridesAllowed', 'SetupIconFile',
    'UninstallDisplayIcon', 'UninstallDisplayName', 'CloseApplications',
    'CloseApplicationsFilter', 'RestartApplications', 'AppMutex', 'AppId',
    'VersionInfoVersion', 'VersionInfoCompany', 'VersionInfoDescription',
    'VersionInfoProductName', 'VersionInfoProductVersion',
    'VersionInfoCopyright', 'VersionInfoTextVersion', 'MinVersion',
    'ArchitecturesAllowed', 'ArchitecturesInstallIn64BitMode',
    'DisableDirPage', 'DisableProgramGroupPage', 'DirExistsWarning',
    'LicenseFile', 'InfoBeforeFile', 'InfoAfterFile', 'SetupLogging',
    'AllowNoIcons', 'CreateUninstallRegKey', 'Uninstallable',
    'UsePreviousAppDir', 'UsePreviousGroup', 'ChangesEnvironment',
    'UpdateUninstallLogAppName', 'WizardResizable', 'ShowUndisplayableLanguages',
}

UNINSTALLDELETE_TYPES = {'files', 'filesandordirs', 'dirifempty'}
INSTALLDELETE_TYPES = UNINSTALLDELETE_TYPES
FILES_FLAGS = {
    'recursesubdirs', 'createallsubdirs', 'ignoreversion', 'overwritereadonly',
    'uninsremovereadonly', 'replacesameversion', 'skipifsourcedoesntexist',
    'confirmoverwrite', 'deleteafterinstall', 'dontcopy', 'external',
    'onlyifdestfileexists', 'promptifolder', 'regserver', 'regtypelib',
    'restartreplace', 'sharedfile', 'sign', 'signonce', 'solidbreak',
    'sortfilesbyextension', 'sortfilesbyname', 'touch', 'uninsnosharedfileprompt',
    'comparetimestamp', '32bit', '64bit', 'allowunsafefiles', 'dontverifychecksum',
    'gacinstall', 'isreadme', 'nocompression', 'noencryption', 'setntfscompression',
    'unsetntfscompression', 'disablenouninstallwarning', 'onlyifdoesntexist',
}
RUN_FLAGS = {
    'postinstall', 'nowait', 'waituntilidle', 'waituntilterminated',
    'skipifsilent', 'skipifnotsilent', 'unchecked', 'runhidden',
    'shellexec', 'runascurrentuser', 'runasoriginaluser', 'hidewizard',
    '32bit', '64bit', 'dontinheritparameters', 'runonceid', 'no32bit', 'no64bit',
}
ICONS_FLAGS = {
    'runminimized', 'runmaximized', 'runhidden', 'closeonexit',
    'useapppaths', 'excludefromshowinnewinstall', 'preventpinning',
    'foldershortcut', 'uninsneveruninstall',
}

errors = []

def err(lineno, msg):
    errors.append('line %d: %s' % (lineno, msg))

def parse_params(lineno, rest, allowed_value_checks):
    """rest is the part after the section-specific leading fields."""
    for chunk in rest.split(';'):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r'^([A-Za-z0-9]+):\s*(.*)$', chunk)
        if not m:
            err(lineno, 'malformed parameter %r (expected "Key: value")' % chunk)
            continue
        key, value = m.group(1), m.group(2).strip()
        check = allowed_value_checks.get(key.lower())
        if check:
            check(lineno, key, value)

def check_enum(lineno, key, value, valid, what):
    for v in value.split():
        if v.lower() not in valid:
            err(lineno, '%s %r is not a valid %s (valid: %s)'
                % (key, v, what, ', '.join(sorted(valid))))

lines = open(PATH, encoding='utf-8-sig').read().splitlines()
section = None
brace_comment_open = False
for i, raw in enumerate(lines, 1):
    line = raw.strip()
    if not line or line.startswith(';'):
        continue
    m = re.match(r'^\[([A-Za-z]+)\]\s*$', line)
    if m:
        section = m.group(1)
        if section not in KNOWN_SECTIONS:
            err(i, 'unknown section [%s]' % section)
        continue
    if line.startswith('#'):
        continue  # ISPP directive
    if section is None:
        continue
    if section == 'Code':
        continue  # Pascal syntax is out of scope for this linter
    if '{' in line or '}' in line.replace('{app}', '').replace('{autopf}', ''):
        # crude: flag braces that are not Inno constants {name}
        leftovers = re.sub(r'\{[A-Za-z0-9_:#\\ ()\-\.\u0621-\u064A]+\}', '', line)
        if '{' in leftovers or '}' in leftovers:
            err(i, 'stray { or } outside [Code] - comments in script sections start with ;')
            continue
    if section == 'Setup':
        m = re.match(r'^([A-Za-z0-9]+)=(.*)$', line)
        if not m:
            err(i, 'malformed [Setup] line (expected Key=value): %r' % line)
            continue
        if m.group(1) not in SETUP_DIRECTIVES:
            err(i, 'unknown [Setup] directive %r' % m.group(1))
        if m.group(1) == 'DirExistsWarning' and m.group(2).strip().lower() not in ('yes', 'no', 'auto'):
            err(i, 'DirExistsWarning must be yes, no or auto')
        continue
    if section == 'Languages':
        continue
    # entry sections: leading "Key: value; ..." parameter lists
    if section in ('UninstallDelete', 'InstallDelete'):
        parse_params(i, line, {
            'type': lambda n, k, v: check_enum(n, k, v, UNINSTALLDELETE_TYPES, 'uninstall-delete Type'),
        })
    elif section == 'Files':
        parse_params(i, line, {
            'flags': lambda n, k, v: check_enum(n, k, v, FILES_FLAGS, 'Files flag'),
        })
    elif section == 'Run' or section == 'UninstallRun':
        parse_params(i, line, {
            'flags': lambda n, k, v: check_enum(n, k, v, RUN_FLAGS, 'Run flag'),
        })
    elif section == 'Icons':
        parse_params(i, line, {
            'flags': lambda n, k, v: check_enum(n, k, v, ICONS_FLAGS, 'Icons flag'),
        })

if errors:
    print('check_iss: %d problem(s) in %s:' % (len(errors), PATH))
    for e in errors:
        print('  ' + e)
    sys.exit(1)
print('check_iss: %s OK' % PATH)
