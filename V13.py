import asyncio
import json
import os

from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import ReactionEmoji

# =========================
# STORAGE
# =========================

BASE_DIR = "/storage/emulated/0/TELEGRAM_CONTROL_V3"
SESSION_DIR = os.path.join(BASE_DIR, "SESSIONS")
DB_FILE = os.path.join(BASE_DIR, "accounts.json")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

accounts = []
clients = {}  # phone -> client
default_account = None

REACTIONS = ["👍", "❤️", "🔥", "😂", "😮"]

# =========================
# UI
# =========================

def clear():
    os.system("clear")

def banner():
    print("""
========================
 TELEGRAM CONTROL PANEL
========================
1. Add Account
2. Show Accounts
3. Enable Account
4. Disable Account
5. Change Default Account
6. Send DM
7. Send Group Message
8. Reply by Link
9. Reaction (Single Account)
10. Join Group
11. Leave Group
12. Exit
========================
""")

# =========================
# DB
# =========================

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(accounts, f, indent=2)

# =========================
# LOGIN
# =========================

async def login_account(acc):
    session_path = os.path.join(SESSION_DIR, acc["session"])

    client = TelegramClient(session_path, acc["api_id"], acc["api_hash"])
    await client.connect()

    print(f"\nLOGIN | {acc['phone']}")

    if not await client.is_user_authorized():
        print("OTP required")
        await client.send_code_request(acc["phone"])
        code = input("OTP: ").strip()

        try:
            await client.sign_in(acc["phone"], code)
        except SessionPasswordNeededError:
            pwd = input("2FA Password: ").strip()
            await client.sign_in(password=pwd)

        print("Session saved")
    else:
        print("Auto login")

    clients[acc["phone"]] = client

# =========================
# LOAD ACCOUNTS
# =========================

async def load_all():
    global accounts

    accounts = load_db()

    seen = set()
    unique = []

    for acc in accounts:
        if acc["phone"] in seen:
            continue
        seen.add(acc["phone"])
        unique.append(acc)

    accounts = unique
    save_db()

    for acc in accounts:
        if acc.get("active", True):
            try:
                await login_account(acc)
            except Exception as e:
                print("Login error:", e)

# =========================
# HELPERS
# =========================

def get_active_accounts():
    return [a for a in accounts if a.get("active", True)]

def select_account():
    show_accounts()
    try:
        i = int(input("Select account #: ")) - 1
        if i < 0 or i >= len(accounts):
            return None
        return accounts[i]
    except:
        return None

# =========================
# SHOW
# =========================

def show_accounts():
    print("\n=== ACCOUNTS ===\n")

    if not accounts:
        print("No accounts found")
        return

    for i, acc in enumerate(accounts, 1):
        status = "ACTIVE" if acc.get("active", True) else "DISABLED"
        mark = " (DEFAULT)" if acc["phone"] == default_account else ""
        print(f"[{i}] {status} | {acc['phone']}{mark}")

# =========================
# RESOLVE
# =========================

async def resolve(client, target):
    target = target.replace("https://t.me/", "").replace("@", "")
    try:
        return await client.get_entity(target)
    except:
        return None

# =========================
# FEATURES
# =========================

async def send_dm():
    acc = select_account()
    if not acc:
        return

    client = clients.get(acc["phone"])
    if not client:
        print("Not logged in")
        return

    target = input("User: ")
    msg = input("Message: ")

    entity = await resolve(client, target)
    if not entity:
        print("Not found")
        return

    await client.send_message(entity, msg)
    print("DM sent")

async def reaction_single():
    acc = select_account()
    if not acc:
        return

    client = clients.get(acc["phone"])
    if not client:
        print("Not logged in")
        return

    link = input("Post link: ").replace("https://t.me/", "").strip("/")
    parts = link.split("/")

    if len(parts) < 2:
        print("Invalid link")
        return

    chat = parts[0]
    msg_id = int(parts[1])

    print("1. 👍 2. ❤️ 3. 🔥 4. 😂 5. 😮")
    r = input("Reaction: ")

    reaction = REACTIONS[int(r)-1] if r.isdigit() and 1 <= int(r) <= 5 else "👍"

    entity = await client.get_entity(chat)

    await client(functions.messages.SendReactionRequest(
        peer=entity,
        msg_id=msg_id,
        reaction=[ReactionEmoji(emoticon=reaction)]
    ))

    print("Reaction sent")

# =========================
# JOIN / LEAVE
# =========================

async def join_group():
    acc = select_account()
    if not acc:
        return

    client = clients.get(acc["phone"])
    link = input("Group link: ")

    entity = await client.get_entity(link)
    await client(JoinChannelRequest(entity))

    print("Joined")

async def leave_group():
    acc = select_account()
    if not acc:
        return

    client = clients.get(acc["phone"])
    link = input("Group link: ")

    entity = await client.get_entity(link)
    await client(LeaveChannelRequest(entity))

    print("Left")

# =========================
# MAIN
# =========================

async def main():
    clear()
    banner()
    await load_all()

    global default_account

    while True:
        choice = input("Choose: ")

        if choice == "2":
            show_accounts()

        elif choice == "6":
            await send_dm()

        elif choice == "9":
            await reaction_single()

        elif choice == "10":
            await join_group()

        elif choice == "11":
            await leave_group()

        else:
            break

    for c in clients.values():
        try:
            await c.disconnect()
        except:
            pass

asyncio.run(main())
