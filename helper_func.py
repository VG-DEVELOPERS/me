import base64
import re
import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

from config import FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, ADMINS
from shortzy import Shortzy
from database.database import user_data

# ------------------------ SUBSCRIPTION CHECK ------------------------

async def is_subscribed(filter, client, update):
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True

    for channel in [FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2]:
        if not channel:
            continue
        try:
            member = await client.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except UserNotParticipant:
            return False
        except Exception:
            return False
    return True

subscribed = filters.create(is_subscribed)

# ------------------------ BALANCE SYSTEM ------------------------

def get_user_balance(user_id: int) -> int:
    user = user_data.get(user_id)
    if not user:
        user_data[user_id] = {"balance": 0}
        return 0
    return user.get("balance", 0)

def add_balance(user_id: int, amount: int):
    if user_id not in user_data:
        user_data[user_id] = {"balance": amount}
    else:
        user_data[user_id]["balance"] = user_data[user_id].get("balance", 0) + amount

def deduct_balance(user_id: int, amount: int) -> bool:
    if user_id not in user_data or user_data[user_id].get("balance", 0) < amount:
        return False
    user_data[user_id]["balance"] -= amount
    return True

# ------------------------ BASE64 ENCODE/DECODE ------------------------

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = base64_bytes.decode("ascii").strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    return string_bytes.decode("ascii")

# ------------------------ MESSAGE HELPERS ------------------------

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages + 200]
        try:
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=temb_ids)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=temb_ids)
        except Exception:
            msgs = []
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id, msg_id = matches.group(1), int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        elif channel_id == client.db_channel.username:
            return msg_id
    return 0

# ------------------------ URL SHORTENER ------------------------

async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    return await shortzy.convert(link)

# ------------------------ TIME HELPERS ------------------------

def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time
    
