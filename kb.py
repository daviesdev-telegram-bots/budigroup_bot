from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

class Admin:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Add balance", "admin_add_balance"))
    kb.add(InlineKeyboardButton("Change balance", "admin_alter_balance"))
