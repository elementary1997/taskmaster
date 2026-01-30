#!/bin/bash

# Exit on error
set -e

APP_NAME="modern-task-manager"
VERSION="1.0.0"
BUILD_DIR="build_deb"
DEB_DIR="$BUILD_DIR/$APP_NAME-$VERSION"

echo "🚀 Starting Debian package build..."

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/DEBIAN"

# Default to python3
PYTHON_CMD="python3"

# Check for .venv or venv directory and use that python if found
if [ -f ".venv/bin/python" ]; then
    echo "✅ Found active virtual environment in .venv"
    PYTHON_CMD=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    echo "✅ Found active virtual environment in venv"
    PYTHON_CMD="venv/bin/python"
fi

# Check if PyInstaller is installed
echo "🔍 Checking for PyInstaller..."
if ! $PYTHON_CMD -c "import PyInstaller" &> /dev/null; then
    echo "⚠️ PyInstaller not found. Installing..."
    $PYTHON_CMD -m pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install PyInstaller. Please install it manually: $PYTHON_CMD -m pip install pyinstaller"
        exit 1
    fi
fi

# 1. Build binary with PyInstaller
echo "📦 Building binary with PyInstaller using $PYTHON_CMD..."
# Use the detected python command
$PYTHON_CMD -m PyInstaller --noconsole --onefile --name "$APP_NAME" --clean \
    --hidden-import=PySide6.QtCore \
    --hidden-import=PySide6.QtGui \
    --hidden-import=PySide6.QtWidgets \
    modern_task_manager.py

# 2. Copy binary
echo "📂 Copying files..."
cp "dist/$APP_NAME" "$DEB_DIR/usr/bin/"
chmod +x "$DEB_DIR/usr/bin/$APP_NAME"

# 3. Copy desktop file
cp "packaging/modern-task-manager.desktop" "$DEB_DIR/usr/share/applications/"

# 4. Copy control file
cp "packaging/debian/control" "$DEB_DIR/DEBIAN/"

# 5. Build .deb package
echo "🔨 Building .deb package..."
dpkg-deb --build "$DEB_DIR"

echo "✅ Build successful!"
echo "📁 Package located at: $BUILD_DIR/$APP_NAME-$VERSION.deb"
