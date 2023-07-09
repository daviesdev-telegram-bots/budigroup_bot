import os
import sys
from datetime import datetime, timedelta

import schedule
from smsactivate.api import SMSActivateAPI
from telebot import TeleBot

from models import Order, session

bot_token = os.getenv("bot_token")

bot = TeleBot(bot_token, parse_mode="HTML")

sa = SMSActivateAPI(os.getenv("SMS_ACTIVATE_APIKEY"))

_, order_id = sys.argv
order = session.query(Order).get(int(order_id))


def check_order_status():
    response = sa.getStatus(order.activation_id)
    if str(response).find("STATUS_OK") != -1:
        order.delivered = True
        bot.send_message(order.user,
                         f"Your order has been completed\nActivation ID: <code>{order.activation_id}</code>\n"
                         f"Phone: <code>+{order.phone_number}</code>\n\nCode: <b>{response}</b>")
        sys.exit(0)
    if (datetime.now() - order.time_created) > timedelta(minutes=4):
        sa.setStatus(order.activation_id, status=8)
        sys.exit(0)


schedule.every().minute.do(check_order_status)

while True:
    schedule.run_pending()
