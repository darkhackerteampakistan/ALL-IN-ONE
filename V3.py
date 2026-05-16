import asyncio
import json
import os

from telethon import TelegramClient

# =========================
# STORAGE (FILE MANAGER VISIBLE)
# =========================

BASE_DIR = "/storage/emulated/0/TELEGRAM_CONTROL_V3"
SESSION_DIR = os.path.join(BASE_DIR, "SESSIONS")
DB_FILE = os.path.join(BASE_DIR, "accounts.json")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(BASE_DIR, exist_ok=True)

clients = []
accounts = []

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


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# UI
# =========================

def banner():
    print("""
=====================================
   TELEGRAM CONTROL PANEL V3
   File Manager Storage Version
=====================================
DM | Group | Comment | Account Manager
=====================================
""")

# =========================
# LOGIN
# =========================

async def login_account(i, acc):
    session_path = os.path.join(SESSION_DIR, acc["session"])

    client = TelegramClient(session_path, acc["api_id"], acc["api_hash"])
    await client.connect()

    print(f"\nACCOUNT {i} | ****{acc['phone'][-4:]}")

    if not await client.is_user_authorized():
        print("OTP required")
        await client.send_code_request(acc["phone"])
        code = input("OTP: ").strip()
        await client.sign_in(acc["phone"], code)
        print("Session saved")
    else:
        print("Auto login")

    return client

# =========================
# LOAD ACCOUNTS
# =========================

async def load_all():
    global accounts

    accounts = load_db()
    active = [a for a in accounts if a.get("active", True)]

    for i, acc in enumerate(active, 1):
        try:
            client = await login_account(i, acc)
            clients.append(client)
        except Exception as e:
            print("Login error:", e)

# =========================
# ADD ACCOUNT
# =========================

async def add_account():
    acc = {
        "session": f"acc{len(accounts)+1}",
        "api_id": int(input("API ID: ")),
        "api_hash": input("API HASH: "),
        "phone": input("PHONE: "),
        "active": True
    }

    accounts.append(acc)
    save_db(accounts)

    client = await login_account(len(accounts), acc)
    clients.append(client)

# =========================
# SHOW
# =========================

def show_accounts():
    print("\n=== ACCOUNTS ===")
    for i, acc in enumerate(accounts, 1):
        status = "ACTIVE" if acc.get("active", True) else "DISABLED"
        print(f"[{i}] {status} | {acc['phone']}")

# =========================
# ENABLE / DISABLE
# =========================

def disable_account():
    show_accounts()
    i = int(input("Disable #: ")) - 1
    if 0 <= i < len(accounts):
        accounts[i]["active"] = False
        save_db(accounts)
        print("Disabled")


def enable_account():
    show_accounts()
    i = int(input("Enable #: ")) - 1
    if 0 <= i < len(accounts):
        accounts[i]["active"] = True
        save_db(accounts)
        print("Enabled")

# =========================
# SELECT CLIENT
# =========================

def select_client():
    show_accounts()
    i = int(input("Select account #: ")) - 1

    if 0 <= i < len(clients):
        return clients[i]

    print("Invalid selection")
    return None

# =========================
# HELPERS
# =========================

async def send_dm(client):
    user = input("Username / ID / Phone: ")
    msg = input("Message: ")

    entity = await client.get_entity(user)
    await client.send_message(entity, msg)

    print("Sent DM")


async def send_group(client):
    group = input("Group username / ID: ")
    msg = input("Message: ")

    entity = await client.get_entity(group)
    await client.send_message(entity, msg)

    print("Sent Group Message")


async def comment_post(client):
    link = input("Post link: ")
    comment = input("Comment: ")

    link = link.replace("https://t.me/", "").replace("http://t.me/", "").strip("/")

    parts = link.split("/")

    if len(parts) < 2:
        print("Invalid link")
        return

    chat = parts[0]
    msg_id = int(parts[1])

    entity = await client.get_entity(chat)

    await client.send_message(entity, comment, reply_to=msg_id)

    print("Comment sent")

# =========================
# MAIN
# =========================

async def main():
    banner()
    print("Storage:", BASE_DIR)

    await load_all()

    while True:
        print("""
========================
1. Add Account
2. Show Accounts
3. Disable Account
4. Enable Account
5. Send DM
6. Send Group Message
7. Comment on Post
8. Exit
========================
""")

        choice = input("Choose: ").strip()

        if choice == "1":
            await add_account()

        elif choice == "2":
            show_accounts()

        elif choice == "3":
            disable_account()

        elif choice == "4":
            enable_account()

        elif choice == "5":
            client = select_client()
            if client:
                await send_dm(client)

        elif choice == "6":
            client = select_client()
            if client:
                await send_group(client)

        elif choice == "7":
            client = select_client()
            if client:
                await comment_post(client)

        else:
            break

    for c in clients:
        try:
            await c.disconnect()
        except:
            pass


asyncio.run(main())
