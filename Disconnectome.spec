import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all necessary data and binaries
datas = [
    ('themes', 'themes'),
    ('data', 'data'),
    ('logo.png', '.'),      # Cross-platform fallback
]

binaries = []

hiddenimports = [
    'PIL._tkinter_finder',
    'PIL._imagingtk',
    'customtkinter',
    'scipy',
    'scipy.sparse.csgraph._validation',
    'scipy.special.cython_special',
    'nibabel',
    'dipy',
]

# Collect all customtkinter and antspyx data
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('antspyx')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib.tests', 'scipy.tests', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Disconnectome',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.png' if sys.platform != 'win32' else 'logo.ico'
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Disconnectome.app',
        icon='logo.icns',
        bundle_identifier='com.disconnectome.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
