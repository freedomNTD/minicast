# -*- mode: python ; coding: utf-8 -*-
# MiniCast PyInstaller spec

a = Analysis(
    ['minicast.py'],
    pathex=[],
    binaries=[('bin/mpv.exe', 'bin'), ('bin/vulkan-1.dll', 'bin')],
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
    excludes=[],
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
