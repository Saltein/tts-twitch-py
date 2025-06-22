# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['A:\\PYTHON_projects\\tts-twitch\\tts-twitch.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\nikit\\miniconda3\\Lib\\site-packages\\irc\\codes.txt', 'irc')],
    hiddenimports=[],
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
    name='tts-twitch',
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
)
