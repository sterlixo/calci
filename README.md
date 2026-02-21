# 🔴 KaliCopilot — AI Pentesting Copilot

AI-powered pentesting assistant for Kali Linux, built with **OpenRouter free models** (Llama 3, Mistral, Gemma, etc.)

## Features
- 💬 **Natural language pentesting assistant** — ask anything
- 🖥️ **CLI mode** — terminal-based chat with colored output
- 🌐 **Web UI mode** — hacker-themed browser interface
- ⚡ **Run & analyze** — execute tools and get instant AI analysis
- 📋 **Quick prompts** — common pentest workflows one click away
- 💾 **Session export** — save conversations to JSON

## Quick Start

### 1. Install dependencies
```bash
chmod +x setup.sh && ./setup.sh
```

### 2. Get FREE API key
Sign up at https://openrouter.ai — it's completely free.

### 3. Set API key
```bash
export OPENROUTER_API_KEY=sk-or-your-key-here
```

To make it permanent:
```bash
echo 'export OPENROUTER_API_KEY=sk-or-your-key-here' >> ~/.bashrc
source ~/.bashrc
```

### 4. Run

**CLI mode:**
```bash
python3 copilot.py
```

**Web UI mode:**
```bash
python3 server.py
# Open http://localhost:5000
```

## CLI Commands
| Command | Description |
|---------|-------------|
| `run <cmd>` | Execute a tool + get AI analysis |
| `analyze` | Paste tool output for analysis |
| `save` | Export session to JSON |
| `clear` | Clear conversation history |
| `model <name>` | Switch AI model |
| `exit` | Quit |

## Free Models Available (OpenRouter)
- `meta-llama/llama-3.3-70b-instruct:free` ← default (best)
- `mistralai/mistral-7b-instruct:free`
- `google/gemma-3-27b-it:free`
- `deepseek/deepseek-r1:free`
- `qwen/qwen-2.5-72b-instruct:free`

## Ethical Use
This tool is for **authorized penetration testing only** — CTFs, bug bounties, your own lab, or systems you have explicit written permission to test.

## Files
```
kali-copilot/
├── copilot.py    # CLI chatbot
├── server.py     # Flask web server
├── index.html    # Web UI frontend
├── setup.sh      # Install script
└── README.md     # This file
```
