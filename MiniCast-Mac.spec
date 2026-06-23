# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the macOS .app bundle.

Built on macOS only (e.g. via GitHub Actions macos-latest). Differences from
the Windows ``MiniCast.spec``:

* Produces an ``.app`` bundle (``COLLECT`` -> ``BUNDLE``) instead of a single
  ``.exe``.
* No bundled ``mpv.exe`` / ``vulkan-1.dll`` — on macOS the user supplies mpv
  via Homebrew (``brew install mpv``) and MiniCast finds it on ``PATH``.
* Uses ``icon.icns`` for the bundle icon and hides the dock icon (this is a
  menu-bar app, just like the Windows build lives in the tray).
"""

import os

block_cipher = None

datas = [
    ('minicast/xml', 'minicast/xml'),
    ('minicast/assets', 'minicast/assets'),
    ('minicast/.version', 'minicast'),
    ('i18n/zh_CN/LC_MESSAGES/minicast.mo', 'i18n/zh_CN/LC_MESSAGES'),
]
# On macOS, bundle the Homebrew mpv binary so users don't need to install it
# themselves (CI copies it to bin/mpv before building). The runtime resolves it
# via Setting.set_mpv_default_path() -> get_base_path('bin/MacOS/mpv'), so the
# binary must land under bin/MacOS/ inside the bundle. Using ``binaries`` lets
# PyInstaller collect mpv's dynamic-library dependencies too.
binaries = []
if os.path.exists('bin/mpv'):
    binaries.append(('bin/mpv', 'bin/MacOS'))

a = Analysis(
    ['minicast.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'rumps',
        'pyperclip',
        'pyobjc',
        'AppKit',
        'Foundation',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MiniCast',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='minicast/assets/icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MiniCast',
)

# Assemble the .app bundle. LSUIElement=1 hides the dock icon so MiniCast
# behaves as a pure menu-bar app.
app = BUNDLE(
    coll,
    name='MiniCast.app',
    icon='minicast/assets/icon.icns',
    bundle_identifier='com.freedomntd.minicast',
    info_plist={
        'CFBundleName': 'MiniCast',
        'CFBundleDisplayName': 'MiniCast',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,            # menu-bar app: no dock icon
        'LSMinimumSystemVersion': '10.13',
        'NSHighResolutionCapable': True,
        'NSMicrophoneUsageDescription': 'MiniCast plays received media; microphone access is not used.',
    },
)
