from datetime import datetime, timedelta

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from utils import services as all_services, load_file

register_kb = InlineKeyboardMarkup()
register_kb.add(InlineKeyboardButton("📝Register", callback_data="register"))

general_kb = ReplyKeyboardMarkup()
general_kb.add(KeyboardButton("🛍️Order Goods"), KeyboardButton("🤖Order Service"))
general_kb.add(KeyboardButton("👤Account"), KeyboardButton("🕑Order History"))
general_kb.add(KeyboardButton("📞Support"))


def service_order(order):
    kb = InlineKeyboardMarkup()
    cancel = None
    if (datetime.now() - order.time_created) > timedelta(minutes=2):
        cancel = InlineKeyboardButton("❌Cancel", callback_data="cancel_service_order:" + str(order.id))
    change = None
    if not order.delivered:
        change = InlineKeyboardButton("🔃Get code", callback_data="refresh_service_history:" + str(order.id))
    if (datetime.now() - order.time_created) > timedelta(minutes=3):
        change = InlineKeyboardButton("🔃Change Number", callback_data="change_number:" + str(order.id))
    kb.add(change, cancel)
    kb.add(back_btn("order_history"))
    return kb


def goods_types_kb():
    data = load_file("data.json")["types"]
    goods_types_kb = InlineKeyboardMarkup(row_width=2)
    goods_types_kb.add(*[InlineKeyboardButton(i.title(), callback_data="good:" + i) for i in data])
    return goods_types_kb


def back_btn(step="back"):
    return InlineKeyboardButton("back", callback_data=step)


def buy_good_kb(good):
    buy_good_kb = InlineKeyboardMarkup()
    buy_good_kb.add(InlineKeyboardButton("🛒Buy", callback_data=f"buy_good:{good}"))
    buy_good_kb.add(back_btn("order_goods"))
    return buy_good_kb


def services_kb(services):
    services_kb = InlineKeyboardMarkup()
    services_kb.add(InlineKeyboardButton("🔍Search", callback_data="search_service"))
    services_kb.add(*[InlineKeyboardButton(i, callback_data="s_" + all_services[i]) for i in services])
    return services_kb


class Admin:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Edit balance", callback_data="admin_edit_balance"))
    kb.add(InlineKeyboardButton("Edit Membership", callback_data="admin_control_membership"))
    kb.add(InlineKeyboardButton("Registrations", callback_data="admin_registrations"))
    kb.add(InlineKeyboardButton("Edit Goods", callback_data="admin_edit_goods"))

    def edit_goods_kb():
        data = load_file("data.json")["types"]
        edit_goods_kb = InlineKeyboardMarkup(row_width=2)
        edit_goods_kb.add(InlineKeyboardButton("➕Add good type", callback_data="admin_new_good"))
        edit_goods_kb.add(*[InlineKeyboardButton(i.title(), callback_data="admin_edit:" + i) for i in data])
        edit_goods_kb.add(back_btn("admin_home"))
        return edit_goods_kb

    edit_balance_kb = InlineKeyboardMarkup()
    edit_balance_kb.add(InlineKeyboardButton("Add balance", callback_data="admin_add_balance"),
                        InlineKeyboardButton("Change balance", callback_data="admin_alter_balance"))
    edit_balance_kb.add(back_btn("admin_home"))

    def edit_good_kb(good):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"Add {good} data", callback_data=f"admin_add_goods:{good}"),
               InlineKeyboardButton(f"Change price", callback_data=f"admin_price_change_goods:{good}"))
        kb.add(InlineKeyboardButton("❌Delete", callback_data="admin_delete_good:" + good),
               Admin.back_btn("admin_edit_goods"))
        return kb

    def register_kb(chat_id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅Accept", callback_data="admin_register_user:" + str(chat_id)),
               InlineKeyboardButton("⛔Ignore", callback_data="admin_ignore_member"))
        return kb

    class Membership:
        def edit_membership(is_disabled, uid):
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Turn On Membership" if is_disabled else "Turn Off Membership",
                                        callback_data=f"admin_control_membership:{uid}"))
            kb.add(InlineKeyboardButton("❌Delete User", callback_data=f"admin_delete_user:{uid}"))
            kb.add(Admin.back_btn())
            return kb

    def back_btn(step="admin_home"):
        return InlineKeyboardButton("back", callback_data=step)
