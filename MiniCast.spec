# -*- mode: python ; coding: utf-8 -*-
# MiniCast PyInstaller spec
import os

# Bundle mpv.exe and vulkan-1.dll only when present. CI downloads mpv.exe;
# vulkan-1.dll is an optional system runtime that mpv can fall back from, so
# its absence must not break the build.
binaries = []
for name in ('bin/mpv.exe', 'bin/vulkan-1.dll'):
    if os.path.exists(name):
        binaries.append((name, 'bin'))

a = Analysis(
    ['minicast.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        ('minicast/.version', 'minicast'),
        ('minicast/xml/*', 'minicast/xml'),
        ('minicast/assets/*', 'minicast/assets'),
        ('i18n/zh_CN/LC_MESSAGES/minicast.mo', 'i18n/zh_CN/LC_MESSAGES'),
    ],
    hiddenimports=['psutil', 'pystray._win32', 'win32api', 'win32con'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude libraries that MiniCast never imports but get pulled in via
    # transitive deps (cherrypy -> jaraco.text -> typer -> rich -> pygments)
    # or PyInstaller hooks (numpy). This keeps the exe ~40 MB instead of ~66 MB.
    excludes=[
        'rich', 'typer', 'typer_slim', 'pygments', 'markdown_it', 'mdurl',
        'numpy', 'scipy', 'pandas', 'matplotlib', 'setuptools', 'pip',
        'pytest', 'doctest', 'unittest', 'pydoc',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MiniCast',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['minicast\\assets\\icon.ico'],
)
