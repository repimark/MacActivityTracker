#!/bin/bash

# macOS Time Tracker - Installation Script

echo "================================================"
echo "  macOS Time Tracker - Installation Script"
echo "================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed."
    echo "Installing pip..."
    python3 -get-pip.py
fi

echo "✅ pip3 found"
echo ""

# Install required packages
echo "📦 Installing required Python packages..."
echo ""

pip3 install --user -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "✅ All packages installed successfully!"
echo ""

# Create launch script
echo "📝 Creating launch script..."

cat > launch_tracker.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 time_tracker.py
EOF

chmod +x launch_tracker.sh

echo "✅ Launch script created!"
echo ""

# Create macOS app bundle (optional)
echo "📱 Would you like to create a macOS app bundle? (y/n)"
read -r create_app

if [ "$create_app" = "y" ] || [ "$create_app" = "Y" ]; then
    echo "Creating app bundle..."
    
    APP_NAME="TimeTracker.app"
    APP_DIR="$APP_NAME/Contents/MacOS"
    RESOURCES_DIR="$APP_NAME/Contents/Resources"
    
    mkdir -p "$APP_DIR"
    mkdir -p "$RESOURCES_DIR"
    
    # Copy files
    cp time_tracker.py "$APP_DIR/"
    cp launch_tracker.sh "$APP_DIR/"
    
    # Create Info.plist
    cat > "$APP_NAME/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch_tracker.sh</string>
    <key>CFBundleIdentifier</key>
    <string>com.timetracker.app</string>
    <key>CFBundleName</key>
    <string>TimeTracker</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSUIElement</key>
    <string>1</string>
</dict>
</plist>
PLIST
    
    echo "✅ App bundle created: $APP_NAME"
    echo ""
fi

echo "================================================"
echo "  Installation Complete! 🎉"
echo "================================================"
echo ""
echo "To start the Time Tracker:"
echo "  1. Run: ./launch_tracker.sh"
echo "     OR"
echo "  2. Run: python3 time_tracker.py"
if [ "$create_app" = "y" ] || [ "$create_app" = "Y" ]; then
    echo "     OR"
    echo "  3. Double-click TimeTracker.app"
fi
echo ""
echo "⚠️  IMPORTANT: On first launch, macOS will ask for:"
echo "  • Accessibility permissions (required for tracking)"
echo "  • Screen recording permissions (may be required)"
echo ""
echo "To grant permissions:"
echo "  1. Go to System Settings > Privacy & Security"
echo "  2. Click on 'Accessibility'"
echo "  3. Add and enable Python or TimeTracker"
echo ""
echo "Data will be stored in: ~/.timetracker/"
echo ""
echo "================================================"