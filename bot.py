from telebot import TeleBot
from dotenv import load_dotenv
import os, json
load_dotenv()

bot_token = os.getenv("bot_token")
owners = json.loads(os.getenv("owners"))
bot = TeleBot(bot_token, parse_mode="HTML")


@bot.message_handler(["start"])
def start(message):
    pass


bot.enable_save_next_step_handlers(120)
print("Started")
bot.infinity_polling()