from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from dotenv import load_dotenv
from kb import *
import os, json
load_dotenv()

bot_token = os.getenv("bot_token")

from utils import get_balance, get_user, verfiy_float, session, User

owners = json.loads(os.getenv("owners"))
bot = TeleBot(bot_token, parse_mode="HTML")

@bot.message_handler(["start"])
def start(message: Message):
    user = session.query(User).get(str(message.chat.id))
    if not user or not user.is_registered:
        bot.send_message(message.chat.id, f"Welcome {message.chat.username}.\nYour ID: `{message.chat.id}`\nYou don't have an account yet. Click the button below to register", parse_mode="markdown", reply_markup=register_kb)
        return
    bot.send_message(message.chat.id, f"Welcome {message.chat.username}.\n\n🪪Your ID: `{message.chat.id}`\n💰Balance: {user.balance}", parse_mode="markdown", reply_markup=general_kb)

@bot.message_handler(["admin"], func=lambda msg: msg.chat.id in owners)
def admin(message: Message):
    bot.send_message(message.chat.id, "Welcome to the admin panel.", reply_markup=Admin.kb)

@bot.message_handler(["clear"], func=lambda msg: msg.chat.id in owners)
def clear(message: Message):
    for u in session.query(User).all():
        session.delete(u)
    session.commit()
    bot.send_message(message.chat.id, "Cleared")

@bot.message_handler(func=lambda msg: msg.text)
def all_messages(message: Message):
    if message.text == "👤Account":
        start(message)
    elif message.text == "🕑Order History":
        pass
    elif message.text == "📞Support":
        pass

@bot.callback_query_handler(func=lambda msg: msg.data != None)
def callback_query_handler(callback: CallbackQuery):
    message = callback.message
    data = callback.data

    if data == "register":
        user = session.query(User).get(message.chat.id)
        if not user:
            session.add(User(id=message.chat.id))
            session.commit()
        bot.edit_message_text("<b>Your registration has been sent!.</b>\nYou will be notified when you have been approved", message.chat.id, message.id)
        for i in owners:
            bot.send_message(i, f"@{message.chat.username} has sent a membership request\nUser ID: `{message.chat.id}`", parse_mode="markdown", reply_markup=Admin.register_kb(message.chat.id))

    if data.startswith("admin_") and message.chat.id in owners:
        data = data[6:]
        if data == "edit_balance":
            bot.edit_message_text("What kind of editing do you want to do?", reply_markup=Admin.edit_balance_kb(), chat_id=message.chat.id, message_id=message.id)
        
        elif data == "add_balance":
            bot.edit_message_text("Send the <b>Telegram ID</b> of the user you want to add balance to", chat_id=message.chat.id, message_id=message.id)
            bot.register_next_step_handler(message, get_user_id, "add")

        elif data == "alter_balance":
            bot.edit_message_text("Send the <b>Telegram ID</b> of the user you want to change their balance value", chat_id=message.chat.id, message_id=message.id)
            bot.register_next_step_handler(message, get_user_id, "alter")
        
        elif data == "control_membership":
            bot.edit_message_text("Send the <b>Telegram ID</b> of a user", chat_id=message.chat.id, message_id=message.id)
            bot.register_next_step_handler(message, get_user_id, "membership")

        elif data == "ignore_member":
            bot.edit_message_reply_markup(message.chat.id, message.id, reply_markup=InlineKeyboardMarkup())

        elif data.startswith("register_user"):
            _, uid = data.split(":")
            user = get_user(uid)
            user.is_registered = True
            user.is_disabled = not user.is_disabled
            session.commit()
            bot.send_message(uid, "✅Your membership has been accepted by the admin", reply_markup=general_kb)
            bot.edit_message_text(f"You have turned accepted @{bot.get_chat(user.id)} 's membership", message.chat.id, message.id, reply_markup=Admin.back_btn())
        
        elif data.startswith("control_membership"):
            _, uid = data.split(":")
            user = get_user(uid)
            user.is_disabled = not user.is_disabled
            session.commit()
            if user.is_disabled:
                text = "⛔Your membership has been suspended by the admin"
            else:
                text = "✅Your membership has been accepted by the admin"
            bot.send_message(uid, text, reply_markup=general_kb)
            bot.edit_message_text(f"You have turned {'off' if user.is_disabled else 'on'} @{bot.get_chat(user.id)} 's membership", message.chat.id, message.id, reply_markup=Admin.back_btn())

        elif data == "registrations":
            bot.edit_message_text("")

        elif data == "home":
            bot.edit_message_text("Welcome to the admin panel.", reply_markup=Admin.kb, chat_id=message.chat.id, message_id=message.id)
        return

def get_user_id(message, mode):
    if not message.text:
        return
    try:
        user = bot.get_chat(message.text)
    except:
        bot.send_message(message.chat.id, "Incorrect user ID. Please make sure the user has chatted with the bot before")
        bot.register_next_step_handler(message, get_user_id, mode)
        return
    u = get_user(user.id)
    if mode == "membership":
        bot.send_message(message.chat.id, f"User ID: `{user.id}`\nUsername: {user.username}\nBalance: {u.balance}\nMembership: {'⛔Inactive' if u.is_disabled else '✅Active'}", reply_markup=Admin.Membership.edit_membership(u.is_disabled, user.id))
        return

    data = {"add": {
        "text": "What amount do you want to add to @"+user.username,
        "func": add_balance
    },
    "alter":{
        "text":"What amount do you want to add to @"+user.username,
        "func": alter_balance
    },}
    bot.send_message(message.chat.id, data[mode]["text"])
    bot.register_next_step_handler(message, data[mode]["func"], u)

def add_balance(message, user):
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user)
        return
    user.balance += amt
    session.commit()
    username = bot.get_chat(user.id).username
    bot.send_message(message.chat.id, f"You have added {amt} to {username}\nCurrent balance: {user.balance}", reply_markup=Admin.back_btn("edit_balance"))
    bot.send_message(user.id, f"{amt} has been added to your balance\nCurrent balance: {user.balance}")

def alter_balance(message, user):
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user)
        return
    user.balance = amt
    session.commit()
    username = bot.get_chat(user.id).username
    bot.send_message(message.chat.id, f"You overwritten {username}'s balance to {amt}", reply_markup=Admin.back_btn("edit_balance"))
    bot.send_message(user.id, f"Your balance has been updated by the admin\nCurrent balance: {user.balance}")

print("Started")
bot.infinity_polling()