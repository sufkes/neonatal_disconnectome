#!/bin/bash
# Build script for Disconnectome Linux application
# Usage: ./build_linux.sh [clean|build|both|appimage]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This script is designed for Linux only"
    exit 1
fi

# Configuration
BUILD_TYPE="${1:-both}"
PROJECT_ROOT="$(pwd)"
SPEC_FILE="Disconnectome.spec"

# Check for required files
check_requirements() {
    print_status "Checking requirements..."

    if [ ! -f "$SPEC_FILE" ]; then
        print_error "Spec file not found: $SPEC_FILE"
        exit 1
    fi

    if [ ! -f "app.py" ]; then
        print_error "app.py not found"
        exit 1
    fi

    if ! command -v pyinstaller &> /dev/null; then
        print_error "PyInstaller not found. Install with: pip install pyinstaller"
        exit 1
    fi

    print_status "Requirements check passed"
}

# Clean build artifacts
clean_build() {
    print_status "Cleaning build artifacts..."

    # Remove build directories
    rm -rf build/
    rm -rf dist/
    rm -rf __pycache__/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # Remove spec file generated files
    rm -f Disconnectome.spec.bak

    print_status "Clean complete"
}

clean_user_data() {
    print_status "Cleaning user data directories..."

    # Linux user data locations
    USER_DATA_DIRS=(
        "$HOME/.local/share/Disconnectome"
        "$HOME/.cache/Disconnectome"
    )

    for dir in "${USER_DATA_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            print_warning "Removing: $dir"
            rm -rf "$dir"
        fi
    done

    print_status "User data cleaned"
}

# Check data directory size
check_data_size() {
    print_status "Checking data directory sizes..."

    if [ -d "data" ]; then
        DATA_SIZE=$(du -sh data 2>/dev/null | cut -f1)
        print_warning "data/ directory size: $DATA_SIZE"

        if [ -d "data/controls" ]; then
            CONTROLS_SIZE=$(du -sh data/controls | cut -f1)
            print_warning "data/controls/ directory size: $CONTROLS_SIZE"
            print_warning "Large controls directory may cause build issues"
            echo -n "Continue anyway? (y/n): "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                print_status "Build cancelled"
                exit 0
            fi
        fi
        if [ -d "data/template" ]; then
            CONTROLS_SIZE=$(du -sh data/template | cut -f1)
            print_warning "data/template/ directory size: $CONTROLS_SIZE"
            print_warning "Large template directory may cause build issues"
            echo -n "Continue anyway? (y/n): "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                print_status "Build cancelled"
                exit 0
            fi
        fi
    fi
}

# Create icon if it doesn't exist
create_icon() {
    if [ ! -f "app_icon.png" ]; then
        print_warning "app_icon.png not found. Icon will not be included."
        return
    fi

    # For Linux, PNG is usually sufficient
    # But we can create different sizes for better appearance
    if command -v convert &> /dev/null; then
        print_status "Creating icon sizes from app_icon.png..."

        mkdir -p icons
        for size in 16 32 48 64 128 256; do
            convert app_icon.png -resize ${size}x${size} icons/logo_${size}.png 2>/dev/null || true
        done

        print_status "Icons created in icons/ directory"
    else
        print_warning "ImageMagick not installed. Using app_icon.png as-is."
        print_warning "Install for better icons: sudo apt-get install imagemagick"
    fi
}

# Build the application
build_app() {
    print_status "Starting PyInstaller build..."

    # Set environment variables for build
    export PYTHONOPTIMIZE=1

    # Run PyInstaller
    pyinstaller \
        --clean \
        --noconfirm \
        "$SPEC_FILE" \
        2>&1 | tee build.log

    if [ $? -eq 0 ]; then
        print_status "Build completed successfully!"

        if [ -d "dist/Disconnectome" ]; then
            APP_SIZE=$(du -sh dist/Disconnectome | cut -f1)
            print_status "Application size: $APP_SIZE"
            print_status "Application location: $PROJECT_ROOT/dist/Disconnectome"

            # Make executable
            chmod +x dist/Disconnectome/Disconnectome
        fi
    else
        print_error "Build failed. Check build.log for details"
        exit 1
    fi
}

# Create .desktop file for Linux
create_desktop_file() {
    print_status "Creating .desktop file..."

    cat > dist/Disconnectome/disconnectome.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Disconnectome
Comment=Brain disconnectome analysis tool
Exec=$(pwd)/dist/Disconnectome/Disconnectome
Icon=$(pwd)/dist/Disconnectome/app_icon.png
Terminal=false
Categories=Science;Education;MedicalSoftware;
EOF

    print_status "Desktop file created: dist/Disconnectome/disconnectome.desktop"
    print_status "To install system-wide:"
    print_status "  sudo cp dist/Disconnectome/disconnectome.desktop /usr/share/applications/"
}

# Test the built application
test_app() {
    print_status "Testing application..."

    if [ ! -f "dist/Disconnectome/Disconnectome" ]; then
        print_error "Application not found"
        return 1
    fi

    # Try to launch the app
    print_status "Attempting to launch application..."
    ./dist/Disconnectome/Disconnectome &

    print_status "Application launched. Check if it opens correctly."
    print_warning "Press Ctrl+C to stop if app doesn't open or crashes"
    sleep 5
}

# Create AppImage (portable Linux application)
create_appimage() {
    if [ ! -d "dist/Disconnectome" ]; then
        print_error "Application not found. Build first."
        return 1
    fi

    print_status "Creating AppImage..."

    # Check for appimagetool
    if ! command -v appimagetool &> /dev/null; then
        print_warning "appimagetool not found. Downloading..."

        wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
            -O appimagetool
        chmod +x appimagetool
    fi

    # Create AppDir structure
    APP_DIR="Disconnectome.AppDir"
    rm -rf "$APP_DIR"
    mkdir -p "$APP_DIR/usr/bin"
    mkdir -p "$APP_DIR/usr/share/applications"
    mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

    # Copy application
    cp -r dist/Disconnectome/* "$APP_DIR/usr/bin/"

    # Copy icon
    if [ -f "app_icon.png" ]; then
        cp app_icon.png "$APP_DIR/usr/share/icons/hicolor/256x256/apps/disconnectome.png"
        cp app_icon.png "$APP_DIR/disconnectome.png"
    fi

    # Create desktop file
    cat > "$APP_DIR/disconnectome.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Disconnectome
Comment=Brain disconnectome analysis tool
Exec=Disconnectome
Icon=disconnectome
Terminal=false
Categories=Science;Education;MedicalSoftware;
EOF

    # Copy desktop file
    cp "$APP_DIR/disconnectome.desktop" "$APP_DIR/usr/share/applications/"

    # Create AppRun
    cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin"
exec "${HERE}/usr/bin/Disconnectome" "$@"
EOF

    chmod +x "$APP_DIR/AppRun"

    # Build AppImage
    ARCH=x86_64 ./appimagetool "$APP_DIR" Disconnectome-x86_64.AppImage

    if [ $? -eq 0 ]; then
        APP_SIZE=$(du -sh Disconnectome-x86_64.AppImage | cut -f1)
        print_status "AppImage created: Disconnectome-x86_64.AppImage ($APP_SIZE)"
        print_status "You can now distribute this single file!"
    else
        print_error "Failed to create AppImage"
        return 1
    fi

    # Clean up
    rm -rf "$APP_DIR"
}

# Create DEB package
create_deb() {
    if [ ! -d "dist/Disconnectome" ]; then
        print_error "Application not found. Build first."
        return 1
    fi

    print_status "Creating DEB package..."

    # Create package structure
    PKG_DIR="disconnectome_1.0.0_amd64"
    rm -rf "$PKG_DIR"

    mkdir -p "$PKG_DIR/DEBIAN"
    mkdir -p "$PKG_DIR/opt/disconnectome"
    mkdir -p "$PKG_DIR/usr/share/applications"
    mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$PKG_DIR/usr/bin"

    # Copy application
    cp -r dist/Disconnectome/* "$PKG_DIR/opt/disconnectome/"

    # Create symlink
    cat > "$PKG_DIR/usr/bin/disconnectome" << 'EOF'
#!/bin/bash
cd /opt/disconnectome
exec /opt/disconnectome/Disconnectome "$@"
EOF
    chmod +x "$PKG_DIR/usr/bin/disconnectome"

    # Copy icon
    if [ -f "app_icon.png" ]; then
        cp app_icon.png "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/disconnectome.png"
    fi

    # Create desktop file
    cat > "$PKG_DIR/usr/share/applications/disconnectome.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Disconnectome
Comment=Brain disconnectome analysis tool
Exec=/usr/bin/disconnectome
Icon=disconnectome
Terminal=false
Categories=Science;Education;MedicalSoftware;
EOF

    # Create control file
    cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: disconnectome
Version: 1.0.0
Section: science
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8)
Maintainer: Your Name <your.email@example.com>
Description: Brain disconnectome analysis tool
 Disconnectome is a tool for analyzing brain disconnectivity
 patterns in neonatal brain imaging data.
EOF

    # Build package
    dpkg-deb --build "$PKG_DIR"

    if [ $? -eq 0 ]; then
        PKG_SIZE=$(du -sh "${PKG_DIR}.deb" | cut -f1)
        print_status "DEB package created: ${PKG_DIR}.deb ($PKG_SIZE)"
        print_status "Install with: sudo dpkg -i ${PKG_DIR}.deb"
    else
        print_error "Failed to create DEB package"
        return 1
    fi

    # Clean up
    rm -rf "$PKG_DIR"
}

# Troubleshooting function
troubleshoot() {
    print_status "Running diagnostics..."

    echo ""
    echo "System Information:"
    uname -a

    echo ""
    echo "Python Version:"
    python --version

    echo ""
    echo "PyInstaller Version:"
    pyinstaller --version

    echo ""
    echo "Installed Packages (relevant):"
    pip list | grep -E "customtkinter|antspyx|scipy|numpy|nibabel|dipy"

    echo ""
    echo "Project Structure:"
    tree -L 2 -I '__pycache__|*.pyc|build|dist' 2>/dev/null || ls -R | head -50

    echo ""
    echo "Display Server:"
    echo "DISPLAY=$DISPLAY"
    echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"

    echo ""
    print_status "Check build.log for detailed error messages"
}

# Main execution
main() {
    echo ""
    echo "========================================"
    echo "  Disconnectome Linux Build Script"
    echo "========================================"
    echo ""

    check_requirements

    case "$BUILD_TYPE" in
        clean)
            clean_build
            ;;
        clean-all)
            clean_build
            clean_user_data
            ;;
        build)
            check_data_size
            create_icon
            build_app
            create_desktop_file
            ;;
        both)
            clean_build
            check_data_size
            create_icon
            build_app
            create_desktop_file
            ;;
        test)
            test_app
            ;;
        appimage)
            create_appimage
            ;;
        deb)
            create_deb
            ;;
        troubleshoot)
            troubleshoot
            ;;
        *)
            echo "Usage: $0 [clean|clean-all|build|both|test|appimage|deb|troubleshoot]"
            echo ""
            echo "Options:"
            echo "  clean         - Remove build artifacts"
            echo "  clean-all     - Remove build artifacts AND user data"
            echo "  build         - Build the application"
            echo "  both          - Clean then build (default)"
            echo "  test          - Test the built application"
            echo "  appimage      - Create portable AppImage"
            echo "  deb           - Create DEB package"
            echo "  troubleshoot  - Run diagnostics"
            exit 1
            ;;
    esac

    echo ""
    print_status "Done!"
}

# Run main function
main
