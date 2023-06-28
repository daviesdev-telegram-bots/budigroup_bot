from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

register_kb = InlineKeyboardMarkup()
register_kb.add(InlineKeyboardButton("Register", callback_data="register"))

general_kb = ReplyKeyboardMarkup()
general_kb.add(KeyboardButton("👤Account"), KeyboardButton("🕑Order History"))
general_kb.add(KeyboardButton("📞Support"))

class Admin:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Edit balance", callback_data="admin_edit_balance"))
    kb.add(InlineKeyboardButton("Edit Membership", callback_data="admin_control_membership"))
    kb.add(InlineKeyboardButton("Registrations", callback_data="admin_registrations"))
    
    def register_kb(chat_id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅Accept", "admin_control_membership:"+str(chat_id)), InlineKeyboardButton("⛔Ignore", "admin_ignore_member"))
    
    def edit_balance_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Add balance", callback_data="admin_add_balance"), InlineKeyboardButton("Change balance", callback_data="admin_alter_balance"))
        kb.add(Admin.back_btn())
        return kb

    class Membership:
        def edit_membership(is_disabled, uid):
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Turn On Membership" if is_disabled else "Turn Off Membership", callback_data=f"admin_control_membership:{uid}"))
            kb.add(Admin.back_btn())
            return kb
        
        def confirm_membership_edit():
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Edit Membership", callback_data="admin_add_balance"), InlineKeyboardButton("Edit Membership", callback_data="admin_add_balance"))
            kb.add(Admin.back_btn())
            return kb
            

    def back_btn(step="admin_home"):
        return InlineKeyboardButton("back", callback_data=step)