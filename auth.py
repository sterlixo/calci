#!/usr/bin/env python3
"""
Calcium Auth — Multi-user login system
Stores users in users.json with bcrypt hashed passwords
"""

import json
import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta

try:
    import bcrypt
except ImportError:
    os.system("pip3 install bcrypt --break-system-packages -q")
    import bcrypt

USERS_FILE = Path(__file__).parent / "users.json"
SESSIONS_FILE = Path(__file__).parent / ".sessions.json"

# ── Load / Save users ─────────────────────────────────────────────────────────
def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ── Load / Save sessions ──────────────────────────────────────────────────────
def load_sessions():
    if SESSIONS_FILE.exists():
        with open(SESSIONS_FILE) as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

# ── User operations ───────────────────────────────────────────────────────────
def create_user(username: str, password: str, role: str = "user") -> dict:
    """Create a new user. Returns {success, message}"""
    users = load_users()

    if not username or len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters"}
    if not password or len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters"}
    if username in users:
        return {"success": False, "message": f"User '{username}' already exists"}

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = {
        "password": hashed,
        "role": role,
        "created": datetime.now().isoformat(),
        "last_login": None
    }
    save_users(users)
    return {"success": True, "message": f"User '{username}' created"}

def delete_user(username: str) -> dict:
    """Delete a user."""
    users = load_users()
    if username not in users:
        return {"success": False, "message": "User not found"}
    del users[username]
    save_users(users)
    return {"success": True, "message": f"User '{username}' deleted"}

def list_users() -> list:
    """List all users (without passwords)."""
    users = load_users()
    return [
        {
            "username": u,
            "role": data["role"],
            "created": data.get("created", ""),
            "last_login": data.get("last_login", "Never")
        }
        for u, data in users.items()
    ]

def verify_login(username: str, password: str) -> dict:
    """Verify login credentials. Returns {success, token, role}"""
    users = load_users()

    if username not in users:
        return {"success": False, "message": "Invalid username or password"}

    user = users[username]
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return {"success": False, "message": "Invalid username or password"}

    # Create session token
    token = secrets.token_hex(32)
    sessions = load_sessions()
    sessions[token] = {
        "username": username,
        "role": user["role"],
        "expires": (datetime.now() + timedelta(hours=24)).isoformat()
    }
    save_sessions(sessions)

    # Update last login
    users[username]["last_login"] = datetime.now().isoformat()
    save_users(users)

    return {
        "success": True,
        "token": token,
        "username": username,
        "role": user["role"]
    }

def verify_token(token: str) -> dict:
    """Verify a session token. Returns {valid, username, role}"""
    if not token:
        return {"valid": False}

    sessions = load_sessions()
    if token not in sessions:
        return {"valid": False}

    session = sessions[token]
    # Check expiry
    if datetime.now() > datetime.fromisoformat(session["expires"]):
        del sessions[token]
        save_sessions(sessions)
        return {"valid": False}

    return {
        "valid": True,
        "username": session["username"],
        "role": session["role"]
    }

def logout_token(token: str):
    """Remove a session token."""
    sessions = load_sessions()
    sessions.pop(token, None)
    save_sessions(sessions)

def change_password(username: str, old_password: str, new_password: str) -> dict:
    """Change a user's password."""
    users = load_users()
    if username not in users:
        return {"success": False, "message": "User not found"}
    if not bcrypt.checkpw(old_password.encode(), users[username]["password"].encode()):
        return {"success": False, "message": "Current password is incorrect"}
    if len(new_password) < 6:
        return {"success": False, "message": "New password must be at least 6 characters"}

    users[username]["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    save_users(users)
    return {"success": True, "message": "Password changed successfully"}

# ── Init: create default admin if no users exist ──────────────────────────────
def init_auth():
    users = load_users()
    if not users:
        result = create_user("admin", "calcium123", role="admin")
        print(f"[AUTH] Created default admin user — username: admin, password: calcium123")
        print(f"[AUTH] ⚠ Please change the default password after first login!")
    return len(load_users())

if __name__ == "__main__":
    # CLI user management
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 auth.py [create|delete|list]")
        print("  create <username> <password> [admin|user]")
        print("  delete <username>")
        print("  list")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "create" and len(sys.argv) >= 4:
        role = sys.argv[4] if len(sys.argv) > 4 else "user"
        print(create_user(sys.argv[2], sys.argv[3], role)["message"])
    elif cmd == "delete" and len(sys.argv) >= 3:
        print(delete_user(sys.argv[2])["message"])
    elif cmd == "list":
        users = list_users()
        print(f"\n{'USERNAME':<20} {'ROLE':<10} {'LAST LOGIN'}")
        print("─" * 50)
        for u in users:
            ll = u['last_login'] or 'Never'
            if ll != 'Never':
                ll = ll[:16].replace('T', ' ')
            print(f"{u['username']:<20} {u['role']:<10} {ll}")
        print()
