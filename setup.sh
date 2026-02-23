#!/bin/bash
# KaliCopilot Setup Script
# Run this once to install dependencies

echo ""
echo "  ██╗  ██╗ █████╗ ██╗     ██╗      ██████╗ ██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗"
echo "  ██╔╝██╔╝██╔══██╗██║     ██║     ██╔════╝██╔═══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝"
echo "  █████╔╝ ███████║██║     ██║     ██║     ██║   ██║██████╔╝██║██║     ██║   ██║   ██║   "
echo "  ██╔═██╗ ██╔══██║██║     ██║     ██║     ██║   ██║██╔═══╝ ██║██║     ██║   ██║   ██║   "
echo "  ██║  ██╗██║  ██║███████╗██║     ╚██████╗╚██████╔╝██║     ██║███████╗╚██████╔╝   ██║   "
echo "  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝   "
echo ""
echo "  [ AI-Powered Pentesting Copilot Setup ]"
echo ""

# Install Python dependencies
echo "[*] Installing Python dependencies..."
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt

echo ""
echo "[+] Dependencies installed!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SETUP COMPLETE — Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Get your FREE OpenRouter API key:"
echo "     https://openrouter.ai  (sign up, it's free)"
echo ""
echo "  2. Set your API key:"
echo "     export OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx"
echo ""
echo "  3. Run CLI mode:"
echo "     python3 copilot.py"
echo ""
echo "  4. Run Web UI mode:"
echo "     python3 server.py"
echo "     Then open: http://localhost:5000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
