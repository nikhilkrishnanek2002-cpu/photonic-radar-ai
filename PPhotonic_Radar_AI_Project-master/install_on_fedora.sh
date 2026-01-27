#!/bin/bash
# PHOENIX-RADAR Fedora Installer

echo "🔵 Detected System: Fedora (Linux)"
echo "🚀 Starting Installation for PHOENIX-RADAR..."

# 1. Install System Dependencies (Qt requirements)
# Note: PySide6 wheels usually include Qt, but some system libs might be needed on Fedora.
echo "📦 Checking system libraries..."
sudo dnf install -y python3-pip python3-devel mesa-libGL zlib libjpeg-turbo libxcb xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm

# 2. Install Python Dependencies
echo "🐍 Installing Python libraries..."
pip3 install --user PySide6 pyqtgraph numpy scipy scikit-learn torch pyyaml

# 3. Make Launcher Executable
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
chmod +x "$PROJECT_DIR/launch_desktop.sh"

# 4. Create Desktop Entry (.desktop file)
ICON_PATH="$PROJECT_DIR/desktop_app/assets/radar_icon.png"
# Create a dummy icon if it doesn't exist to prevent ugly broken image
mkdir -p "$PROJECT_DIR/desktop_app/assets"
if [ ! -f "$ICON_PATH" ]; then
    # Generate a simple red circle as a placeholder icon if needed (optional)
    # For now, we will assume standard system icon or skip
    touch "$ICON_PATH" 
fi

DESKTOP_FILE="$HOME/.local/share/applications/phoenix_radar.desktop"

echo "🖥️  Creating Menu Shortcut..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Name=Phoenix Radar AI
Comment=Photonic Radar & AI Strategic Console
Exec=$PROJECT_DIR/launch_desktop.sh
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Science;Engineering;Education;
EOF

# 5. Fix permissions
chmod +x "$DESKTOP_FILE"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null

echo "✅ Installation Complete!"
echo "   You can now find 'Phoenix Radar AI' in your Applications menu."
echo "   Or run ./launch_desktop.sh to start immediately."
