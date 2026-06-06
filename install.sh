#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# AVCS — Audio Video Conversion Suite
# Install script for Linux (Ubuntu / Debian / Mint / Fedora)
# ══════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/avcs"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

BOLD='\033[1m'
AMBER='\033[33m'
GREEN='\033[32m'
RED='\033[31m'
RESET='\033[0m'

echo ""
echo -e "${AMBER}${BOLD}  ╔═══════════════════════════════════════╗${RESET}"
echo -e "${AMBER}${BOLD}  ║  AVCS — Audio Video Conversion Suite  ║${RESET}"
echo -e "${AMBER}${BOLD}  ║  Installer v1.0.0                     ║${RESET}"
echo -e "${AMBER}${BOLD}  ╚═══════════════════════════════════════╝${RESET}"
echo ""

# ── Detect package manager ───────────────────────────────────────
detect_pm() {
    if command -v apt-get &>/dev/null; then echo "apt"
    elif command -v dnf &>/dev/null;   then echo "dnf"
    elif command -v pacman &>/dev/null; then echo "pacman"
    else echo "unknown"; fi
}
PM=$(detect_pm)

# ── Check Python ─────────────────────────────────────────────────
echo -e "${BOLD}[1/5] Checking Python 3...${RESET}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}  ✗ Python 3 not found.${RESET}"
    echo "  Install it: sudo apt install python3"
    exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}  ✓ Python $PY_VER found${RESET}"

# ── Check / install ffmpeg ───────────────────────────────────────
echo ""
echo -e "${BOLD}[2/5] Checking ffmpeg...${RESET}"
if command -v ffmpeg &>/dev/null; then
    FFMPEG_VER=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
    echo -e "${GREEN}  ✓ ffmpeg $FFMPEG_VER found${RESET}"
else
    echo -e "${AMBER}  ⚠  ffmpeg not found. Attempting to install...${RESET}"
    if [ "$PM" = "apt" ]; then
        sudo apt-get install -y ffmpeg
    elif [ "$PM" = "dnf" ]; then
        sudo dnf install -y ffmpeg
    elif [ "$PM" = "pacman" ]; then
        sudo pacman -S --noconfirm ffmpeg
    else
        echo -e "${RED}  ✗ Cannot auto-install ffmpeg. Please install manually.${RESET}"
        echo "    https://ffmpeg.org/download.html"
    fi
fi

# ── Install Python deps ──────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/5] Installing Python dependencies...${RESET}"

# Prefer system PyQt5 package (avoids pip build issues)
if python3 -c "import PyQt5" &>/dev/null; then
    echo -e "${GREEN}  ✓ PyQt5 already installed${RESET}"
else
    echo "  Installing PyQt5..."
    if [ "$PM" = "apt" ]; then
        sudo apt-get install -y python3-pyqt5 || pip3 install --user PyQt5
    elif [ "$PM" = "dnf" ]; then
        sudo dnf install -y python3-qt5 || pip3 install --user PyQt5
    else
        pip3 install --user PyQt5
    fi
fi

echo -e "${GREEN}  ✓ Dependencies ready${RESET}"

# ── Copy application ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}[4/5] Installing AVCS to $APP_DIR...${RESET}"
mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copy all app files
cp -r "$SCRIPT_DIR"/. "$APP_DIR/"
chmod +x "$APP_DIR/main.py"

# Create launcher script
cat > "$BIN_DIR/avcs" << EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/main.py" "\$@"
EOF
chmod +x "$BIN_DIR/avcs"

echo -e "${GREEN}  ✓ Application installed${RESET}"

# ── Desktop entry ────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[5/5] Creating desktop entry...${RESET}"
cat > "$DESKTOP_DIR/avcs.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AVCS
GenericName=Audio Video Conversion Suite
Comment=Convert video and audio files including legacy TVO format
Exec=python3 $APP_DIR/main.py
Icon=$APP_DIR/banner.svg
Terminal=false
Categories=AudioVideo;Video;Audio;Utility;
Keywords=video;audio;convert;mp4;mkv;avi;tvo;teveo;
StartupWMClass=avcs
EOF

# Refresh desktop database if available
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" &>/dev/null || true
fi

echo -e "${GREEN}  ✓ Desktop entry created${RESET}"

# ── Done ─────────────────────────────────────────────────────────
echo ""
echo -e "${AMBER}${BOLD}  Installation complete!${RESET}"
echo ""
echo "  Run AVCS:"
echo -e "    ${BOLD}avcs${RESET}                      (if ~/.local/bin is in your PATH)"
echo -e "    ${BOLD}python3 $APP_DIR/main.py${RESET}"
echo ""
echo "  Or find 'AVCS' in your application menu."
echo ""

# PATH reminder
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${AMBER}  ⚠  Note: Add ~/.local/bin to your PATH:${RESET}"
    echo "       echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "       source ~/.bashrc"
    echo ""
fi
