import asyncio
import json
import os
import random

from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import ReactionEmoji

# =========================
# STORAGE (SD CARD)
# =========================

BASE_DIR = "/storage/emulated/0/TELEGRAM_CONTROL_V3"
SESSION_DIR = os.path.join(BASE_DIR, "SESSIONS")
DB_FILE = os.path.join(BASE_DIR, "accounts.json")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

clients = []
accounts = []

REACTIONS = ["👍", "❤️", "🔥", "😂", "😮"]

# =========================
# UI
# =========================

def clear():
    os.system("clear")

def banner():
    print("""
====================================
   TELEGRAM CONTROL PANEL (FINAL)
====================================
AUTO: Reaction | Join | Leave
MANUAL: DM | Group | Comment
====================================
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

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

        try:
            await client.sign_in(acc["phone"], code)
        except SessionPasswordNeededError:
            pwd = input("2FA Password: ").strip()
            await client.sign_in(password=pwd)

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
        except:
            pass

# =========================
# ACCOUNT MANAGEMENT
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

def show_accounts():
    print("\n=== ACCOUNTS ===")
    for i, acc in enumerate(accounts, 1):
        status = "ACTIVE" if acc.get("active", True) else "DISABLED"
        print(f"[{i}] {status} | {acc['phone']}")

def disable_account():
    show_accounts()
    i = int(input("Disable #: ")) - 1
    if 0 <= i < len(accounts):
        accounts[i]["active"] = False
        save_db(accounts)

def enable_account():
    show_accounts()
    i = int(input("Enable #: ")) - 1
    if 0 <= i < len(accounts):
        accounts[i]["active"] = True
        save_db(accounts)

def select_client():
    show_accounts()
    i = int(input("Select account #: ")) - 1

    if 0 <= i < len(clients):
        return clients[i]

    return None

# =========================
# MANUAL FEATURES
# =========================

async def send_dm(client):
    user = input("User/ID/Phone: ")
    msg = input("Message: ")

    entity = await client.get_entity(user)
    await client.send_message(entity, msg)

async def send_group(client):
    group = input("Group username: ")
    msg = input("Message: ")

    entity = await client.get_entity(group)
    await client.send_message(entity, msg)

async def comment_post(client):
    link = input("Post link: ")
    comment = input("Comment: ")

    link = link.replace("https://t.me/", "").strip("/")
    parts = link.split("/")

    if len(parts) < 2:
        print("Invalid link")
        return

    chat = parts[0]
    msg_id = int(parts[1])

    entity = await client.get_entity(chat)
    await client.send_message(entity, comment, reply_to=msg_id)

# =========================
# AUTO FEATURES
# =========================

async def reaction_all():
    link = input("Post link: ")

    link = link.replace("https://t.me/", "").strip("/")
    parts = link.split("/")

    if len(parts) < 2:
        print("Invalid link")
        return

    chat = parts[0]
    msg_id = int(parts[1])

    for client in clients:
        try:
            emoji = random.choice(REACTIONS)

            entity = await client.get_entity(chat)

            await client(
                functions.messages.SendReactionRequest(
                    peer=entity,
                    msg_id=msg_id,
                    reaction=[ReactionEmoji(emoticon=emoji)]
                )
            )
        except:
            pass

async def join_all():
    link = input("Group link: ")

    for client in clients:
        try:
            entity = await client.get_entity(link)
            await client(JoinChannelRequest(entity))
        except:
            pass

async def leave_all():
    link = input("Group link: ")

    for client in clients:
        try:
            entity = await client.get_entity(link)
            await client(LeaveChannelRequest(entity))
        except:
            pass

# =========================
# MAIN
# =========================

async def main():
    clear()
    banner()

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
8. Reaction (AUTO)
9. Join Group (AUTO)
10. Leave Group (AUTO)
11. Exit
========================
""")

        choice = input("Choose: ").strip()

        if choice == "1":
            await add_account()

        elif choice == "2":
            show_accounts()
            input("Enter...")

        elif choice == "3":
            disable_account()

        elif choice == "4":
            enable_account()

        elif choice == "5":
            c = select_client()
            if c:
                await send_dm(c)

        elif choice == "6":
            c = select_client()
            if c:
                await send_group(c)

        elif choice == "7":
            c = select_client()
            if c:
                await comment_post(c)

        elif choice == "8":
            await reaction_all()

        elif choice == "9":
            await join_all()

        elif choice == "10":
            await leave_all()

        else:
            break

    for c in clients:
        try:
            await c.disconnect()
        except:
            pass


asyncio.run(main())
