from bot import bot
from models import session
from utils import verfiy_float, get_user

def get_user_id(message, mode):
    if not message.text:
        return
    try:
        user = bot.get_chat(message.text)
    except:
        bot.send_message(
            message.chat.id, "Incorrect user ID. Please make sure the user has chatted with the bot before")
        return
    data = {"add": {
        "text": "What amount do you want to add to @"+user.username,
        "func": add_balance
    },
    "alter":{
        "text":"What amount do you want to add to @"+user.username,
        "func": alter_balance
    }}
    bot.send_message(message.chat.id, data[mode]["text"])
    bot.register_next_step_handler(message, data["mode"]["func"], user.id)

def add_balance(message, user_id):
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user_id)
        return
    get_user(user_id).balance += amt
    session.commit()

def alter_balance(message, user_id):
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user_id)
        return
    get_user(user_id).balance = amt
    session.commit()

