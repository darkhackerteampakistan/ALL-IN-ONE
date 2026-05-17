import os
import json
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

BASE_DIR = "/storage/emulated/0/TELEGRAM_CONTROL_PANEL"
SESSION_DIR = os.path.join(BASE_DIR, "sessions")
DB_FILE = os.path.join(BASE_DIR, "accounts.json")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

accounts = []
clients = []
default_account = None


# ================= DB =================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ================= LOGIN =================
async def login(acc):
    session_path = os.path.join(SESSION_DIR, acc["session"])

    client = TelegramClient(session_path, acc["api_id"], acc["api_hash"])
    await client.connect()

    if not await client.is_user_authorized():
        print("\nLOGIN:", acc["phone"])
        await client.send_code_request(acc["phone"])
        code = input("OTP: ")

        try:
            await client.sign_in(acc["phone"], code)
        except SessionPasswordNeededError:
            pwd = input("2FA Password: ")
            await client.sign_in(password=pwd)

    return client


# ================= INIT =================
async def init():
    global accounts, clients

    accounts = load_db()

    for acc in accounts:
        if acc.get("active", True):
            try:
                clients.append(await login(acc))
            except:
                pass


# ================= UI =================
def show_accounts():
    print("\n=== ACCOUNTS ===")
    for i, a in enumerate(accounts, 1):
        status = "ACTIVE" if a.get("active", True) else "DISABLED"
        print(f"[{i}] {status} | {a['phone']}")


# ================= DEFAULT =================
def set_default():
    global default_account

    show_accounts()
    i = int(input("Select default #: ")) - 1
    default_account = accounts[i]["phone"]
    print("Default set:", default_account)


def get_default_client():
    if not default_account:
        set_default()

    for c, a in zip(clients, accounts):
        if a["phone"] == default_account:
            return c
    return None


# ================= ACTIONS =================
async def send_dm():
    c = get_default_client()
    user = input("User: ")
    msg = input("Message: ")

    entity = await c.get_entity(user)
    await c.send_message(entity, msg)


async def send_group():
    c = get_default_client()
    group = input("Group: ")
    msg = input("Message: ")

    entity = await c.get_entity(group)
    await c.send_message(entity, msg)


async def reply_by_link():
    c = get_default_client()

    link = input("Post link: ").replace("https://t.me/", "")
    msg = input("Reply: ")

    chat, mid = link.split("/")
    entity = await c.get_entity(chat)

    await c.send_message(entity, msg, reply_to=int(mid))


# ================= REACTION =================
async def reaction():
    c = get_default_client()

    link = input("Post link: ").replace("https://t.me/", "")
    chat, mid = link.split("/")

    entity = await c.get_entity(chat)

    await c(
        SendReactionRequest(
            peer=entity,
            msg_id=int(mid),
            reaction=[ReactionEmoji(emoticon="👍")]
        )
    )

    print("Reaction sent")


# ================= JOIN =================
async def join_group():
    c = get_default_client()

    link = input("Group link: ")

    entity = await c.get_entity(link)
    await c(JoinChannelRequest(entity))

    print("Joined")


# ================= LEAVE =================
async def leave_group():
    c = get_default_client()

    link = input("Group link: ")

    entity = await c.get_entity(link)
    await c(LeaveChannelRequest(entity))

    print("Left")


# ================= MAIN =================
async def main():
    await init()

    while True:
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
10. Join Group (Single Account)
11. Leave Group (Single Account)
12. Exit
========================
""")

        ch = input("Choose: ")

        if ch == "2":
            show_accounts()

        elif ch == "5":
            set_default()

        elif ch == "6":
            await send_dm()

        elif ch == "7":
            await send_group()

        elif ch == "8":
            await reply_by_link()

        elif ch == "9":
            await reaction()

        elif ch == "10":
            await join_group()

        elif ch == "11":
            await leave_group()

        else:
            break

    for c in clients:
        try:
            await c.disconnect()
        except:
            pass


asyncio.run(main())
