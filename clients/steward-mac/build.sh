#!/usr/bin/env bash
# Build and package Steward native macOS Desktop application (IWO-112).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "== Building Steward macOS Desktop Application =="

swift build -c release

BIN_PATH="$(swift build -c release --show-bin-path)/Steward"
APP_DIR="$SCRIPT_DIR/dist/Steward.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cp "$BIN_PATH" "$MACOS_DIR/Steward"

cat > "$CONTENTS_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Steward</string>
    <key>CFBundleIdentifier</key>
    <string>com.ai-lab.steward</string>
    <key>CFBundleName</key>
    <string>Steward</string>
    <key>CFBundleDisplayName</key>
    <string>Steward Desk</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "== Steward.app packaged successfully at $APP_DIR =="
