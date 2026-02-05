# -*- mode: python ; coding: utf-8 -*-
"""
Cross-Platform PyInstaller Spec File for Disconnectome
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
    ('user_settings.json', '.'),
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
    'PIL._tkinter_finder',
    'PIL._imagingtk',
    'customtkinter',
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

    # ✅ FIX: Add jaraco imports
    'jaraco',
    'jaraco.text',
    'jaraco.functools',
    'jaraco.context',
    'jaraco.collections',
    'jaraco.classes',

    # ✅ FIX: Add jaraco dependencies
    'importlib_metadata',
    'importlib_resources',
    'zipp',
    'more_itertools',

    # ✅ FIX: Add pkg_resources (often the root cause)
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
    print(f"✓ Collected CustomTkinter: {len(tmp_ret[0])} data files, {len(tmp_ret[1])} binaries")
except Exception as e:
    print(f"⚠ Warning: Could not collect customtkinter: {e}")

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

    print(f"✅ Collected jaraco: {len(jaraco_ret[0])} data files")
    print(f"✅ Collected jaraco.text: {len(jaraco_text_ret[0])} data files")
except Exception as e:
    print(f"⚠️  Warning: Could not collect jaraco packages: {e}")

# ANTsPyx - can be large, collect selectively
try:
    ants_data = collect_data_files('antspyx', include_py_files=False)
    # Filter out large files (>50MB)
    ants_data_filtered = [
        (src, dst) for src, dst in ants_data
        if os.path.exists(src) and os.path.getsize(src) < 50 * 1024 * 1024
    ]
    datas += ants_data_filtered
    print(f"✓ Collected ANTsPyx: {len(ants_data_filtered)} data files (filtered)")

    # Collect ANTsPyx binaries
    tmp_ret = collect_all('antspyx')
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception as e:
    print(f"⚠ Warning: Could not collect antspyx: {e}")

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
# ANALYSIS
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
# REMOVE DUPLICATES AND LARGE FILES
# ============================================================================
# Remove duplicate files
seen = set()
a.datas = [x for x in a.datas if not (x[0] in seen or seen.add(x[0]))]

# Remove duplicate binaries
seen_bin = set()
a.binaries = [x for x in a.binaries if not (x[0] in seen_bin or seen_bin.add(x[0]))]

# Log large files (for debugging)
print("\n" + "="*80)
print("LARGE FILES (>10MB) BEING INCLUDED:")
print("="*80)
large_files_found = False
for dest, src, typ in a.datas:
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
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Disconnectome',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # UPX causes issues on macOS
        console=False,  # No console for production
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.icns' if os.path.exists('icon.icns') else 'app_icon.png'
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
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

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Disconnectome',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,  # UPX works better on Windows
        console=False,  # No console for production
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.ico' if os.path.exists('icon.ico') else 'app_icon.png',
        version='version_info.txt' if os.path.exists('version_info.txt') else None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
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

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Disconnectome',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # No console for production
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='app_icon.png',
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
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
print(f"Platform: {sys.platform}")
print(f"Data files: {len(a.datas)}")
print(f"Binary files: {len(a.binaries)}")
print(f"Python modules: {len(a.pure)}")
print(f"Hidden imports: {len(hiddenimports)}")
print("="*80 + "\n")
