# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

pyqt5_datas, pyqt5_binaries, pyqt5_hiddenimports = collect_all("PyQt5")
mysql_hiddenimports = collect_submodules("mysql")
mysql_connector_hiddenimports = collect_submodules("mysql.connector")

hiddenimports = [
    "dotenv",
    *pyqt5_hiddenimports,
    *mysql_hiddenimports,
    *mysql_connector_hiddenimports,
]

datas = [
    ("app/assets", "assets"),
    ("app/storage", "storage"),
    *pyqt5_datas,
]

binaries = [
    *pyqt5_binaries,
]

a = Analysis(
    ["aractakip.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    name="AracTakip",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AracTakip",
)
