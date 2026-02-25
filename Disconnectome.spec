# -*- mode: python ; coding: utf-8 -*-
"""
Cross-Platform PyInstaller Spec File for Disconnectome
Produces two executables in a single COLLECT:
  - Disconnectome      (GUI, console=False)
  - disconnectome-cli  (CLI, console=True)

Works on macOS, Windows, and Linux
"""

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# Get the project root directory
project_root = os.path.abspath(os.getcwd())

# ============================================================================
# PLATFORM DETECTION
# ============================================================================
IS_MACOS = sys.platform == 'darwin'
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')

print(f"\n{'='*80}")
print(f"Building for: {sys.platform}")
print(f"Python version: {sys.version}")
print(f"{'='*80}\n")

# ============================================================================
# DATA FILES - Platform agnostic
# ============================================================================
datas = [
    ('themes/*.json', 'themes'),
    ('app_icon.png', '.'),
]

# Only include necessary template files, not entire data directory
if os.path.exists('data/template'):
    print("WARNING: data/template directory found but NOT included in build")
    print("         Use data download system for production builds")
    # Uncomment next line ONLY for testing with small datasets:
    # datas.append(('data/template', 'data/template'))


# WARNING: Exclude large controls directory by default
if os.path.exists('data/controls'):
    print("WARNING: data/controls directory found but NOT included in build")
    print("         Use data download system for production builds")
    # Uncomment next line ONLY for testing with small datasets:
    # datas.append(('data/controls', 'data/controls'))

# ============================================================================
# BINARIES - Platform specific
# ============================================================================
binaries = []

# macOS specific binaries (if needed)
if IS_MACOS:
    # Usually not needed - Tkinter is part of Python on macOS
    pass

# Windows specific binaries (if needed)
elif IS_WINDOWS:
    # Add Windows-specific DLLs if needed
    pass

# Linux specific binaries (if needed)
elif IS_LINUX:
    # Add Linux-specific .so files if needed
    pass

# ============================================================================
# HIDDEN IMPORTS
# ============================================================================
hiddenimports = [
    # Click (required by CLI)
    'click',
    'click.core',
    'click.decorators',
    'click.exceptions',
    'click.formatting',
    'click.termui',
    'click.types',
    'click.utils',

    # Image / GUI
    'PIL._tkinter_finder',
    'PIL._imagingtk',
    'customtkinter',

    # Science stack
    'scipy',
    'scipy.sparse.csgraph._validation',
    'scipy.special.cython_special',
    'nibabel',
    'dipy',
    'numpy',
    'matplotlib',
    'skimage',
    'ants',
    'antspyx',

    # jaraco (required by setuptools / pkg_resources)
    'jaraco',
    'jaraco.text',
    'jaraco.functools',
    'jaraco.context',
    'jaraco.collections',
    'jaraco.classes',

    # jaraco dependencies
    'importlib_metadata',
    'importlib_resources',
    'zipp',
    'more_itertools',

    # pkg_resources
    'pkg_resources',
    'pkg_resources.py2_warn',
]

# Collect submodules for problematic packages
hiddenimports += collect_submodules('scipy.sparse')
hiddenimports += collect_submodules('scipy.special')
hiddenimports += collect_submodules('skimage')

# ✅ FIX: Collect jaraco submodules
print("Collecting jaraco submodules...")
try:
    hiddenimports += collect_submodules('jaraco')
except Exception as e:
    print(f"Warning: Could not collect jaraco submodules: {e}")

# Platform-specific hidden imports
if IS_WINDOWS:
    hiddenimports += [
        'win32com',
        'win32com.client',
    ]

# ============================================================================
# COLLECT PACKAGE DATA
# ============================================================================

# CustomTkinter - essential for all platforms
try:
    tmp_ret = collect_all('customtkinter')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
    print(f"[ok] Collected CustomTkinter: {len(tmp_ret[0])} data files, {len(tmp_ret[1])} binaries")
except Exception as e:
    print(f"[!] Warning: Could not collect customtkinter: {e}")

# ✅ FIX: Collect ALL jaraco packages completely
try:
    print("Collecting jaraco packages (complete)...")

    # Collect everything from jaraco namespace
    jaraco_ret = collect_all('jaraco')
    datas += jaraco_ret[0]
    binaries += jaraco_ret[1]
    hiddenimports += jaraco_ret[2]

    # Specifically ensure jaraco.text is complete
    jaraco_text_ret = collect_all('jaraco.text')
    datas += jaraco_text_ret[0]
    binaries += jaraco_text_ret[1]
    hiddenimports += jaraco_text_ret[2]

    print(f"[ok] Collected jaraco: {len(jaraco_ret[0])} data files")
    print(f"[ok] Collected jaraco.text: {len(jaraco_text_ret[0])} data files")
except Exception as e:
    print(f"[!]  Warning: Could not collect jaraco packages: {e}")

# ANTsPyx - can be large, collect selectively
try:
    ants_data = collect_data_files('antspyx', include_py_files=False)
    # Filter out large files (>50MB)
    ants_data_filtered = [
        (src, dst) for src, dst in ants_data
        if os.path.exists(src) and os.path.getsize(src) < 50 * 1024 * 1024
    ]
    datas += ants_data_filtered
    print(f"[ok] Collected ANTsPyx: {len(ants_data_filtered)} data files (filtered)")

    # Collect ANTsPyx binaries
    tmp_ret = collect_all('antspyx')
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception as e:
    print(f"[!] Warning: Could not collect antspyx: {e}")

# ============================================================================
# EXCLUDES - Remove unnecessary modules
# ============================================================================
excludes = [
    'matplotlib.tests',
    'scipy.tests',
    'pytest',
    'IPython',
    'jupyter',
    'notebook',
    'pandas.tests',
    'numpy.tests',
    'setuptools',
    'distutils',
    'pkg_resources',
]

# ============================================================================
# ANALYSIS — GUI (app.py)
# ============================================================================
a = Analysis(
    ['app.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# ANALYSIS — CLI (cli.py)
# ============================================================================
a_cli = Analysis(
    ['cli.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# REMOVE DUPLICATES AND LARGE FILES
# ============================================================================
def dedup_datas(analysis):
    seen = set()
    analysis.datas = [x for x in analysis.datas if not (x[0] in seen or seen.add(x[0]))]

def dedup_binaries(analysis):
    seen = set()
    analysis.binaries = [x for x in analysis.binaries if not (x[0] in seen or seen.add(x[0]))]

for _a in (a_gui, a_cli):
    dedup_datas(_a)
    dedup_binaries(_a)

# Log large files
print("\n" + "="*80)
print("LARGE FILES (>10 MB) BEING INCLUDED IN GUI ANALYSIS:")
print("="*80)
large_files_found = False
for dest, src, typ in a_gui.datas:
    if os.path.exists(src):
        size_mb = os.path.getsize(src) / (1024 * 1024)
        if size_mb > 10:
            print(f"  {size_mb:.1f} MB - {dest}")
            large_files_found = True
if not large_files_found:
    print("  (None found - good!)")

# ============================================================================
# PYZ (Python Archive)
# ============================================================================
pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)
pyz_cli = PYZ(a_cli.pure, a_cli.zipped_data, cipher=block_cipher)

# ============================================================================
# PLATFORM-SPECIFIC BUILD CONFIGURATION
# ============================================================================

if IS_MACOS:
    # ========================================================================
    # macOS BUILD
    # ========================================================================
    print("\n" + "="*80)
    print("CONFIGURING macOS BUILD")
    print("="*80)

    exe_gui = EXE(
        pyz_gui,
        a_gui.scripts,
        [],
        exclude_binaries=True,
        name='Disconnectome',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,          # GUI — no console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.icns' if os.path.exists('icon.icns') else 'app_icon.png',
    )

    exe_cli = EXE(
        pyz_cli,
        a_cli.scripts,
        [],
        exclude_binaries=True,
        name='disconnectome-cli',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=True,           # CLI — must have console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )

    coll = COLLECT(
        exe_gui,
        exe_cli,
        a_gui.binaries,
        a_gui.zipfiles,
        a_gui.datas,
        # Merge CLI-only binaries/datas that aren't already in GUI set
        a_cli.binaries,
        a_cli.zipfiles,
        a_cli.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='Disconnectome',
    )

    app = BUNDLE(
        coll,
        name='Disconnectome.app',
        icon='icon.icns' if os.path.exists('icon.icns') else None,
        bundle_identifier='com.disconnectome.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSRequiresAquaSystemAppearance': 'False',
            'LSMinimumSystemVersion': '10.13.0',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'NIfTI File',
                    'CFBundleTypeRole': 'Viewer',
                    'LSHandlerRank': 'Alternate',
                    'LSItemContentTypes': ['public.nii', 'public.nii.gz'],
                }
            ],
        },
    )

elif IS_WINDOWS:
    # ========================================================================
    # WINDOWS BUILD
    # ========================================================================
    print("\n" + "="*80)
    print("CONFIGURING WINDOWS BUILD")
    print("="*80)

    exe_gui = EXE(
        pyz_gui,
        a_gui.scripts,
        [],
        exclude_binaries=True,
        name='Disconnectome',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,          # GUI — no console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.ico' if os.path.exists('icon.ico') else 'app_icon.png',
        version='version_info.txt' if os.path.exists('version_info.txt') else None,
    )

    exe_cli = EXE(
        pyz_cli,
        a_cli.scripts,
        [],
        exclude_binaries=True,
        name='disconnectome-cli',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,           # CLI — must have console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )

    coll = COLLECT(
        exe_gui,
        exe_cli,
        a_gui.binaries,
        a_gui.zipfiles,
        a_gui.datas,
        a_cli.binaries,
        a_cli.zipfiles,
        a_cli.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='Disconnectome',
    )

elif IS_LINUX:
    # ========================================================================
    # LINUX BUILD
    # ========================================================================
    print("\n" + "="*80)
    print("CONFIGURING LINUX BUILD")
    print("="*80)

    exe_gui = EXE(
        pyz_gui,
        a_gui.scripts,
        [],
        exclude_binaries=True,
        name='Disconnectome',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,          # GUI — no console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='app_icon.png',
    )

    exe_cli = EXE(
        pyz_cli,
        a_cli.scripts,
        [],
        exclude_binaries=True,
        name='disconnectome-cli',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,           # CLI — must have console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )

    coll = COLLECT(
        exe_gui,
        exe_cli,
        a_gui.binaries,
        a_gui.zipfiles,
        a_gui.datas,
        a_cli.binaries,
        a_cli.zipfiles,
        a_cli.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='Disconnectome',
    )

# ============================================================================
# BUILD SUMMARY
# ============================================================================
print("\n" + "="*80)
print("BUILD CONFIGURATION SUMMARY")
print("="*80)
print(f"Platform          : {sys.platform}")
print(f"GUI entry point   : app.py  → Disconnectome")
print(f"CLI entry point   : cli.py  → disconnectome-cli")
print(f"GUI data files    : {len(a_gui.datas)}")
print(f"CLI data files    : {len(a_cli.datas)}")
print(f"GUI binaries      : {len(a_gui.binaries)}")
print(f"CLI binaries      : {len(a_cli.binaries)}")
print(f"Hidden imports    : {len(hiddenimports)}")
print("="*80 + "\n")
print("Output will be in: dist/Disconnectome/")
print("  Disconnectome        — launch GUI")
print("  disconnectome-cli    — run headless / scripted")
print("="*80 + "\n")
