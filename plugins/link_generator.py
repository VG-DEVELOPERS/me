# (©) Codexbotz

import asyncio
import razorpay
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

from bot import Bot
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode, get_user_balance, add_balance, deduct_balance

razorpay_client = razorpay.Client(
    auth=("rzp_live_Kfvz8iobE8iUZc", "bcPhJQ2pHTaaF94FhWCEl6eD")
)

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(['start', 'users', 'broadcast', 'batch', 'genlink', 'stats']))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
    ])

    await reply_text.edit(f"<b>Here is your link</b>\n\n{link}", reply_markup=reply_markup, disable_web_page_preview=True)

    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(reply_markup)


@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
    ])

    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)


@Bot.on_message(filters.private & filters.command("balance"))
async def check_balance(bot, message: Message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add ₹50", callback_data="add_money_50")]
    ])

    await message.reply_text(f"💰 Your balance: ₹{balance}", reply_markup=keyboard)


@Bot.on_callback_query(filters.regex("add_money_50"))
async def handle_add_money(bot, query: CallbackQuery):
    user_id = query.from_user.id
    payment = razorpay_client.payment_link.create({
        "amount": 5000,
        "currency": "INR",
        "description": f"Add Balance for {user_id}",
        "callback_url": "https://yourdomain.com/payment-success",
        "callback_method": "get",
        "notes": {
            "user_id": str(user_id)
        }
    })
    url = payment['short_url']
    await query.message.reply_text(f"💸 Click to pay ₹50 and add balance:\n{url}")
    
