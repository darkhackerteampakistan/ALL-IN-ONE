import asyncio
import json
import os
import random
import time

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

REACTIONS = ["👍", "❤️", "🔥", "😂", "😮"]

# =========================
# UI
# =========================

def clear():
    os.system("clear")

def banner():
    print("""
====================================
 TELEGRAM CONTROL PANEL (SAFE AUTO)
====================================
DM | GROUP | REPLY | JOIN | LEAVE | STORY ASSIST
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

    seen = set()
    unique = []

    for acc in accounts:
        if acc["phone"] in seen:
            continue
        seen.add(acc["phone"])
        unique.append(acc)

    accounts = unique
    save_db(accounts)

    for i, acc in enumerate(accounts, 1):
        if acc.get("active", True):
            try:
                c = await login_account(i, acc)
                clients.append(c)
            except Exception as e:
                print("Login error:", e)

# =========================
# ACCOUNT VIEW
# =========================

def show_accounts():
    print("\n=== ACCOUNTS ===")
    for i, a in enumerate(accounts, 1):
        status = "ACTIVE" if a.get("active", True) else "DISABLED"
        print(f"[{i}] {status} | {a['phone']}")

# =========================
# CLIENT ACTIVE LIST
# =========================

def active_pairs():
    return [(c, a) for c, a in zip(clients, accounts) if a.get("active", True)]

# =========================
# RESOLVE
# =========================

async def resolve_entity(client, target):
    target = str(target).replace("https://t.me/", "").replace("@", "")
    try:
        return await client.get_entity(target)
    except:
        return None

# =========================
# SAFE SEND
# =========================

async def safe_send(client, entity, msg):
    try:
        return await client.send_message(entity, msg)
    except Exception as e:
        print("Send error:", e)

# =========================
# DM
# =========================

async def send_dm():
    show_accounts()
    c_index = int(input("Select account #: ")) - 1

    if c_index < 0 or c_index >= len(clients):
        return

    c = clients[c_index]
    target = input("User: ")
    msg = input("Message: ")

    entity = await resolve_entity(c, target)
    if not entity:
        print("Not found")
        return

    await safe_send(c, entity, msg)
    print("DM sent")

# =========================
# STORY ASSISTANT MODE (SAFE AUTO)
# =========================

async def story_assistant():
    link = input("Story/Post link: ").strip()

    print("""
Choose reaction mode:
1. 👍
2. ❤️
3. 🔥
4. 😂
5. 😮
6. Random per account
""")

    mode = input("Choice: ").strip()

    parts = link.replace("https://t.me/", "").strip("/").split("/")

    if len(parts) < 2:
        print("Invalid link")
        return

    chat = parts[0]
    msg_id = int(parts[1])

    pairs = active_pairs()

    print("\n=== STARTING SAFE AUTO ASSISTANT ===\n")

    for idx, (client, acc) in enumerate(pairs, 1):

        if mode == "1":
            reaction = "👍"
        elif mode == "2":
            reaction = "❤️"
        elif mode == "3":
            reaction = "🔥"
        elif mode == "4":
            reaction = "😂"
        elif mode == "5":
            reaction = "😮"
        else:
            reaction = random.choice(REACTIONS)

        try:
            entity = await client.get_entity(chat)

            await client(functions.messages.SendReactionRequest(
                peer=entity,
                msg_id=msg_id,
                reaction=[ReactionEmoji(emoticon=reaction)]
            ))

            print(f"[{idx}] {acc['phone']} → {reaction} ✔ SENT")

        except Exception as e:
            print(f"[{idx}] {acc['phone']} → FAILED: {e}")

        time.sleep(1.5)  # SAFE DELAY

# =========================
# JOIN / LEAVE
# =========================

async def join_all():
    link = input("Group link: ")
    for c, _ in active_pairs():
        try:
            entity = await c.get_entity(link)
            await c(JoinChannelRequest(entity))
            print("Joined")
        except:
            pass

async def leave_all():
    link = input("Group link: ")
    for c, _ in active_pairs():
        try:
            entity = await c.get_entity(link)
            await c(LeaveChannelRequest(entity))
            print("Left")
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
1. Show Accounts
2. Send DM
3. Story Assistant Mode (SAFE AUTO)
4. Join Group
5. Leave Group
6. Exit
========================
""")

        ch = input("Choose: ")

        if ch == "2":
            await send_dm()

        elif ch == "3":
            await story_assistant()

        elif ch == "4":
            await join_all()

        elif ch == "5":
            await leave_all()

        else:
            break

    for c in clients:
        try:
            await c.disconnect()
        except:
            pass

asyncio.run(main())
