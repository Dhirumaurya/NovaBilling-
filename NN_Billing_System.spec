# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['NN_Billing_System.py'],
    pathex=[],
    binaries=[],
    datas=[('invoice.jpg', '.'), ('invoice1.jpg', '.'), ('invoice2.jpg', '.'), ('nova.png', '.'), ('company.db', '.'), ('logo2.jpg', '.')],
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
    name='NN_Billing_System',
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
    version='version.txt',
    icon=['logo.ico'],
)
