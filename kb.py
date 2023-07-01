from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from utils import services as all_services

register_kb = InlineKeyboardMarkup()
register_kb.add(InlineKeyboardButton("Register", callback_data="register"))


general_kb = ReplyKeyboardMarkup()
general_kb.add(KeyboardButton("🛍️Order Goods"), KeyboardButton("🤖Order Service"))
general_kb.add(KeyboardButton("👤Account"), KeyboardButton("🕑Order History"))
general_kb.add(KeyboardButton("📞Support"))

goods_types_kb = InlineKeyboardMarkup()
goods_types_kb.add(InlineKeyboardButton("Instagram accounts", callback_data="good:ig"), InlineKeyboardButton("VCC", callback_data="good:vcc"))

def back_btn(step="back"):
    return InlineKeyboardButton("back", callback_data=step)

def buy_good_kb(good):
    buy_good_kb = InlineKeyboardMarkup()
    buy_good_kb.add(InlineKeyboardButton("Buy", callback_data=f"buy_good:{good}"))
    buy_good_kb.add(back_btn("order_goods"))
    return buy_good_kb

def services_kb(services):
    services_kb = InlineKeyboardMarkup()
    services_kb.add(InlineKeyboardButton("🔍Search", callback_data="search_service"))
    services_kb.add(*[InlineKeyboardButton(i, callback_data="s_"+all_services[i]) for i in services])
    return services_kb


class Admin:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Edit balance", callback_data="admin_edit_balance"))
    kb.add(InlineKeyboardButton("Edit Membership", callback_data="admin_control_membership"))
    kb.add(InlineKeyboardButton("Registrations", callback_data="admin_registrations"))
    kb.add(InlineKeyboardButton("Edit Goods", callback_data="admin_edit_goods"))

    edit_goods_kb = InlineKeyboardMarkup()
    edit_goods_kb.add(InlineKeyboardButton("Instagram", callback_data="admin_edit:Instagram"), InlineKeyboardButton("VCC", callback_data="admin_edit:VCC"))
    edit_goods_kb.add(back_btn("admin_home"))

    edit_balance_kb = InlineKeyboardMarkup()
    edit_balance_kb.add(InlineKeyboardButton("Add balance", callback_data="admin_add_balance"), InlineKeyboardButton("Change balance", callback_data="admin_alter_balance"))
    edit_balance_kb.add(back_btn())

    def edit_good_kb(good):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"Add {good} data", callback_data=f"admin_add_goods:{good}"), InlineKeyboardButton(f"Change price", callback_data=f"admin_price_change_goods:{good}"))
        kb.add(Admin.back_btn("admin_edit_goods"))
        return kb

    def register_kb(chat_id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅Accept", callback_data="admin_register_user:"+str(chat_id)), InlineKeyboardButton("⛔Ignore", callback_data="admin_ignore_member"))
        return kb
    
    class Membership:
        def edit_membership(is_disabled, uid):
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Turn On Membership" if is_disabled else "Turn Off Membership", callback_data=f"admin_control_membership:{uid}"))
            kb.add(Admin.back_btn())
            return kb
            
    def back_btn(step="admin_home"):
        return InlineKeyboardButton("back", callback_data=step)