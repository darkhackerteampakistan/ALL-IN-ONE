import asyncio
import json
import os
import random

from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import ReactionEmoji

# =========================
# STORAGE
# =========================

BASE_DIR = os.path.expanduser("~/TELEGRAM_MASTER_UI")
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

def banner():
    print("""
=====================================
     TELEGRAM AUTOMATION TOOL
=====================================
   Developer : Rifat Tools Lab
   Version   : 2.0 UI Edition
   Features  : Reaction | Join | Leave
                Multi Account Manager
=====================================
""")


def loading():
    print("Loading system...\n")

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
            pwd = input("2FA: ").strip()
            await client.sign_in(password=pwd)

        print("Session saved")

    else:
        print("Auto login")

    return client

# =========================
# LOAD ACCOUNTS (ACTIVE ONLY)
# =========================

async def load_all():
    global accounts

    accounts = load_db()

    if not accounts:
        print("No accounts found")
        return

    active_accounts = [a for a in accounts if a.get("active", True)]

    print(f"\nLoading {len(active_accounts)} ACTIVE accounts...\n")

    for i, acc in enumerate(active_accounts, 1):
        client = await login_account(i, acc)
        clients.append(client)

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
# SHOW ACCOUNTS
# =========================

def show_accounts():
    print("\n=== ACCOUNTS ===")

    for i, acc in enumerate(accounts, 1):
        status = "ACTIVE" if acc.get("active", True) else "DISABLED"
        print(f"[{i}] {status} | {acc['phone']}")

# =========================
# DISABLE / ENABLE
# =========================

def disable_account():
    show_accounts()
    idx = int(input("Disable account #: ")) - 1

    if 0 <= idx < len(accounts):
        accounts[idx]["active"] = False
        save_db(accounts)
        print("Account disabled")


def enable_account():
    show_accounts()
    idx = int(input("Enable account #: ")) - 1

    if 0 <= idx < len(accounts):
        accounts[idx]["active"] = True
        save_db(accounts)
        print("Account enabled")

# =========================
# REACTION
# =========================

async def send_reaction(client, chat, msg_id):
    emoji = random.choice(REACTIONS)

    await client(functions.messages.SendReactionRequest(
        peer=chat,
        msg_id=msg_id,
        reaction=[ReactionEmoji(emoticon=emoji)]
    ))

    print("Reaction:", emoji)

# =========================
# JOIN / LEAVE
# =========================

async def join_chat(client, link):
    try:
        entity = await client.get_entity(link)
        await client(JoinChannelRequest(entity))
        print("Joined:", link)
    except Exception as e:
        print("Join error:", e)


async def leave_chat(client, link):
    try:
        entity = await client.get_entity(link)
        await client(LeaveChannelRequest(entity))
        print("Left:", link)
    except Exception as e:
        print("Leave error:", e)

# =========================
# ACTIONS (ONLY ACTIVE ACCOUNTS)
# =========================

async def reaction_all(link):
    chat, msg_id = link.split("/")
    msg_id = int(msg_id)

    for i, client in enumerate(clients, 1):
        await send_reaction(client, chat, msg_id)
        await asyncio.sleep(2)


async def join_all(link):
    for client in clients:
        await join_chat(client, link)
        await asyncio.sleep(2)


async def leave_all(link):
    for client in clients:
        await leave_chat(client, link)
        await asyncio.sleep(2)

# =========================
# MAIN
# =========================

async def main():
    banner()
    loading()

    await load_all()

    while True:
        print("""
========================
1. Add Account
2. Show Accounts
3. Disable Account
4. Enable Account
5. Reaction
6. Join Group/Channel
7. Leave Group/Channel
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
            link = input("chat/msg (channel/123): ")
            await reaction_all(link)

        elif choice == "6":
            link = input("Join link: ")
            await join_all(link)

        elif choice == "7":
            link = input("Leave link: ")
            await leave_all(link)

        else:
            break

    for c in clients:
        try:
            await c.disconnect()
        except:
            pass


asyncio.run(main())
