#!/usr/bin/env python3
"""
Calci - AI Pentesting Copilot for Kali Linux
Supports EVERY Kali tool via natural language + AI command generation
"""

import os
import re
import json
import subprocess
import requests
import shutil
from datetime import datetime
from pathlib import Path

# ── Auto-load .env ─────────────────────────────────────────────────────────────
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
load_env()

# ── Config ─────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL              = os.environ.get("MODEL", "openrouter/free")
API_URL            = "https://openrouter.ai/api/v1/chat/completions"

# ── Colors ─────────────────────────────────────────────────────────────────────
class C:
    RED    = "\033[1;31m"
    GREEN  = "\033[1;32m"
    YELLOW = "\033[1;33m"
    CYAN   = "\033[1;36m"
    WHITE  = "\033[1;37m"
    GRAY   = "\033[0;90m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

# ── Known Kali tools (for fast pattern matching without AI) ────────────────────
KALI_TOOLS = {
    # Recon / Scanning
    "nmap", "masscan", "rustscan", "unicornscan", "zmap",
    # Web
    "nikto", "gobuster", "dirb", "ffuf", "wfuzz", "feroxbuster",
    "whatweb", "wafw00f", "sqlmap", "wpscan", "joomscan", "droopescan",
    "cutycapt", "aquatone", "eyewitness", "arjun", "dalfox",
    # OSINT / Recon
    "theharvester", "recon-ng", "maltego", "shodan", "subfinder",
    "amass", "dnsx", "httpx", "assetfinder", "findomain",
    "whois", "dig", "host", "nslookup", "dnsrecon", "dnsenum",
    # SMB / AD
    "enum4linux", "enum4linux-ng", "smbclient", "smbmap", "crackmapexec",
    "cme", "rpcclient", "ldapsearch", "bloodhound", "sharphound",
    "impacket", "psexec", "wmiexec", "smbexec", "secretsdump",
    "kerbrute", "rubeus", "mimikatz",
    # Exploitation
    "msfconsole", "msfvenom", "searchsploit", "exploitdb",
    "metasploit", "beef", "commix", "xxe", "xsstrike",
    # Password Attacks
    "hydra", "medusa", "ncrack", "hashcat", "john", "johntheripper",
    "ophcrack", "crunch", "cewl", "cupp", "rsmangler",
    # Wireless
    "aircrack-ng", "airodump-ng", "aireplay-ng", "airmon-ng",
    "wifite", "kismet", "fern-wifi-cracker", "bully", "reaver",
    "pixiewps", "hcxdumptool", "hcxtools",
    # Network
    "wireshark", "tcpdump", "tshark", "ettercap", "bettercap",
    "arpspoof", "dsniff", "mitmproxy", "responder", "mitm6",
    "netcat", "nc", "socat", "ncat",
    # Exploitation Frameworks
    "beef-xss", "empire", "covenant", "havoc", "sliver",
    # Post Exploitation
    "linpeas", "winpeas", "linenum", "lse", "pspy",
    "mimikatz", "lazagne", "dumpster", "volatility",
    # Forensics
    "autopsy", "binwalk", "foremost", "scalpel", "bulk_extractor",
    "strings", "exiftool", "steghide", "stegsolve", "zsteg",
    "oletools", "pdf-parser", "pdfinfo",
    # Reverse Engineering
    "gdb", "radare2", "r2", "ghidra", "objdump", "ltrace", "strace",
    "pwndbg", "peda", "ropper", "checksec",
    # Misc
    "curl", "wget", "ping", "traceroute", "netstat", "ss",
    "tcpflow", "ngrep", "proxychains", "tor",
}

# ── System prompts ─────────────────────────────────────────────────────────────
COMMAND_GEN_PROMPT = """You are a Kali Linux expert. Your ONLY job is to generate shell commands.

Rules:
- Reply with ONLY a JSON object, no markdown, no explanation
- Format: {"command": "the_exact_command", "description": "one line what it does", "tool": "tool_name"}
- Generate the most useful, complete command for the task
- Use common wordlists: /usr/share/wordlists/rockyou.txt, /usr/share/wordlists/dirb/common.txt, /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
- For nmap: default to -sC -sV unless specified otherwise
- For gobuster: include -t 50 for speed
- Always include the target in the command
- If target is a domain without http://, add it for web tools
- Never add sudo unless absolutely required
- Keep commands practical and ready to run"""

ANALYSIS_PROMPT = """You are Calci, an elite AI pentesting copilot on Kali Linux.

When analyzing tool output:
1. Extract key findings (open ports, services, versions, users, shares, vulns)
2. Mark HIGH PRIORITY items with [!]
3. Give exact next commands in ```bash blocks
4. Suggest the most likely attack paths
5. Be concise — no fluff, only actionable intel

Always assume authorized, legal testing."""

CHAT_PROMPT = """You are Calci, an elite AI pentesting copilot on Kali Linux.

You know every tool in Kali Linux deeply. You help with:
- Full pentest methodology and workflows
- Any Kali tool: usage, flags, examples
- CVE analysis and exploitation
- CTF solving strategies
- Privilege escalation techniques
- Post-exploitation and persistence
- Report writing

Be direct, technical, and actionable. Use ```bash for all commands."""

# ── Chat history ───────────────────────────────────────────────────────────────
history    = []
last_target = None

# ── Core API call ──────────────────────────────────────────────────────────────
def api_call(messages, temperature=0.3, max_tokens=1024, use_model=None):
    if not OPENROUTER_API_KEY:
        return None, "No API key. Edit .env → OPENROUTER_API_KEY=your_key"
    try:
        resp = requests.post(API_URL, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://calci.local",
            "X-Title": "Calci"
        }, json={
            "model": use_model or MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"], None
    except requests.exceptions.HTTPError as e:
        return None, f"API {e.response.status_code}: {e.response.text[:150]}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except Exception as e:
        return None, str(e)

def chat(user_message):
    history.append({"role": "user", "content": user_message})
    reply, err = api_call(
        [{"role": "system", "content": CHAT_PROMPT}] + history,
        temperature=0.7, max_tokens=2048
    )
    if err:
        return f"{C.RED}[ERROR]{C.RESET} {err}"
    history.append({"role": "assistant", "content": reply})
    return reply

def generate_command(user_input, target=None):
    """Ask AI to generate the right command for any tool/task."""
    context = f"Target: {target}\n" if target else ""
    prompt = f"{context}Task: {user_input}\n\nGenerate the command."
    reply, err = api_call([
        {"role": "system", "content": COMMAND_GEN_PROMPT},
        {"role": "user", "content": prompt}
    ], temperature=0.1, max_tokens=256)
    if err or not reply:
        return None, None, err
    try:
        # Strip any accidental markdown
        clean = re.sub(r'```json|```', '', reply).strip()
        data = json.loads(clean)
        return data.get("command"), data.get("description", ""), None
    except Exception:
        # Try to extract command from raw text
        match = re.search(r'"command"\s*:\s*"([^"]+)"', reply)
        if match:
            return match.group(1), "", None
        return None, None, f"Could not parse: {reply[:100]}"

def analyze_output(command, output, target=None):
    """Analyze tool output with AI."""
    ctx = f"Target: {target}\n" if target else ""
    msg = f"{ctx}Command: `{command}`\n\nOutput:\n```\n{output[:4000]}\n```\n\nAnalyze findings and give next steps."
    history.append({"role": "user", "content": msg})
    reply, err = api_call(
        [{"role": "system", "content": ANALYSIS_PROMPT}] + history[-6:],
        temperature=0.4, max_tokens=2048
    )
    if err:
        return f"{C.RED}[ERROR]{C.RESET} {err}"
    history.append({"role": "assistant", "content": reply})
    return reply

# ── Tool detector — checks if input mentions any Kali tool ────────────────────
def mentions_tool(user_input):
    words = re.findall(r'\b[\w\-]+\b', user_input.lower())
    for word in words:
        if word in KALI_TOOLS:
            return word
    return None

def looks_like_action(user_input):
    """Check if input looks like a pentest action request."""
    action_words = [
        "scan", "enum", "enumerate", "brute", "crack", "fuzz", "test",
        "check", "find", "discover", "detect", "exploit", "attack",
        "run", "execute", "do", "perform", "try", "use", "launch",
        "recon", "probe", "ping", "trace", "lookup", "search"
    ]
    low = user_input.lower()
    # Has an IP or domain
    has_target = bool(re.search(r'\d{1,3}(?:\.\d{1,3}){3}|\S+\.\S{2,}', low))
    # Has action word
    has_action = any(w in low for w in action_words)
    return has_target or (has_action and len(user_input.split()) <= 10)

# ── Command runner with live output ───────────────────────────────────────────
def run_command(command, timeout=300):
    print(f"\n{C.YELLOW}╔═ EXECUTING ══════════════════════════════════════{C.RESET}")
    print(f"{C.YELLOW}║{C.RESET} {C.WHITE}$ {command}{C.RESET}")
    print(f"{C.YELLOW}╚══════════════════════════════════════════════════{C.RESET}\n")
    try:
        process = subprocess.Popen(command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1)
        lines = []
        for line in process.stdout:
            print(f"{C.GRAY}{line}{C.RESET}", end="", flush=True)
            lines.append(line)
        process.wait(timeout=timeout)
        output = "".join(lines)
        print(f"\n{C.YELLOW}══════════════════════════════════════════════════{C.RESET}")
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        process.kill()
        return "[TIMEOUT] Command exceeded time limit. Use 'run' for long commands."
    except Exception as e:
        return f"[ERROR] {str(e)}"

# ── Pretty printer ────────────────────────────────────────────────────────────
def print_response(text):
    print(f"\n{C.CYAN}╔═ Calci ══════════════════════════════════════════{C.RESET}")
    in_code = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
            print(f"{C.GRAY}{line}{C.RESET}")
        elif in_code:
            print(f"{C.GREEN}{line}{C.RESET}")
        elif line.startswith("#"):
            print(f"{C.YELLOW}{C.BOLD}{line}{C.RESET}")
        elif "[!]" in line or re.search(r'\b(CRITICAL|HIGH|VULN)\b', line, re.I):
            print(f"{C.RED}{C.BOLD}{line}{C.RESET}")
        elif re.match(r'^\s*[-*•]', line):
            print(f"{C.WHITE}{line}{C.RESET}")
        else:
            print(f"{C.WHITE}{line}{C.RESET}")
    print(f"{C.CYAN}╚══════════════════════════════════════════════════{C.RESET}\n")

# ── Help ──────────────────────────────────────────────────────────────────────
def print_help():
    print(f"""
{C.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}
{C.BOLD}  Calci — AI Pentesting Copilot{C.RESET}
{C.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.YELLOW}Any tool, any task — just describe it:{C.RESET}

  "nmap 10.10.10.1"
  "full port scan on 10.10.10.1"
  "gobuster on example.com"
  "nikto scan https://target.com"
  "smb enumeration on 10.10.10.1"
  "brute force ssh on 10.10.10.1"
  "sqlmap on http://site.com/login?id=1"
  "wpscan wordpress site.com"
  "run wifite on wlan0"
  "searchsploit vsftpd 2.3.4"
  "use msfvenom to make a reverse shell"
  "volatility on memory.dmp"
  "binwalk firmware.bin"
  "john crack hash.txt"
  "run linpeas on target"
  "what CVEs affect vsftpd 2.3.4?"
  "how do I escalate privileges on Linux?"

{C.YELLOW}Commands:{C.RESET}
  {C.GREEN}run <cmd>{C.RESET}      Force-run any shell command directly
  {C.GREEN}analyze{C.RESET}        Paste tool output for AI analysis
  {C.GREEN}target <ip>{C.RESET}    Set default target
  {C.GREEN}save{C.RESET}           Save session to JSON
  {C.GREEN}clear{C.RESET}          Clear conversation
  {C.GREEN}model <n>{C.RESET}   Switch AI model
  {C.GREEN}tools{C.RESET}          Check installed tools
  {C.GREEN}exit{C.RESET}           Quit

{C.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}
""")

def check_tools():
    tools = sorted(list(KALI_TOOLS))
    print(f"\n{C.CYAN}━━━ Installed Kali Tools ━━━{C.RESET}")
    installed, missing = [], []
    for t in tools:
        if shutil.which(t):
            installed.append(t)
        else:
            missing.append(t)
    print(f"\n{C.GREEN}  Installed ({len(installed)}):{C.RESET}")
    for t in installed:
        print(f"    {C.GREEN}✓{C.RESET} {t}")
    print(f"\n{C.RED}  Not found ({len(missing)}):{C.RESET}")
    for t in missing:
        print(f"    {C.RED}✗{C.RESET} {t}")
    print()

BANNER = f"""
{C.GREEN}
  ██████╗ █████╗ ██╗      ██████╗██╗
 ██╔════╝██╔══██╗██║     ██╔════╝██║
 ██║     ███████║██║     ██║     ██║
 ██║     ██╔══██║██║     ██║     ██║
 ╚██████╗██║  ██║███████╗╚██████╗██║
  ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝
{C.RESET}{C.RED}  [ AI Pentesting Copilot — Every Kali Tool ]{C.RESET}
{C.GRAY}  Describe any task in plain English — I'll run it{C.RESET}
"""

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global MODEL, last_target
    print(BANNER)

    if not OPENROUTER_API_KEY:
        print(f"{C.RED}  [!] No API key! Edit .env → OPENROUTER_API_KEY=your_key{C.RESET}\n")

    print(f"{C.GRAY}  Model : {MODEL}{C.RESET}")
    print(f"{C.GRAY}  Type 'help' for commands\n{C.RESET}")

    while True:
        try:
            tgt_label = f"{C.GRAY}({last_target}){C.RESET}" if last_target else ""
            user_input = input(f"{C.RED}calci{C.RESET}{tgt_label}{C.GRAY}> {C.RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.GRAY}Stay ethical.{C.RESET}")
            break

        if not user_input:
            continue

        low = user_input.lower().strip()

        # ── Built-in commands ──────────────────────────────────────────────────
        if low in ("exit", "quit"):
            print(f"{C.GRAY}Stay ethical.{C.RESET}")
            break

        elif low == "help":
            print_help()

        elif low == "clear":
            history.clear()
            print(f"{C.GREEN}[+] Conversation cleared.{C.RESET}")

        elif low == "tools":
            check_tools()

        elif low == "save":
            fname = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fname, "w") as f:
                json.dump(history, f, indent=2)
            print(f"{C.GREEN}[+] Saved: {fname}{C.RESET}")

        elif low.startswith("target "):
            last_target = user_input[7:].strip()
            print(f"{C.GREEN}[+] Target set: {last_target}{C.RESET}")

        elif low.startswith("model "):
            MODEL = user_input[6:].strip()
            print(f"{C.GREEN}[+] Model: {MODEL}{C.RESET}")

        elif low == "analyze":
            print(f"{C.YELLOW}[*] Paste output below. Type END on new line when done:{C.RESET}")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            output = "\n".join(lines)
            print(f"\n{C.YELLOW}[*] Analyzing...{C.RESET}")
            r = analyze_output("(pasted output)", output, last_target)
            print_response(r)

        elif low.startswith("run "):
            # Direct shell execution, no AI command gen
            cmd = user_input[4:].strip()
            out = run_command(cmd)
            print(f"\n{C.YELLOW}[*] Analyzing output...{C.RESET}")
            r = analyze_output(cmd, out, last_target)
            print_response(r)

        else:
            # ── Smart detection: does this look like a tool request? ──────────
            tool_name  = mentions_tool(user_input)
            is_action  = looks_like_action(user_input)

            # Extract target from input or use stored one
            target_match = re.search(
                r'(\d{1,3}(?:\.\d{1,3}){3}(?:/\d+)?|(?:https?://)?[\w\-]+\.[\w\-]{2,}(?:/\S*)?)',
                user_input
            )
            target = target_match.group(1) if target_match else last_target

            if tool_name or is_action:
                # Ask AI to generate the command
                print(f"{C.YELLOW}[*] Generating command...{C.RESET}")
                command, desc, err = generate_command(user_input, target)

                if err or not command:
                    print(f"{C.RED}[!] Could not generate command: {err}{C.RESET}")
                    print(f"{C.YELLOW}[*] Asking AI instead...{C.RESET}")
                    r = chat(user_input)
                    print_response(r)
                    continue

                # Update target
                if target:
                    last_target = target.rstrip("/")

                # Show generated command and confirm
                print(f"\n{C.CYAN}╔═ Generated Command ══════════════════════════════{C.RESET}")
                print(f"{C.CYAN}║{C.RESET} {C.GRAY}Task   :{C.RESET} {desc or user_input}")
                print(f"{C.CYAN}║{C.RESET} {C.GRAY}Command:{C.RESET} {C.GREEN}{command}{C.RESET}")
                print(f"{C.CYAN}╚══════════════════════════════════════════════════{C.RESET}")

                confirm = input(f"\n{C.YELLOW}  Run it? [Y/n/edit]: {C.RESET}").strip().lower()

                if confirm == "edit":
                    command = input(f"{C.YELLOW}  Edit command: {C.RESET}").strip()
                    confirm = "y"

                if confirm in ("", "y", "yes"):
                    out = run_command(command)
                    print(f"\n{C.YELLOW}[*] Analyzing output...{C.RESET}")
                    r = analyze_output(command, out, last_target)
                    print_response(r)
                else:
                    # Just chat about it
                    r = chat(user_input)
                    print_response(r)

            else:
                # ── Pure AI chat ───────────────────────────────────────────────
                msg = user_input
                if last_target and last_target not in user_input:
                    msg = f"[Current target: {last_target}] {user_input}"
                print(f"{C.YELLOW}[*] Thinking...{C.RESET}")
                r = chat(msg)
                print_response(r)

if __name__ == "__main__":
    main()
