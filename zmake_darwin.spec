# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['zmake_qt/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[('zmake/data', 'data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tk',
        'PIL.ImageTk',
    ],
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
    name='zmake',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity="MelianMiko",
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
    name='zmake',
)
app = BUNDLE(
    coll,
    name='zmake.app',
    icon="assets/logo.png",
    bundle_identifier=None,
    info_plist={
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeIconFile': 'Document',
                'CFBundleTypeName': 'Document',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeOSTypes': ['****']
            }
        ]
    },
)
