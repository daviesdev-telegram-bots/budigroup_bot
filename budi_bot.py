from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from kb import *
import os, json
from smsactivate.api import SMSActivateAPI
from dotenv import load_dotenv
load_dotenv()

bot_token = os.getenv("bot_token")
from utils import get_balance, get_user, verfiy_float, session, User, services, countries, Order, load_file, save_file

sa = SMSActivateAPI(os.getenv("SMS_ACTIVATE_APIKEY"))
owners = json.loads(os.getenv("owners"))
bot = TeleBot(bot_token, parse_mode="HTML")
support = "https://t.me/daviesdev"

@bot.message_handler(["start"])
def start(message: Message):
    user = session.query(User).get(str(message.chat.id))
    if not user or not user.is_registered:
        bot.send_message(message.chat.id, f"Welcome {message.chat.username}.\nYour ID: `{message.chat.id}`\nYou don't have an account yet. Click the button below to register", parse_mode="markdown", reply_markup=register_kb)
        return
    bot.send_message(message.chat.id, f"Welcome {message.chat.username}.\n\n🪪Your ID: `{message.chat.id}`\n💰Balance: {user.balance} points", parse_mode="markdown", reply_markup=general_kb)

@bot.message_handler(["admin"], func=lambda msg: msg.chat.id in owners)
def admin(message: Message):
    bot.send_message(message.chat.id, "Welcome to the admin panel.", reply_markup=Admin.kb)

# @bot.message_handler(["clear"], func=lambda msg: msg.chat.id in owners)
# def clear(message: Message):
#     for u in session.query(User).all():
#         session.delete(u)
#     session.commit()
#     bot.send_message(message.chat.id, "Cleared")

@bot.message_handler(func=lambda msg: msg.text)
def all_messages(message: Message):
    if message.text == "👤Account":
        start(message)
    elif message.text == "🤖Order Service":
        bot.send_message(message.chat.id, "What service do you want to order?.\nIf the service is not listed here, just click \"🔍Search\"", reply_markup=services_kb(list(services)[:20]))
    elif message.text == "🛍️Order Goods":
        bot.send_message(message.chat.id, "What kind of good do you want to buy?", reply_markup=goods_types_kb)
    elif message.text == "🕑Order History":
        pass
    elif message.text == "📞Support":
        pass

@bot.callback_query_handler(func=lambda msg: msg.data != None)
def callback_query_handler(callback: CallbackQuery):
    message = callback.message
    data = callback.data
    bot.clear_reply_handlers(message)

    if data == "register":
        user = get_user(message.chat.id)
        bot.edit_message_text("<b>Your registration has been sent!.</b>\nYou will be notified when you have been approved", message.chat.id, message.id)
        for i in owners:
            bot.send_message(i, f"@{message.chat.username} has sent a membership request\nUser ID: `{message.chat.id}`", parse_mode="markdown", reply_markup=Admin.register_kb(message.chat.id))

    elif data == "search_service":
        bot.edit_message_text("Send the first letters of the service you want to search", message.chat.id, message.id, reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, search_service)

    elif data == "order_goods":
        bot.edit_message_text("What kind of good do you want to buy?", message.chat.id, message.id, reply_markup=goods_types_kb)

    elif data == "order_service":
        bot.edit_message_text("What service do you want to order?.\nIf the service is not listed here, just click \"🔍Search\"", message.chat.id,message.id, reply_markup=services_kb(list(services)[:20]))

    elif data.startswith("s_"):
        data = data[2:]
        res = sa.getTopCountriesByService(data)
        cs = []
        for i in res:
            country_number = str(res[i]['country'])
            cs.append((countries[country_number], country_number))
        cs.sort()
        text = "\n".join([f"/{country_number} {country_name}" for country_name, country_number in cs])
        text = "Choose your country by tapping the numbers on the left\n\n"+text
        bot.edit_message_text(text, message.chat.id, message.id, reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, select_country, data, res)

    elif data.startswith("purchase_smsactivate"):
        _, service, country = data.split(":")
        number_data = sa.getNumberV2(service, freePrice=True, maxPrice=10, verification=True, country=country)
        if number_data.get("activationId"):
            activation_id = number_data["activationId"]
            phone_number = number_data["phoneNumber"]
            country = number_data["countryCode"]
            user = get_user(message.chat.id)
            user.balance -= float(number_data["activationCost"])*4
            order = Order(activation_id=activation_id, phone_number=phone_number, country_code=country, service=service, type="service", user=str(message.chat.id))
            session.add(order)
            session.commit()
            bot.edit_message_text(f"Purchase Successful\n\nActivation ID: `{activation_id}`\nPhone: `{phone_number}`\nCountry: {countries[country]}\nService: {service}", parse_mode="markdown")
        else:
            bot.edit_message_text("Something went wrong. Please try again later.", message.chat.id, message.id, reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))

    elif data.startswith("good"):
        good = data.split(":")[-1]
        prices = load_file("prices.json")
        if good == "ig":
            bot.edit_message_text(f"<b>Purchase Instagram Account</b>\n\nPrice: <b>{prices['instagram']} points</b>", message.chat.id, message.id, reply_markup=buy_good_kb("instagram"))
        elif good == "vcc":
            bot.edit_message_text(f"<b>Purchase VCC</b>\n\nPrice: <b>{prices['vcc']} points</b>", message.chat.id, message.id, reply_markup=buy_good_kb(good))

    elif data.startswith("buy_good"):
        _, good = data.split(":")
        prices = load_file("prices.json")
        user = get_user(message.chat.id)
        if user.balance < prices[good]:
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Top up Points", support)).add(back_btn("order_goods"))
            bot.edit_message_text(f"Not enough points to purchase this good\nYou need additional <b>{prices[good]-user.balance} points</b> to pay for this good", message.chat.id, message.id, reply_markup=kb)
            return
        file = load_file(good+".json")
        if len(file) <= 0:
            bot.edit_message_text(f"Out of stock.\nPlease, check again later", message.chat.id, message.id, reply_markup=kb)
            return
        delivery_data = file[0]
        file.pop(0)
        user.balance -= prices[good]
        order = Order(text=json.dumps(delivery_data), type="goods", user=user.id)
        session.add(order)
        session.commit()
        save_file(file, good+".json")
        if good == "instagram":
            text = "User: {}\nPassword: {}\nCookies: {}".format(*delivery_data)
        else:
            text = "\n".join(delivery_data)
        bot.edit_message_text("<b>Purchase Successful</b>\n\n"+text, message.chat.id, message.id)

    elif data == "back":
        pass

    if data.startswith("admin_") and message.chat.id in owners:
        data = data[6:]
        if data == "edit_balance":
            bot.edit_message_text("What kind of editing do you want to do?", reply_markup=Admin.edit_balance_kb, chat_id=message.chat.id, message_id=message.id)
        
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
            bot.edit_message_text(f"You have accepted @{bot.get_chat(user.id).username} 's membership", message.chat.id, message.id, reply_markup=Admin.back_btn())
        
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
            pass

        elif data == "edit_goods":
            bot.edit_message_text("Select what good you want to edit", message.chat.id, message.id, reply_markup=Admin.edit_goods_kb)
        
        elif data.startswith("add_goods"):
            good = data.split(":")[-1]
            bot.edit_message_text(f"Send the a .txt file for the new {good} goods", message.chat.id, message.id, reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:"+good)))
            bot.register_next_step_handler(message, add_goods, good)

        elif data.startswith("price_change_goods"):
            good = data.split(":")[-1]
            bot.edit_message_text(f"Send the price you want to set for "+good+" goods", message.chat.id, message.id, reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:"+good)))
            bot.register_next_step_handler(message, change_goods_price, good)

        elif data.startswith("edit"):
            good = data.split(":")[-1]
            bot.edit_message_text("What property of "+good+" do you want to edit?", message.chat.id, message.id, reply_markup=Admin.edit_good_kb(good))

        elif data == "home":
            bot.edit_message_text("Welcome to the admin panel.", reply_markup=Admin.kb, chat_id=message.chat.id, message_id=message.id)
        return

def change_goods_price(message:Message, good:str):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message")
        bot.register_next_step_handler(message, change_goods_price, good)
        return
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, change_goods_price, good)
        return
    file = load_file("prices.json")
    file[good.lower()] = amt
    save_file(file, "prices.json")
    bot.send_message(message.chat.id, "The price for "+good+" goods has been set to "+str(amt)+" points", reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:"+good)))

def add_goods(message: Message, good:str):
    if is_cancel(message): return
    if not message.document:
        bot.send_message(message.chat.id, "You need to send a document")
        bot.register_next_step_handler(message, add_goods, good)
        return
    
    file = bot.download_file(bot.get_file(message.document.file_id).file_path)
    filename = good.lower()+".json"
    kb = InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:"+good))
    sep = ":" if good.lower() == "instagram" else "|"
    try:
        data = []
        for line in file.decode().split("\n"):
            if len(line.split(sep)) < 2:
                continue
            user, password, cookies, *other = line.split(sep)
            data.append((user, password, cookies[1:] if sep == ":" else cookies, *other))
        f = load_file(filename)
        f.extend(data)
        save_file(f, filename)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "This file has a fault and cannot be adcded.", reply_markup=kb)
    else:
        bot.send_message(message.chat.id, "This file has been added successfully in "+good, reply_markup=kb)

def get_user_id(message, mode):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message")
        bot.register_next_step_handler(message, get_user_id, mode)
        return
    try:
        user = bot.get_chat(message.text)
    except:
        bot.send_message(message.chat.id, "Incorrect user ID. Please make sure the user has chatted with the bot before")
        bot.register_next_step_handler(message, get_user_id, mode)
        return
    u = get_user(user.id)
    if mode == "membership":
        bot.send_message(message.chat.id, f"User ID: `{user.id}`\nUsername: {user.username}\nBalance: {u.balance} points\nMembership: {'⛔Inactive' if u.is_disabled else '✅Active'}", reply_markup=Admin.Membership.edit_membership(u.is_disabled, user.id))
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
    if is_cancel(message): return
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user)
        return
    user.balance += amt
    session.commit()
    username = bot.get_chat(user.id).username
    bot.send_message(message.chat.id, f"You have added {amt} to {username}\nCurrent balance: {user.balance} points", reply_markup=Admin.back_btn("edit_balance"))
    bot.send_message(user.id, f"{amt} has been added to your balance\nCurrent balance: {user.balance} points")

def alter_balance(message, user):
    if is_cancel(message): return
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user)
        return
    user.balance = amt
    session.commit()
    username = bot.get_chat(user.id).username
    bot.send_message(message.chat.id, f"You have overwritten {username}'s balance to {amt} points", reply_markup=Admin.back_btn("edit_balance"))
    bot.send_message(user.id, f"Your balance has been updated by the admin\nCurrent balance: {user.balance} points")

def search_service(message: Message):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message", reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, search_service)
        return
    search_list = []
    if json.dumps(services).lower().find(message.text.lower()) != -1:
        for i in services:
            if i.lower().startswith(message.text.lower()):
                search_list.append(i)
    bot.send_message(message.chat.id, "Search results", reply_markup=services_kb(search_list))

def is_cancel(message):
    if message.text == "/start":
        bot.clear_reply_handlers(message)
        start(message)
        return True 
    if message.text == "/admin":
        bot.clear_reply_handlers(message)
        admin(message)
        return True
    return

def select_country(message:Message, service:str, response:dict):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message", reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, select_country, service, response)
        return
    if message.text.startswith("/"):
        country = message.text[1:]
    
    if not country.isdigit() or not countries.get(country):
        bot.send_message(message.chat.id, "Invalid Country code, try again")
        bot.register_next_step_handler(message, select_country, service, response)
        return
    for i in services:
        if services[i] == service:
            service = i
            break
    for i in response:
        if response[i]["country"] == int(country):
            price = response[i]["retail_price"]
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Purchase", callback_data=f"purchase_smsactivate:{service}:{country}"))
            kb.add(back_btn("order_service"))
            bot.send_message(message.chat.id, f"Order summary:\n\nService: <b>{service}</b>\nCountry: <b>{countries[country]}</b>\nPrice: <b>{price*4} points</b>", reply_markup=kb)
            break

print("Started")
bot.infinity_polling()