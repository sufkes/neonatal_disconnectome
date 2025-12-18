# Disconnectome - Build Instructions

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/your-org/disconnectome)

A desktop application for analyzing brain disconnectivity patterns in neonatal brain imaging data.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Build Instructions](#detailed-build-instructions)
  - [macOS](#building-for-macos)
  - [Windows](#building-for-windows)
  - [Linux](#building-for-linux)
- [Data Package Setup](#data-package-setup)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Disconnectome is a Python-based desktop application built with CustomTkinter that provides a graphical interface for brain lesion disconnectome analysis. The application supports:

- T1w and T2w brain image processing
- Lesion mask warping to age-matched templates
- Disconnectome map generation
- Pre-warped lesion workflow
- Cross-platform deployment (macOS, Windows, Linux)

## Prerequisites

### All Platforms

- **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **8GB RAM minimum** (16GB recommended)
- **10GB free disk space** (for build process and data)

### Platform-Specific Tools

#### macOS

```bash
# Xcode Command Line Tools (required)
xcode-select --install

# Homebrew (recommended)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Optional: ImageMagick for icon conversion
brew install imagemagick
```

#### Windows

- **Visual C++ Redistributable** ([Download](https://aka.ms/vs/17/release/vc_redist.x64.exe))
- **Optional:** ImageMagick for icon conversion ([Download](https://imagemagick.org/script/download.php))
- **Optional:** Inno Setup for creating installers ([Download](https://jrsoftware.org/isinfo.php))

#### Linux (Ubuntu/Debian)

```bash
# Essential build tools
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    python3-tk \
    gcc \
    build-essential \
    pkg-config \
    libhdf5-dev \
    cmake

# Optional: ImageMagick for icon conversion
sudo apt-get install imagemagick
```

#### Linux (Fedora/RHEL)

```bash
# Essential build tools
sudo dnf install -y \
    python3.11 \
    python3-tkinter \
    gcc \
    gcc-c++ \
    make \
    hdf5-devel \
    cmake

# Optional: ImageMagick for icon conversion
sudo dnf install ImageMagick
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/disconnectome.git
cd disconnectome

# 2. Create and activate virtual environment
python3.11 -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 4. Run in development mode
python app.py

# 5. Build for your platform
# macOS:
./build_macos.sh build

# Windows:
.\build_windows.bat build

# Linux:
./build_linux.sh build
```

---

## Detailed Build Instructions

### Building for macOS

#### Step 1: Setup Environment

```bash
# Clone repository
git clone https://github.com/your-org/disconnectome.git
cd disconnectome

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

#### Step 2: Create Application Icon

```bash
# Option 1: Use the automated script
python convert_icon.py

# Option 2: Manual creation with sips (macOS native)
mkdir icon.iconset
sips -z 16 16     app_icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     app_icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     app_icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     app_icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   app_icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   app_icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   app_icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   app_icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   app_icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 app_icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
rm -rf icon.iconset
```

#### Step 3: Build Application

```bash
# Make build script executable
chmod +x build_macos.sh

# Clean previous builds (optional)
./build_macos.sh clean

# Build the application
./build_macos.sh build
```

**Output:** `dist/Disconnectome.app`

#### Step 4: Create DMG Installer (Optional)

```bash
./build_macos.sh dmg
```

**Output:** `Disconnectome-macOS.dmg`

#### Step 5: Code Signing (Optional but Recommended)

```bash
# List available signing identities
security find-identity -v -p codesigning

# Sign the application
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --options runtime \
  dist/Disconnectome.app

# Verify the signature
codesign --verify --verbose dist/Disconnectome.app
spctl --assess --verbose dist/Disconnectome.app
```

#### Step 6: Notarization (For Public Distribution)

```bash
# Store credentials (one-time setup)
xcrun notarytool store-credentials "notarytool-profile" \
  --apple-id "your-email@example.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password"

# Notarize the DMG
xcrun notarytool submit Disconnectome-macOS.dmg \
  --keychain-profile "notarytool-profile" \
  --wait

# Staple the notarization ticket
xcrun stapler staple Disconnectome-macOS.dmg
```

#### Testing

```bash
# Test the built application
./build_macos.sh test

# Or manually
open dist/Disconnectome.app
```

---

### Building for Windows

#### Step 1: Setup Environment

```powershell
# Clone repository
git clone https://github.com/your-org/disconnectome.git
cd disconnectome

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

#### Step 2: Create Application Icon

```powershell
# Option 1: Use the automated script
python convert_icon.py

# Option 2: Manual creation with ImageMagick (if installed)
magick convert app_icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

#### Step 3: Build Application

```powershell
# Clean previous builds (optional)
.\build_windows.bat clean

# Build the application
.\build_windows.bat build
```

**Output:** `dist\Disconnectome\` (folder with all required files)

#### Step 4: Create Installer (Recommended)

**Prerequisites:** Install [Inno Setup](https://jrsoftware.org/isinfo.php)

```powershell
# The build script will create installer.iss if it doesn't exist
.\build_windows.bat installer
```

**Output:** `DisconnectomeSetup-1.0.0.exe`

#### Step 5: Code Signing (Optional but Recommended)

```powershell
# Sign the executable
signtool sign /f "path\to\certificate.pfx" /p "password" `
  /tr "http://timestamp.digicert.com" /td SHA256 /fd SHA256 `
  "dist\Disconnectome\Disconnectome.exe"

# Sign the installer
signtool sign /f "path\to\certificate.pfx" /p "password" `
  /tr "http://timestamp.digicert.com" /td SHA256 /fd SHA256 `
  "DisconnectomeSetup-1.0.0.exe"

# Verify signature
signtool verify /pa "DisconnectomeSetup-1.0.0.exe"
```

#### Testing

```powershell
# Test the built application
.\build_windows.bat test

# Or manually
.\dist\Disconnectome\Disconnectome.exe
```

---

### Building for Linux

#### Step 1: Setup Environment

```bash
# Clone repository
git clone https://github.com/your-org/disconnectome.git
cd disconnectome

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

#### Step 2: Build Application

```bash
# Make build script executable
chmod +x build_linux.sh

# Clean previous builds (optional)
./build_linux.sh clean

# Build the application
./build_linux.sh build
```

**Output:** `dist/Disconnectome/` (folder with all required files)

#### Step 3: Create Distribution Packages

##### Option A: AppImage (Universal, Recommended)

```bash
./build_linux.sh appimage
```

**Output:** `Disconnectome-x86_64.AppImage`

**Usage:**

```bash
chmod +x Disconnectome-x86_64.AppImage
./Disconnectome-x86_64.AppImage
```

##### Option B: DEB Package (Debian/Ubuntu)

```bash
./build_linux.sh deb
```

**Output:** `disconnectome_1.0.0_amd64.deb`

**Installation:**

```bash
sudo dpkg -i disconnectome_1.0.0_amd64.deb
```

##### Option C: RPM Package (Fedora/RHEL)

```bash
# Install RPM build tools
sudo dnf install rpm-build rpmdevtools

# Setup build tree
rpmdev-setuptree

# Copy spec file to rpmbuild
cp packaging/disconnectome.spec ~/rpmbuild/SPECS/

# Build RPM
rpmbuild -ba ~/rpmbuild/SPECS/disconnectome.spec
```

**Output:** `~/rpmbuild/RPMS/x86_64/disconnectome-1.0.0-1.x86_64.rpm`

**Installation:**

```bash
sudo dnf install ~/rpmbuild/RPMS/x86_64/disconnectome-1.0.0-1.x86_64.rpm
```

#### Testing

```bash
# Test the built application
./build_linux.sh test

# Or manually
./dist/Disconnectome/Disconnectome
```

---

## Data Package Setup

The application requires large data files (controls and templates) that are downloaded on first launch.

### Step 1: Create Data Packages

```bash
# Navigate to your project directory
cd /path/to/disconnectome

# Create controls package (assuming you have data/controls/)
tar -czf controls.tar.gz data/controls/

# Create template package (assuming you have data/template/)
tar -czf template.tar.gz data/template/

# Verify packages
ls -lh *.tar.gz
```

### Step 2: Generate Checksums

```bash
# Make script executable
chmod +x generate_checksums.sh

# Generate checksums
./generate_checksums.sh

# Example output:
# controls.tar.gz:
#   MD5: 78d1353481151aeaec8d5d0c74b3ab89
#   Size: 500MB
#
# template.tar.gz:
#   MD5: e82bcba92123638b001efe6353df62c0
#   Size: 3000MB
```

### Step 3: Upload to Hosting Service

Choose one of the following hosting options:

#### Option A: Zenodo (Recommended for Research)

1. Go to [zenodo.org](https://zenodo.org)
2. Create an account
3. Click "Upload" → "New upload"
4. Upload `controls.tar.gz` and `template.tar.gz`
5. Fill in metadata (title, description, authors)
6. Click "Publish"
7. Copy the file URLs (format: `https://zenodo.org/record/{RECORD_ID}/files/{filename}`)

#### Option B: Institutional Server

```bash
# SCP upload to university server
scp controls.tar.gz username@server.university.edu:/public/disconnectome/
scp template.tar.gz username@server.university.edu:/public/disconnectome/

# URLs will be:
# https://server.university.edu/public/disconnectome/controls.tar.gz
# https://server.university.edu/public/disconnectome/template.tar.gz
```

#### Option C: AWS S3

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Create bucket
aws s3 mb s3://disconnectome-data

# Upload with public read access
aws s3 cp controls.tar.gz s3://disconnectome-data/ --acl public-read
aws s3 cp template.tar.gz s3://disconnectome-data/ --acl public-read

# URLs will be:
# https://disconnectome-data.s3.amazonaws.com/controls.tar.gz
# https://disconnectome-data.s3.amazonaws.com/template.tar.gz
```

### Step 4: Update Data Downloader Configuration

Edit `lib/data_downloader.py`:

```python
DATA_SOURCES = {
    "controls": {
        "url": "https://your-actual-url.com/controls.tar.gz",  # UPDATE THIS
        "md5": "78d1353481151aeaec8d5d0c74b3ab89",  # UPDATE WITH ACTUAL MD5
        "size_mb": 500,  # UPDATE WITH ACTUAL SIZE
        "required": True,
        "description": "Control subject tractography data",
    },
    "template": {
        "url": "https://your-actual-url.com/template.tar.gz",  # UPDATE THIS
        "md5": "e82bcba92123638b001efe6353df62c0",  # UPDATE WITH ACTUAL MD5
        "size_mb": 3000,  # UPDATE WITH ACTUAL SIZE
        "required": True,
        "description": "dHCP brain templates (28-44 weeks) and warps",
    },
}
```

---

## Development

### Running in Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run application
python app.py
```

### Project Structure

```
disconnectome/
├── app.py                      # Main application entry point
├── cli.py                      # Command-line interface
├── backend/
│   ├── logic.py                # Processing logic with state management
│   ├── step1*.py               # Warp to age-matched template
│   ├── step2*.py               # Apply lesion to control images
│   ├── step3*.py               # Generate visitation maps
│   ├── step4*.py               # Warp to 40w template
│   └── step5*.py               # Generate disconnectome
├── lib/
│   ├── constants.py            # Application constants and paths
│   ├── state_management.py    # State management system
│   ├── theme_manager.py        # Theme management
│   ├── data_downloader.py      # Data download system
│   ├── gui_utils.py            # GUI utility functions
│   ├── makeThumbnails.py       # Thumbnail generation
│   └── utils.py                # General utilities
├── screens/
│   ├── start_screen.py         # Initial workflow selection
│   ├── warp_form.py            # Brain image + lesion mask input
│   ├── warped_lesion_form.py   # Pre-warped lesion input
│   ├── disconnectome_form.py   # Review warp results
│   ├── result_screen.py        # Final disconnectome display
│   └── loading_overlay.py      # Progress indicator
├── themes/                     # CustomTkinter theme files
│   ├── blue.json
│   ├── teal.json
│   └── macos_graphite.json
├── requirements.txt            # Python dependencies
├── Disconnectome.spec          # PyInstaller specification
├── app_icon.png                # Logo for the application
├── convert_icon.py             # Script to convert PNG icon
├── build_macos.sh              # macOS build script
├── build_windows.bat           # Windows build script
├── build_linux.sh              # Linux build script
└── README.md                   # This file
```

[icon source](https://www.freepik.com/icon/brain_5015667#fromView=keyword&page=1&position=12&uuid=cef2547b-fd43-4e93-9ded-3158650c666b)

### Adding New Themes

1. Create a new JSON file in `themes/` directory:

```json
{
  "CTk": {
    "fg_color": ["#F0F0F0", "#222222"]
  },
  "CTkButton": {
    "fg_color": ["#3B82F6", "#60A5FA"],
    "hover_color": ["#2563EB", "#93C5FD"]
  }
  // ... more widget configurations
}
```

2. The theme will automatically appear in the application's theme selector

### Modifying Build Configuration

Edit `Disconnectome.spec` to customize:

- Hidden imports
- Data files to include
- Excluded modules
- Binary dependencies
- Icon paths

---

## Troubleshooting

### Common Build Issues

#### Issue: PyInstaller fails with "ModuleNotFoundError"

**Solution:** Add missing module to `hiddenimports` in `Disconnectome.spec`:

```python
hiddenimports = [
    # ... existing imports
    'your.missing.module',
]
```

#### Issue: "Permission denied" when creating DATA_ROOT

**Solution:** The application will automatically fall back to a temporary directory. Check logs in `disconnectome.log`.

#### Issue: Application crashes on launch

**Solutions:**

1. Check `disconnectome.log` for error messages
2. Run from terminal to see console output:

   ```bash
   # macOS
   ./dist/Disconnectome.app/Contents/MacOS/Disconnectome

   # Windows
   dist\Disconnectome\Disconnectome.exe

   # Linux
   ./dist/Disconnectome/Disconnectome
   ```

#### Issue: Data download fails

**Solutions:**

1. Verify URLs in `lib/data_downloader.py` are accessible
2. Check MD5 checksums match actual files
3. Ensure firewall allows outbound connections
4. Try downloading manually and placing in data directory

#### Issue: Build is too large

**Solution:** Exclude unnecessary files in `Disconnectome.spec`:

```python
excludes = [
    'matplotlib.tests',
    'scipy.tests',
    'pytest',
    'IPython',
    'jupyter',
    # Add more here
]
```

### Platform-Specific Issues

#### macOS: "App is damaged and can't be opened"

**Cause:** Gatekeeper blocking unsigned application

**Solution:**

```bash
# Remove quarantine attribute
xattr -cr dist/Disconnectome.app

# Or allow in System Preferences > Security & Privacy
```

#### Windows: "Windows protected your PC"

**Cause:** SmartScreen filter blocking unsigned executable

**Solution:**

1. Click "More info"
2. Click "Run anyway"
3. Or: Code sign the application

#### Linux: "error while loading shared libraries"

**Cause:** Missing system libraries

**Solution:**

```bash
# Ubuntu/Debian
sudo apt-get install libxcb-xinerama0

# Fedora
sudo dnf install xcb-util-wm
```

### Getting Help

- **Check logs:** `disconnectome.log` in application directory
- **GitHub Issues:** [Report a bug](https://github.com/your-org/disconnectome/issues)
- **Email support:** support@yourlab.edu

---

## Continuous Integration

### GitHub Actions

The repository includes a `.github/workflows/build.yml` file for automated builds.

**To trigger a build:**

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will automatically:

1. Build for all three platforms
2. Run tests
3. Create a GitHub Release
4. Upload build artifacts

---

## Pre-Release Checklist

Before releasing to production:

- [ ] Update version number in `lib/constants.py`
- [ ] Upload data packages to hosting service
- [ ] Update `lib/data_downloader.py` with real URLs and checksums
- [ ] Test data download on fresh installation
- [ ] Test complete workflow on all platforms
- [ ] Update CHANGELOG.md
- [ ] Create release notes
- [ ] Code sign applications (optional)
- [ ] Test installers on clean systems

---

## Distribution

### GitHub Releases

1. **Create Release:**

   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Draft Release on GitHub:**

   - Go to Releases → Draft a new release
   - Select tag `v1.0.0`
   - Add release notes
   - Upload binaries:
     - `Disconnectome-macOS.dmg`
     - `DisconnectomeSetup-1.0.0.exe`
     - `Disconnectome-x86_64.AppImage`
     - `disconnectome_1.0.0_amd64.deb`

3. **Publish Release**

### Alternative Distribution Channels

- **Homebrew (macOS):** Create a Homebrew formula
- **Chocolatey (Windows):** Create a Chocolatey package
- **Snap Store (Linux):** Create a Snap package
- **FlatHub (Linux):** Create a Flatpak

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to new functions
- Update documentation for new features
- Test on at least two platforms before submitting PR

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [ANTs](http://stnava.github.io/ANTs/) - Image registration toolkit

---

## Citation

If you use this software in your research, please cite:

```bibtex
@software{disconnectome2024,
  author = {Your Name},
  title = {Disconnectome: Brain Disconnectome Analysis Tool},
  year = {2024},
  url = {https://github.com/sufkes/neonatal_disconnectome}
}
```

---

## Support

For questions, issues, or feature requests:

- **Documentation:** [https://github.com/sufkes/neonatal_disconnectome](https://github.com/sufkes/neonatal_disconnectome)
- **Issues:** [GitHub Issues](https://github.com/sufkes/neonatal_disconnectome/issues)
- **Email:** support@yourlab.edu

---

**Last Updated:** December 2025
**Version:** 1.0.0
