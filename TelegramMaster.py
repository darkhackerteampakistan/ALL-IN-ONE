import asyncio
import json
import os
import random

from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import ReactionEmoji

# =========================
# NEW UNIFIED STORAGE
# =========================

BASE_DIR = os.path.expanduser("~/TELEGRAM_MASTER")
SESSION_DIR = os.path.join(BASE_DIR, "SESSIONS")
DB_FILE = os.path.join(BASE_DIR, "accounts.json")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

# =========================
# GLOBALS
# =========================

clients = []
accounts = []

REACTIONS = ["👍", "❤️", "🔥", "😂", "😮"]

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
# LOGIN SYSTEM
# =========================

async def login_account(i, acc):
    session_path = os.path.join(SESSION_DIR, acc["session"])

    client = TelegramClient(
        session_path,
        acc["api_id"],
        acc["api_hash"]
    )

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
        print("Auto login OK")

    return client

# =========================
# LOAD ACCOUNTS
# =========================

async def load_all():
    global accounts

    accounts = load_db()

    if not accounts:
        print("No accounts found")
        return

    for i, acc in enumerate(accounts, 1):
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
        print(f"[{i}] {acc['phone']} | {acc['session']}")

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

    print("Reaction sent:", emoji)

# =========================
# JOIN
# =========================

async def join_chat(client, link):
    try:
        entity = await client.get_entity(link)
        await client(JoinChannelRequest(entity))
        print("Joined:", link)

    except UserAlreadyParticipantError:
        print("Already joined")

    except Exception as e:
        print("Join error:", e)

# =========================
# LEAVE
# =========================

async def leave_chat(client, link):
    try:
        entity = await client.get_entity(link)
        await client(LeaveChannelRequest(entity))
        print("Left:", link)

    except Exception as e:
        print("Leave error:", e)

# =========================
# ACTIONS (ALL ACCOUNTS)
# =========================

async def reaction_all(link):
    chat, msg_id = link.split("/")
    msg_id = int(msg_id)

    for i, client in enumerate(clients, 1):
        print(f"\nACCOUNT {i}")
        await send_reaction(client, chat, msg_id)
        await asyncio.sleep(2)

async def join_all(link):
    for i, client in enumerate(clients, 1):
        print(f"\nACCOUNT {i}")
        await join_chat(client, link)
        await asyncio.sleep(2)

async def leave_all(link):
    for i, client in enumerate(clients, 1):
        print(f"\nACCOUNT {i}")
        await leave_chat(client, link)
        await asyncio.sleep(2)

# =========================
# MAIN MENU
# =========================

async def main():
    await load_all()

    while True:
        print("""
========================
1. Add Account
2. Show Accounts
3. Reaction
4. Join Group/Channel
5. Leave Group/Channel
6. Exit
========================
""")

        choice = input("Choose: ").strip()

        if choice == "1":
            await add_account()

        elif choice == "2":
            show_accounts()

        elif choice == "3":
            link = input("chat_id/message_id (e.g. channel/123): ")
            await reaction_all(link)

        elif choice == "4":
            link = input("Join link: ")
            await join_all(link)

        elif choice == "5":
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
