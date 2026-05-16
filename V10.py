import asyncio
import json
import os
import random

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

clients = []
accounts = []
selected_client = None

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
MANUAL: DM | Group | Reply
====================================
""")

# =========================
# DATABASE
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
# ACCOUNT SYSTEM
# =========================

def show_accounts():
    print("\n=== ACCOUNT LIST ===")

    if not accounts:
        print("No accounts found")
        return

    for i, acc in enumerate(accounts, 1):
        status = "ACTIVE" if acc.get("active", True) else "DISABLED"
        print(f"[{i}] {status} | {acc['phone']}")

async def add_account():
    phone = input("PHONE: ").strip()

    if any(a["phone"] == phone for a in accounts):
        print("Already exists!")
        return

    acc = {
        "session": f"acc{len(accounts)+1}",
        "api_id": int(input("API ID: ")),
        "api_hash": input("API HASH: "),
        "phone": phone,
        "active": True
    }

    accounts.append(acc)
    save_db(accounts)

    client = await login_account(len(accounts), acc)
    clients.append(client)

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
# CLIENT SELECT
# =========================

def get_client():
    global selected_client

    if selected_client:
        return selected_client

    show_accounts()
    i = int(input("Select account #: ")) - 1
    selected_client = clients[i]
    return selected_client

# =========================
# SAFE SEND
# =========================

async def safe_send(client, entity, msg, reply_id=None):
    try:
        if reply_id:
            return await client.send_message(entity, msg, reply_to=reply_id)
        return await client.send_message(entity, msg)
    except Exception as e:
        print("Send failed:", e)
        return None

# =========================
# SMART RESOLVER (IMPORTANT)
# =========================

async def resolve_entity(client, target):
    target = str(target).strip()

    target = target.replace("https://t.me/", "").replace("@", "")

    try:
        return await client.get_entity(target)
    except:
        pass

    try:
        if target.isdigit():
            return await client.get_entity(int(target))
    except:
        pass

    return None

# =========================
# MANUAL FEATURES
# =========================

async def send_dm():
    c = get_client()

    target = input("User (username / ID / phone): ")
    msg = input("Message: ")

    entity = await resolve_entity(c, target)

    if not entity:
        print("User not found")
        return

    await safe_send(c, entity, msg)
    print("Message sent")

async def send_group():
    c = get_client()

    target = input("Group/Channel: ")
    msg = input("Message: ")

    entity = await resolve_entity(c, target)

    if not entity:
        print("Group not found")
        return

    await safe_send(c, entity, msg)
    print("Message sent")

async def reply_by_link():
    c = get_client()

    link = input("Message link: ")
    msg = input("Reply message: ")

    link = link.replace("https://t.me/", "").strip("/")
    parts = link.split("/")

    if len(parts) < 2:
        print("Invalid link")
        return

    chat = parts[0]
    msg_id = int(parts[1])

    entity = await resolve_entity(c, chat)

    if not entity:
        print("Chat not found")
        return

    await safe_send(c, entity, msg, msg_id)
    print("Reply sent")

# =========================
# AUTO FEATURES
# =========================

def active_clients():
    return [c for c, a in zip(clients, accounts) if a.get("active", True)]

async def reaction_all():
    link = input("Post link: ")

    link = link.replace("https://t.me/", "").strip("/")
    chat, msg_id = link.split("/")

    for client in active_clients():
        try:
            entity = await client.get_entity(chat)

            await client(
                functions.messages.SendReactionRequest(
                    peer=entity,
                    msg_id=int(msg_id),
                    reaction=[ReactionEmoji(emoticon=random.choice(REACTIONS))]
                )
            )
        except:
            pass

async def join_all():
    link = input("Group link: ")

    for client in active_clients():
        try:
            entity = await client.get_entity(link)
            await client(JoinChannelRequest(entity))
        except:
            pass

async def leave_all():
    link = input("Group link: ")

    for client in active_clients():
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
7. Reply by Link
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

        elif choice == "3":
            disable_account()

        elif choice == "4":
            enable_account()

        elif choice == "5":
            await send_dm()

        elif choice == "6":
            await send_group()

        elif choice == "7":
            await reply_by_link()

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
