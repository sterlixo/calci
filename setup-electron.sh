#!/bin/bash

echo ""
echo "  [ Calcium Electron App Setup ]"
echo ""

# Install Node.js if not present
if ! command -v node &> /dev/null; then
  echo "[*] Installing Node.js..."
  sudo apt install nodejs npm -y
else
  echo "[✓] Node.js found: $(node -v)"
fi

# Install Electron
echo "[*] Installing Electron (this may take a minute)..."
npm install

# Install Python deps
echo "[*] Installing Python dependencies..."
pip3 install requests flask --break-system-packages 2>/dev/null || pip3 install requests flask

# Install desktop shortcut
echo "[*] Installing desktop shortcut..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sed "s|Exec=bash -c \"cd ~/calci|Exec=bash -c \"cd $SCRIPT_DIR|g" calcium.desktop > ~/.local/share/applications/calcium.desktop
chmod +x ~/.local/share/applications/calcium.desktop

echo ""
echo "[✓] Setup complete!"
echo ""
echo "  To launch Calcium:"
echo "    npm start"
echo ""
echo "  Or find 'Calcium' in your Kali app menu."
echo ""
