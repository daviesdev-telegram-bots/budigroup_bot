import json
import os

from dotenv import load_dotenv
from smsactivate.api import SMSActivateAPI
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from kb import *
from utils import get_user, verfiy_float, session, User, services, countries, Order, load_file, save_file, \
    activation_status_response_cleaner

load_dotenv()

bot_token = os.getenv("bot_token")

sa = SMSActivateAPI(os.getenv("SMS_ACTIVATE_APIKEY"))
owners = json.loads(os.getenv("owners"))
bot = TeleBot(bot_token, parse_mode="HTML")
support = "https://t.me/AboAhmed901"


@bot.message_handler(["start"])
def start(message: Message):
    user = session.query(User).get(str(message.chat.id))
    if not user or not user.is_registered:
        bot.send_message(message.chat.id,
                         f"Welcome 👋\n🪪Your ID: `{message.chat.id}`\nYou don't have an account yet. Click the button below to register📝",
                         parse_mode="markdown", reply_markup=register_kb)
        return
    bot.send_message(message.chat.id, f"Welcome 👋\n\n🪪Your ID: `{message.chat.id}`\n💰Balance: {user.balance} points",
                     parse_mode="markdown", reply_markup=general_kb)


@bot.message_handler(["admin"], func=lambda msg: msg.chat.id in owners)
def admin(message: Message):
    bot.send_message(message.chat.id, "Welcome to the admin panel.", reply_markup=Admin.kb)


@bot.message_handler(func=lambda msg: msg.text)
def all_messages(message: Message):
    if get_user(message.chat.id).is_disabled:
        bot.send_message(message.chat.id, "Your account has been suspended.\n\nPlease contact support for more info",
                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Contact", support)))
    elif message.text == "👤Account":
        start(message)
    elif message.text == "🤖Order Service":
        bot.send_message(message.chat.id,
                         "What service do you want to order?.\nIf the service is not listed here, just click \"🔍Search\"",
                         reply_markup=services_kb(list(services)[:20]))
    elif message.text == "🛍️Order Goods":
        bot.send_message(message.chat.id, "What kind of good do you want to buy?", reply_markup=goods_types_kb())
    elif message.text == "🕑Order History":
        orders = session.query(Order).filter_by(user=str(message.chat.id)).order_by(Order.time_created.desc()).limit(
            5).all()
        arr = []
        for order in orders:
            if order.type == "service":
                arr.append(
                    f"<b>SMS Service - {order.time_created.strftime('%I:%M %p %d %b, %Y')}</b>\n/{order.id} +{order.phone_number} - {countries[order.country_code]}")
            elif order.type == "goods":
                arr.append(
                    f"<b>{order.service} - {order.time_created.strftime('%I:%M %p %d %b, %Y')}</b>\n{order.text}")
        text = "\n".join(arr)
        bot.send_message(message.chat.id, "<b>Check out your previous orders here</b>\n\n" + text)
        bot.register_next_step_handler(message, lookup_order)
    elif message.text == "📞Support":
        bot.send_message(message.chat.id, "Click the button below to contact support",
                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Contact", support)))


@bot.callback_query_handler(func=lambda msg: msg.data is not None)
def callback_query_handler(callback: CallbackQuery):
    message = callback.message
    data = callback.data
    bot.clear_reply_handlers(message)

    if data == "register":
        get_user(message.chat.id)
        bot.edit_message_text(
            "<b>Your registration has been sent✅!.</b>\nYou will be notified when you have been approved",
            message.chat.id, message.id)
        for i in owners:
            bot.send_message(i, f"`{message.chat.id}` has sent a membership request", parse_mode="markdown",
                             reply_markup=Admin.register_kb(message.chat.id))

    elif data == "search_service":
        bot.edit_message_text("Send the first letters of the service you want to search🔍", message.chat.id, message.id,
                              reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, search_service)

    elif data == "order_goods":
        bot.edit_message_text("What kind of goods do you want to buy?", message.chat.id, message.id,
                              reply_markup=goods_types_kb())

    elif data == "order_service":
        bot.edit_message_text(
            "What service do you want to order?.\nIf the service is not listed here, just click \"🔍Search\"",
            message.chat.id, message.id, reply_markup=services_kb(list(services)[:20]))

    elif data == "order_history":
        orders = session.query(Order).filter_by(user=str(message.chat.id)).order_by(Order.time_created.desc()).limit(
            5).all()
        arr = []
        for order in orders:
            if order.type == "service":
                arr.append(
                    f"<b>SMS Service - {order.time_created.strftime('%I:%M %p %d %b, %Y')}</b>\n/{order.id} +{order.phone_number} - {countries[order.country_code]}")
            elif order.type == "goods":
                arr.append(
                    f"<b>{order.service} - {order.time_created.strftime('%I:%M %p %d %b, %Y')}</b>\n{order.text}")
        text = "\n".join(arr)
        bot.edit_message_text("<b>Check out your previous orders here</b>\n\n" + text, message.chat.id, message.id)
        bot.register_next_step_handler(message, lookup_order)

    elif data.startswith("s_"):
        data = data[2:]
        res = sa.getTopCountriesByService(data)
        cs = []
        n = 0
        for i in res:
            if n >= 10:
                break
            country_number = str(res[i]['country'])
            cs.append((countries[country_number], country_number, res[i]['retail_price']))
            n += 1
        text = "\n".join(
            f"/{country_number} {country_name} - <i>${price}</i>" for country_name, country_number, price in cs)
        text = "Choose your country by tapping the numbers on the left\n\n" + text
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("View more", callback_data="view_more_countries"))
        kb.add(back_btn("order_service"))
        bot.edit_message_text(text, message.chat.id, message.id, reply_markup=kb)
        bot.register_next_step_handler(message, select_country, data, res)

    elif data == "view_more_countries":
        data = data[2:]
        res = sa.getTopCountriesByService(data)
        cs = []
        for i in res:
            country_number = str(res[i]['country'])
            cs.append((countries[country_number], country_number))
        cs.sort()
        text = "\n".join(f"/{country_number} {country_name}" for country_name, country_number in cs)
        text = "Choose your country by tapping the numbers on the left\n\n" + text
        kb = InlineKeyboardMarkup()
        kb.add(back_btn("order_service"))
        bot.edit_message_text(text, message.chat.id, message.id, reply_markup=kb)
        bot.register_next_step_handler(message, select_country, data, res)

    elif data.startswith("purchase_smsactivate"):
        _, service, service_name, country = data.split(":")
        res = sa.getTopCountriesByService(service)
        max_price = None
        for i in res:
            if res[i]["country"] == country:
                max_price = res[i]["retail_price"]
        if not max_price:
            number_data = sa.getNumberV2(service, freePrice="true", maxPrice=1, country=country)
            if number_data.get("msg") == "WRONG_MAX_PRICE":
                number_data = sa.getNumberV2(service, freePrice="true", maxPrice=number_data["info"]["min"],
                                             country=country)
                max_price = number_data["info"]["min"]
        number_data = sa.getNumberV2(service, freePrice="true", maxPrice=max_price, country=country)
        if number_data.get("activationId"):
            activation_id = number_data["activationId"]
            phone_number = number_data["phoneNumber"]
            country = number_data["countryCode"]
            price = float(number_data["activationCost"]) * 4
            user = get_user(message.chat.id)
            if user.balance < price:
                kb = InlineKeyboardMarkup().add(InlineKeyboardButton("💲Top up Points", support)).add(
                    back_btn("order_goods"))
                bot.edit_message_text(
                    f"😓Not enough points to purchase this good\nYou need extra <b>🪙{price - user.balance} points</b>",
                    message.chat.id, message.id, reply_markup=kb)
                return
            order = Order(activation_id=activation_id, phone_number=phone_number, country_code=country, service=service,
                          type="service", user=str(message.chat.id),
                          time_created=datetime.fromisoformat(number_data["activationTime"]), price=price)
            session.add(order)
            session.commit()
            bot.edit_message_text(
                f"Purchase Successful✅\n\nActivation ID: `{activation_id}`\nPhone: `+{phone_number}`\nCountry: {countries[country]}\nService: {service_name}\n\n_You can see this order in your Order History if you want to get the sms later_",
                message.chat.id, message.id, parse_mode="markdown")
            os.system(f"nohup python3 scheduler.py {order.id} &")
        elif number_data.get("NO_BALANCE"):
            for i in owners:
                bot.send_message(i, "⚠️<b>WARNING</b>: Balance in SMS-Activate has finished")
        else:
            bot.edit_message_text(number_data["message"], message.chat.id, message.id,
                                  reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))

    elif data.startswith("good"):
        good = data.split(":")[-1]
        prices = load_file("data.json")
        bot.edit_message_text(f"<b>🛒Purchase {good}</b>\n\n🪙Price: <b>{prices[good.lower()]} points</b>",
                              message.chat.id, message.id, reply_markup=buy_good_kb(good))

    elif data.startswith("buy_good"):
        _, good = data.split(":")
        user = get_user(message.chat.id)
        prices = load_file("data.json")
        if user.balance < prices[good.lower()]:
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("💲Top up Points", support)).add(
                back_btn("order_goods"))
            bot.edit_message_text(
                f"😓Not enough points to purchase this good\nYou need extra <b>🪙{prices[good.lower()] - user.balance} points</b>",
                message.chat.id, message.id, reply_markup=kb)
            return
        kb = InlineKeyboardMarkup().add(back_btn("order_goods"))
        if not os.path.isfile(good.lower() + ".json"):
            bot.edit_message_text(f"🚫Out of stock.\nPlease, check again later", message.chat.id, message.id,
                                  reply_markup=kb)
            return

        file = load_file(good.lower() + ".json")
        if len(file) <= 0:
            bot.edit_message_text(f"🚫Out of stock.\nPlease, check again later", message.chat.id, message.id,
                                  reply_markup=kb)
            return
        delivery_data = file[0]
        file.pop(0)
        user.balance -= prices[good.lower()]
        order = Order(text=delivery_data, type="goods", user=user.id, price=prices[good.lower()], delivered=True,
                      service=good.title())
        session.add(order)
        session.commit()
        save_file(file, good.lower() + ".json")
        bot.edit_message_text("<b>Purchase Successful</b>✅\n\n" + delivery_data, message.chat.id, message.id)

    elif data.startswith("refresh_service_history"):
        _, order_id = data.split(":")
        order = session.query(Order).filter_by(id=order_id, user=str(message.chat.id)).first()
        if order:
            service_name = None
            for name, service in services.items():
                if service == order.service:
                    service_name = name

            response = sa.getStatus(order.activation_id)
            if str(response).find("STATUS_OK") != -1 and not order.delivered:
                user = get_user(order.user)
                user.balance -= order.price * 4
                order.delivered = True
                session.commit()
            response = activation_status_response_cleaner(response)
            text = "Activation ID: {}\nPhone Number: +{}\n\nStatus: {}\n\nService: {}\n\nCountry: {}".format(
                order.activation_id, order.phone_number, response, service_name, countries[order.country])
            bot.edit_message_text(text, message.chat.id, message.id, reply_markup=service_order(order))

    elif data.startswith("cancel_service_order"):
        _, activation_id = data.split(":")
        order = session.query(Order).filter_by(activation_id=activation_id, user=str(message.chat.id)).first()
        if order:
            response = sa.setStatus(order.activation_id, status="8")
            if response == "ACCESS_CANCEL":
                get_user(message.chat.id).balance += order.price * 4
                session.delete(order)
                session.commit()
                bot.edit_message_text("This order has been canceled and deleted", message.chat.id, message.id,
                                      reply_markup=InlineKeyboardMarkup().add(back_btn("order_history")))
            else:
                bot.answer_callback_query(callback.id, "You cannot cancel this order", True)
            return
        bot.edit_message_text("This order does not exist", message.chat.id, message.id,
                              reply_markup=InlineKeyboardMarkup().add(back_btn("order_history")))

    elif data.startswith("change_number"):
        order = session.query(Order).filter_by(id=data.split(":")[-1], user=str(message.chat.id)).first()
        number_data = sa.getNumberV2(order.service, freePrice="true", maxPrice=order.price, country=order.country_code)
        if number_data.get("NO_NUMBERS"):
            bot.answer_callback_query(callback.id, "There are no numbers available", True)
            return
        elif number_data.get("activationId"):
            order.activation_id = number_data["activationId"]
            order.phone_number = number_data["phoneNumber"]
            order.delivered = False
            order.price = number_data["activationCost"] * 4
            order.time_created = datetime.now()
            session.commit()
            text = "Number Changed!\n\nActivation ID: {}\nPhone Number: +{}\nCountry: {}".format(
                order.activation_id, order.phone_number, countries[order.country])
            bot.edit_message_text(text, message.chat.id, message.id, reply_markup=service_order(order))
            os.system(f"nohup python3 scheduler.py {order.id} &")

    elif data == "back":
        pass

    if data.startswith("admin_") and message.chat.id in owners:
        data = data[6:]
        if data == "edit_balance":
            bot.edit_message_text("What kind of editing do you want to do?", reply_markup=Admin.edit_balance_kb,
                                  chat_id=message.chat.id, message_id=message.id)

        elif data == "add_balance":
            bot.edit_message_text("Send the <b>Telegram ID</b> of the user you want to add balance to",
                                  chat_id=message.chat.id, message_id=message.id)
            bot.register_next_step_handler(message, get_user_id, "add")

        elif data == "alter_balance":
            bot.edit_message_text("Send the <b>Telegram ID</b> of the user you want to change their balance value",
                                  chat_id=message.chat.id, message_id=message.id)
            bot.register_next_step_handler(message, get_user_id, "alter")

        elif data == "control_membership":
            bot.edit_message_text("Send the <b>Telegram ID</b> of a user", chat_id=message.chat.id,
                                  message_id=message.id)
            bot.register_next_step_handler(message, get_user_id, "membership")

        elif data == "ignore_member":
            bot.edit_message_reply_markup(message.chat.id, message.id, reply_markup=InlineKeyboardMarkup())

        elif data.startswith("register_user"):
            _, uid = data.split(":")
            user = get_user(uid)
            user.is_registered = True
            user.is_disabled = False
            session.commit()
            bot.send_message(uid, "✅Your membership has been accepted by the admin", reply_markup=general_kb)
            bot.edit_message_text(f"You have accepted {bot.get_chat(user.id).id}'s membership", message.chat.id,
                                  message.id, reply_markup=Admin.back_btn())

        elif data.startswith("control_membership"):
            _, uid = data.split(":")
            user = get_user(uid)
            user.is_disabled = not user.is_disabled
            session.commit()
            if user.is_disabled:
                text = "⛔Your membership has been suspended by the admin"
            else:
                text = "✅Your membership has been enabled by the admin"
            bot.send_message(uid, text, reply_markup=general_kb)
            bot.edit_message_text(
                f"You have turned {'off' if user.is_disabled else 'on'} {bot.get_chat(user.id).id} 's membership",
                message.chat.id, message.id, reply_markup=Admin.back_btn())

        elif data == "registrations":
            kb = InlineKeyboardMarkup()
            unregistered_users = session.query(User).filter_by(is_registered=False).all()
            kb_btns = [
                InlineKeyboardButton(str(bot.get_chat(i.id).id), callback_data="admin_register_user:" + str(i.id)) for i
                in unregistered_users[:99]]
            kb.add(*kb_btns)
            kb.add(Admin.back_btn())
            bot.edit_message_text("Any name you click will be marked as registered!!", message.chat.id, message.id,
                                  reply_markup=kb)

        elif data == "edit_goods":
            bot.edit_message_text("Select what good you want to edit", message.chat.id, message.id,
                                  reply_markup=Admin.edit_goods_kb())

        elif data.startswith("add_goods"):
            good = data.split(":")[-1]
            bot.edit_message_text(f"Send the a .txt file for the new {good} goods", message.chat.id, message.id,
                                  reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:" + good)))
            bot.register_next_step_handler(message, add_goods, good)

        elif data.startswith("price_change_goods"):
            good = data.split(":")[-1]
            bot.edit_message_text(f"Send the price you want to set for " + good + " goods", message.chat.id, message.id,
                                  reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:" + good)))
            bot.register_next_step_handler(message, change_goods_price, good)

        elif data.startswith("edit"):
            good = data.split(":")[-1]
            bot.edit_message_text("What property of " + good + " do you want to edit?", message.chat.id, message.id,
                                  reply_markup=Admin.edit_good_kb(good))

        elif data.startswith("delete_good:"):
            _, good = data.split(":")
            data = load_file("data.json")
            try:
                data["types"].remove(good.lower())
                data.pop(good.lower())
            except:
                pass
            else:
                save_file(data, "data.json")
            bot.edit_message_text(good + " deleted !", message.chat.id, message.id,
                                  reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit_goods")))


        elif data.startswith("delete_user:"):
            _, uid = data.split(":")
            session.delete(session.query(User).get(uid))
            session.commit()
            bot.edit_message_text(f"{uid} deleted!", message.chat.id, message.id,
                                  reply_markup=InlineKeyboardMarkup().add(Admin.back_btn()))

        elif data == "new_good":
            bot.edit_message_text("What is the name of the goods?", message.chat.id, message.id,
                                  reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit_goods")))
            bot.register_next_step_handler(message, new_goods_name)

        elif data == "home":
            bot.edit_message_text("Welcome to the admin panel.", reply_markup=Admin.kb, chat_id=message.chat.id,
                                  message_id=message.id)
        return


def new_goods_name(message):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message")
        bot.register_next_step_handler(message, new_goods_name)
        return
    data = load_file("data.json")
    data["types"].append(message.text.lower())
    data[message.text.lower()] = 0
    save_file(data, "data.json")
    save_file([], message.text.lower() + ".json")
    bot.send_message(message.chat.id, message.text + " Created.\nPrice is currently set to 0 points",
                     reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit_goods")))


def change_goods_price(message: Message, good: str):
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
    file = load_file("data.json")
    file[good.lower()] = amt
    save_file(file, "data.json")
    bot.send_message(message.chat.id, "The price for " + good + " goods has been set to " + str(amt) + " points",
                     reply_markup=InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:" + good)))


def add_goods(message: Message, good: str):
    if is_cancel(message): return
    if not message.document:
        bot.send_message(message.chat.id, "You need to send a document")
        bot.register_next_step_handler(message, add_goods, good)
        return

    file = bot.download_file(bot.get_file(message.document.file_id).file_path)
    filename = good.lower() + ".json"
    kb = InlineKeyboardMarkup().add(Admin.back_btn("admin_edit:" + good))
    try:
        data = []
        for line in file.decode().split("\n"):
            data.append(line)
        f = load_file(filename)
        f.extend(data)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "This file has a fault and cannot be added.", reply_markup=kb)
    else:
        save_file(f, filename)
        bot.send_message(message.chat.id, "This file has been added successfully in " + good, reply_markup=kb)


def get_user_id(message, mode):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message")
        bot.register_next_step_handler(message, get_user_id, mode)
        return
    try:
        user = bot.get_chat(message.text)
    except:
        bot.send_message(message.chat.id,
                         "Incorrect user ID. Please make sure the user has chatted with the bot before")
        bot.register_next_step_handler(message, get_user_id, mode)
        return
    u = get_user(user.id)
    if mode == "membership":
        bot.send_message(message.chat.id,
                         f"User ID: `{user.id}`\nBalance: {u.balance} points\nMembership: {'⛔Inactive' if u.is_disabled else '✅Active'}",
                         parse_mode="markdown", reply_markup=Admin.Membership.edit_membership(u.is_disabled, user.id))
        return

    data = {"add": {
        "text": "What amount do you want to add to @" + str(user.id),
        "func": add_balance
    },
        "alter": {
            "text": "What amount do you want to add to @" + str(user.id),
            "func": alter_balance
        }, }
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
    bot.send_message(message.chat.id,
                     f"You have added {amt} to {user.id}\nCurrent balance: <b>{user.balance} points</b>",
                     reply_markup=Admin.back_btn("admin_edit_balance"))
    bot.send_message(user.id,
                     f"🪙<b>{amt} points</b> has been added to your balance\nCurrent balance: 🪙<b>{user.balance} points</b>")


def alter_balance(message, user):
    if is_cancel(message): return
    amt = verfiy_float(message.text)
    if not amt:
        bot.send_message(message.chat.id, "Send a valid number. Try again")
        bot.register_next_step_handler(message, add_balance, user)
        return
    user.balance = amt
    session.commit()
    bot.send_message(message.chat.id, f"You have overwritten @{user.id}'s balance to <b>{amt}</b> points",
                     reply_markup=Admin.back_btn("admin_edit_balance"))
    bot.send_message(user.id,
                     f"Your balance has been updated by the admin\nCurrent balance: 🪙<b>{user.balance} points</b>")


def search_service(message: Message):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message",
                         reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, search_service)
        return
    search_list = []
    if json.dumps(services).lower().find(message.text.lower()) != -1:
        for i in services:
            if i.lower().startswith(message.text.lower()):
                search_list.append(i)
    bot.send_message(message.chat.id, "Search results📜", reply_markup=services_kb(search_list))


def is_cancel(message):
    if message.text in ["👤Account", "🤖Order Service", "🛍️Order Goods", "🕑Order History", "📞Support"]:
        all_messages(message)
        return True
    if message.text == "/start":
        bot.clear_reply_handlers(message)
        start(message)
        return True
    if message.text == "/admin":
        bot.clear_reply_handlers(message)
        admin(message)
        return True
    return


def select_country(message: Message, service: str, response: dict):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message",
                         reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, select_country, service, response)
        return
    if message.text.startswith("/"):
        country = message.text[1:]
    else:
        country = message.text

    if not country.isdigit() or not countries.get(country):
        bot.send_message(message.chat.id, "🚫Invalid Country code, try again")
        bot.register_next_step_handler(message, select_country, service, response)
        return
    service_name = ""
    for i in services:
        if services[i] == service:
            service_name = i
            break
    for i in response:
        if response[i]["country"] == int(country):
            price = response[i]["retail_price"]
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Purchase",
                                        callback_data=f"purchase_smsactivate:{service}:{service_name}:{country}"))
            kb.add(back_btn("order_service"))
            bot.send_message(message.chat.id,
                             f"🛒Order summary:\n\nService: <b>{service_name}</b>\nCountry: <b>{countries[country]}</b>\nPrice: 🪙<b>{price * 4} points</b>",
                             reply_markup=kb)
            break


def lookup_order(message):
    if is_cancel(message): return
    if not message.text:
        bot.send_message(message.chat.id, "Send a text message",
                         reply_markup=InlineKeyboardMarkup().add(back_btn("order_service")))
        bot.register_next_step_handler(message, lookup_order)
        return
    if message.text.startswith("/"):
        order_id = message.text[1:]
    else:
        order_id = message.text

    if not order_id.isdigit():
        bot.send_message(message.chat.id, "🚫Invalid OrderID, try again")
        bot.register_next_step_handler(message, lookup_order)
    order = session.query(Order).filter_by(id=int(order_id), user=str(message.chat.id)).first()
    if not order:
        bot.send_message(message.chat.id, "🚫Order not found😓")
        bot.register_next_step_handler(message, lookup_order)
    service_name = None
    for name, service in services.items():
        if service == order.service:
            service_name = name

    response = sa.getStatus(order.activation_id)
    if str(response).find("STATUS_OK") != -1 and not order.delivered:
        user = get_user(order.user)
        user.balance -= order.price * 4
        order.delivered = True
        session.commit()
    response = activation_status_response_cleaner(response)
    text = "Activation ID: <code>{}</code>\nPhone Number: <code>+{}</code>\n\nStatus: {}\n\nService: {}\n\nCountry: {}" \
        .format(order.activation_id, order.phone_number, response, service_name, countries[order.country])
    bot.send_message(message.chat.id, text, reply_markup=service_order(order))


print("Started")
bot.infinity_polling()
