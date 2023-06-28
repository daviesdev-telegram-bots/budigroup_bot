from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from dotenv import load_dotenv
from kb import *
import os, json
load_dotenv()

bot_token = os.getenv("bot_token")
from step_handlers import *
from utils import get_balance

owners = json.loads(os.getenv("owners"))
bot = TeleBot(bot_token, parse_mode="HTML")

@bot.message_handler(["start"])
def start(message: Message):
    bot.send_message(message.chat.id, f"Welcome.\n\n🪪Your ID: `{message.chat.id}`\n💰Balance: {get_balance(message.chat.id)}", parse_mode="markdown", reply_markup=Admin.kb)

@bot.message_handler(["admin"], func=lambda msg: msg.chat.id in owners)
def admin(message: Message):
    bot.send_message(message.chat.id, "Welcome to the admin panel.", reply_markup=Admin.kb)


@bot.callback_query_handler(func=lambda msg: msg.data != None)
def callback_query_handler(callback: CallbackQuery):
    message = callback.message
    data = callback.data

    if data.startswith("admin_") and message.chat.id in owners:
        data = data[6:]
        if data == "add_balance":
            bot.send_message(message.chat.id, "Send the <b>Telegram ID</b> of the user you want to add balance to")
            bot.register_next_step_handler(message, get_user_id, "add")

        elif data == "alter_balance":
            bot.send_message(message.chat.id, "Send the <b>Telegram ID</b> of the user you want to change their balance value")
            bot.register_next_step_handler(message, get_user_id, "alter")
        return

print("Started")
bot.infinity_polling()