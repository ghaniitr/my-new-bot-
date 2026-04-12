"""
Bilingual messages module for Telegram Store Bot.
All user-facing strings in Arabic and English.
"""

from typing import Dict, Any


def t(lang: str, ar: str, en: str) -> str:
    """Return message based on user language preference."""
    return ar if lang == 'ar' else en


# ==================== LANGUAGE SELECTION ====================

def select_language() -> str:
    """Language selection prompt."""
    return "🌐 اختر لغتك | Select your language"


# ==================== MINI APP VERIFICATION ====================

def miniapp_prompt(lang: str) -> str:
    return t(lang,
        "🔒 للحماية من الحسابات المزيفة، يرجى إكمال التحقق:\n\n"
        "اضغط على الزر أدناه لفتح تطبيق الويب، ثم اضغط على 'تحقق'.",
        "🔒 To protect against fake accounts, please complete verification:\n\n"
        "Click the button below to open the web app, then click 'Verify'.")


def miniapp_waiting(lang: str) -> str:
    return t(lang,
        "⏳ جاري التحقق... يرجى الانتظار",
        "⏳ Verifying... please wait")


def miniapp_verified(lang: str) -> str:
    return t(lang,
        "✅ تم التحقق بنجاح! يمكنك المتابعة الآن.",
        "✅ Verification successful! You can now continue.")


def miniapp_failed(lang: str) -> str:
    return t(lang,
        "⚠️ تم اكتشاف مشكلة في التحقق. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.",
        "⚠️ Verification issue detected. Please try again or contact support.")


# ==================== CHANNEL SUBSCRIPTION ====================

def channel_join_prompt(lang: str, channels: list) -> str:
    channels_text = "\n".join([f"• {ch.get('channel_name', 'Channel')}" for ch in channels])
    return t(lang,
        f"📢 للاستمرار، يرجى الانضمام إلى القنوات التالية:\n\n{channels_text}\n\n"
        "بعد الانضمام، اضغط على '✅ انضممت'",
        f"📢 To continue, please join the following channels:\n\n{channels_text}\n\n"
        "After joining, click '✅ I Joined'")


def channel_not_joined(lang: str) -> str:
    return t(lang,
        "❌ لم تنضم إلى جميع القنوات بعد. يرجى الانضمام والمحاولة مرة أخرى.",
        "❌ You haven't joined all channels yet. Please join and try again.")


def channel_join_success(lang: str) -> str:
    return t(lang,
        "✅ شكراً لانضمامك! يمكنك الآن استخدام البوت.",
        "✅ Thanks for joining! You can now use the bot.")


# ==================== MAIN MENU ====================

def main_menu(lang: str, first_name: str, points: int) -> str:
    return t(lang,
        f"👋 أهلاً {first_name}!\n\n"
        f"💰 رصيدك: {points} نقطة\n\n"
        "اختر من القائمة أدناه:",
        f"👋 Hello {first_name}!\n\n"
        f"💰 Your balance: {points} points\n\n"
        "Choose from the menu below:")


# ==================== STORE ====================

def store_home(lang: str) -> str:
    return t(lang,
        "🛍️ متجرنا - اختر الفئة:",
        "🛍️ Our Store - Select a category:")


def category_empty(lang: str) -> str:
    return t(lang,
        "📭 لا توجد منتجات في هذه الفئة حالياً.",
        "📭 No products in this category currently.")


def product_detail(lang: str, product: Dict[str, Any]) -> str:
    name = product['name_ar'] if lang == 'ar' else product['name_en']
    desc = product.get('description_ar' if lang == 'ar' else 'description_en', '')
    price = product['points_price']
    stock = product['stock']
    
    stock_text = t(lang, "✅ متوفر", "✅ In Stock") if stock > 0 else t(lang, "❌ نفذت الكمية", "❌ Out of Stock")
    
    text = f"📦 <b>{name}</b>\n\n"
    if desc:
        text += f"📝 {desc}\n\n"
    text += f"💰 {t(lang, 'السعر', 'Price')}: {price} {t(lang, 'نقطة', 'points')}\n"
    text += f"📊 {stock_text} ({stock} {t(lang, 'متبقي', 'remaining')})"
    
    return text


def product_out_of_stock(lang: str) -> str:
    return t(lang,
        "❌ هذا المنتج غير متوفر حالياً.\n"
        "اضغط على '🔔 أبلغني' ليتم إشعارك عند توفره.",
        "❌ This product is currently unavailable.\n"
        "Click '🔔 Notify Me' to be notified when available.")


def added_to_waiting_list(lang: str) -> str:
    return t(lang,
        "✅ تم إضافتك إلى قائمة الانتظار. سيتم إشعارك عند توفر المنتج.",
        "✅ Added to waiting list. You'll be notified when available.")


def already_on_waiting_list(lang: str) -> str:
    return t(lang,
        "✅ أنت بالفعل في قائمة الانتظار لهذا المنتج.",
        "✅ You're already on the waiting list for this product.")


# ==================== PURCHASE ====================

def purchase_confirm(lang: str, product_name: str, price: int, balance: int) -> str:
    return t(lang,
        f"🛒 تأكيد الشراء\n\n"
        f"📦 المنتج: {product_name}\n"
        f"💰 السعر: {price} نقطة\n"
        f"💳 رصيدك: {balance} نقطة\n\n"
        "هل تريد تأكيد الشراء؟",
        f"🛒 Purchase Confirmation\n\n"
        f"📦 Product: {product_name}\n"
        f"💰 Price: {price} points\n"
        f"💳 Your balance: {balance} points\n\n"
        "Confirm purchase?")


def purchase_success(lang: str, order_id: str, content: str) -> str:
    return t(lang,
        f"✅ تم الشراء بنجاح!\n\n"
        f"📋 رقم الطلب: <code>{order_id}</code>\n\n"
        f"📦 محتوى المنتج:\n<code>{content}</code>\n\n"
        "شكراً لشرائك! 🎉",
        f"✅ Purchase successful!\n\n"
        f"📋 Order ID: <code>{order_id}</code>\n\n"
        f"📦 Product content:\n<code>{content}</code>\n\n"
        "Thank you for your purchase! 🎉")


def purchase_not_enough_points(lang: str, needed: int) -> str:
    return t(lang,
        f"❌ رصيدك غير كافٍ!\n"
        f"تحتاج إلى {needed} نقطة إضافية.",
        f"❌ Insufficient balance!\n"
        f"You need {needed} more points.")


def purchase_out_of_stock(lang: str) -> str:
    return t(lang,
        "❌ عذراً، نفذت الكمية أثناء معالجة طلبك.\n"
        "يرجى المحاولة لاحقاً أو اختيار منتج آخر.",
        "❌ Sorry, the item went out of stock during processing.\n"
        "Please try again later or choose another product.")


def purchase_cancelled(lang: str) -> str:
    return t(lang,
        "❌ تم إلاء الشراء.",
        "❌ Purchase cancelled.")


# ==================== POINTS ====================

def my_points(lang: str, balance: int, total_earned: int, total_spent: int) -> str:
    return t(lang,
        f"💰 رصيدك الحالي: {balance} نقطة\n\n"
        f"📊 إحصائيات:\n"
        f"• إجمالي المكتسب: {total_earned} نقطة\n"
        f"• إجمالي المصروف: {total_spent} نقطة",
        f"💰 Current balance: {balance} points\n\n"
        f"📊 Statistics:\n"
        f"• Total earned: {total_earned} points\n"
        f"• Total spent: {total_spent} points")


def coupon_prompt(lang: str) -> str:
    return t(lang,
        "🎟️ أرسل كود الكوبون لاستبداله بالنقاط:",
        "🎟️ Send the coupon code to redeem for points:")


def coupon_success(lang: str, points: int, new_balance: int) -> str:
    return t(lang,
        f"✅ تم استبدال الكوبون بنجاح!\n"
        f"🎁 حصلت على {points} نقطة\n"
        f"💰 رصيدك الجديد: {new_balance} نقطة",
        f"✅ Coupon redeemed successfully!\n"
        f"🎁 You got {points} points\n"
        f"💰 New balance: {new_balance} points")


def coupon_invalid(lang: str, reason: str = None) -> str:
    if reason:
        return t(lang, f"❌ {reason}", f"❌ {reason}")
    return t(lang,
        "❌ كود الكوبون غير صالح أو منتهي الصلاحية.",
        "❌ Invalid or expired coupon code.")


def coupon_already_used(lang: str) -> str:
    return t(lang,
        "❌ لقد استخدمت هذا الكوبون مسبقاً.",
        "❌ You have already used this coupon.")


def coupon_limit_reached(lang: str) -> str:
    return t(lang,
        "❌ تم استنفاد الاستخدامات المتاحة لهذا الكوبون.",
        "❌ This coupon has reached its usage limit.")


def no_orders(lang: str) -> str:
    return t(lang,
        "📭 ليس لديك أي طلبات حتى الآن.",
        "📭 You don't have any orders yet.")


def order_item(lang: str, order: Dict[str, Any]) -> str:
    product_name = order.get('name_ar' if lang == 'ar' else 'name_en', 'Unknown')
    return t(lang,
        f"📦 {product_name}\n"
        f"📋 {order['order_id']}\n"
        f"💰 {order['amount']} نقطة\n"
        f"📅 {order['created_at'][:10]}",
        f"📦 {product_name}\n"
        f"📋 {order['order_id']}\n"
        f"💰 {order['amount']} points\n"
        f"📅 {order['created_at'][:10]}")


# ==================== DAILY BONUS ====================

def daily_bonus_available(lang: str, points: int) -> str:
    return t(lang,
        f"🎁 المكافأة اليومية متاحة!\n\n"
        f"احصل على {points} نقطة الآن!",
        f"🎁 Daily bonus available!\n\n"
        f"Get {points} points now!")


def daily_bonus_claimed(lang: str, points: int, streak: int) -> str:
    return t(lang,
        f"✅ تم استلام المكافأة!\n"
        f"🎁 حصلت على {points} نقطة\n"
        f"🔥 سلسلة يومية: {streak} يوم",
        f"✅ Bonus claimed!\n"
        f"🎁 You got {points} points\n"
        f"🔥 Daily streak: {streak} days")


def daily_bonus_wait(lang: str, hours: int, minutes: int, seconds: int) -> str:
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return t(lang,
        f"⏳ المكافأة التالية متاحة بعد:\n<code>{time_str}</code>",
        f"⏳ Next bonus available in:\n<code>{time_str}</code>")


# ==================== BUY POINTS ====================

def buy_points_home(lang: str) -> str:
    return t(lang,
        "💎 اشترِ نقاط باستخدام Telegram Stars\n\n"
        "اختر الباقة المناسبة:",
        "💎 Buy points with Telegram Stars\n\n"
        "Select a package:")


def buy_points_no_packages(lang: str) -> str:
    return t(lang,
        "📭 لا توجد باقات متاحة حالياً.",
        "📭 No packages available currently.")


def buy_points_invoice_title(lang: str, stars: int, points: int) -> str:
    return t(lang,
        f"{points} نقطة",
        f"{points} Points")


def buy_points_invoice_description(lang: str, stars: int, points: int) -> str:
    return t(lang,
        f"اشترِ {points} نقطة مقابل {stars} نجمة Telegram",
        f"Buy {points} points for {stars} Telegram Stars")


def buy_points_success(lang: str, points: int, new_balance: int, coupon_code: str) -> str:
    return t(lang,
        f"✅ تم الدفع بنجاح!\n\n"
        f"🎁 حصلت على {points} نقطة\n"
        f"💰 رصيدك الجديد: {new_balance} نقطة\n"
        f"🎟️ كوبونك: <code>{coupon_code}</code>\n\n"
        "شكراً لدعمك! 💖",
        f"✅ Payment successful!\n\n"
        f"🎁 You got {points} points\n"
        f"💰 New balance: {new_balance} points\n"
        f"🎟️ Your coupon: <code>{coupon_code}</code>\n\n"
        "Thank you for your support! 💖")


# ==================== REFERRAL ====================

def referral_home(lang: str, referral_link: str, count: int, earned: int) -> str:
    return t(lang,
        f"🔗 رابط الإحالة الخاص بك:\n"
        f"<code>{referral_link}</code>\n\n"
        f"👥 إجمالي الإحالات النشطة: {count}\n"
        f"💰 إجمالي النقاط المكتسبة: {earned}",
        f"🔗 Your referral link:\n"
        f"<code>{referral_link}</code>\n\n"
        f"👥 Total active referrals: {count}\n"
        f"💰 Total points earned: {earned}")


def referral_awarded_notification(lang: str, points: int, referred_name: str) -> str:
    return t(lang,
        f"🎉 تهانينا! حصلت على {points} نقطة\n"
        f"من إحالة: {referred_name}",
        f"🎉 Congratulations! You got {points} points\n"
        f"from referral: {referred_name}")


def referral_penalty(lang: str, points: int, referred_name: str) -> str:
    return t(lang,
        f"⚠️ تم خصم {points} نقطة\n"
        f"لأن {referred_name} غادر القناة.",
        f"⚠️ {points} points deducted\n"
        f"because {referred_name} left the channel.")


def referral_restore(lang: str, points: int, referred_name: str) -> str:
    return t(lang,
        f"✅ تم إرجاع {points} نقطة\n"
        f"لأن {referred_name} عاد إلى القناة.",
        f"✅ {points} points restored\n"
        f"because {referred_name} rejoined the channel.")


# ==================== SUPPORT ====================

def support_intro(lang: str) -> str:
    return t(lang,
        "📩 الدعم الفني\n\n"
        "أرسل رسالتك وسنقوم بالرد عليك في أقرب وقت.",
        "📩 Support\n\n"
        "Send your message and we'll reply as soon as possible.")


def support_sent(lang: str, ticket_id: int) -> str:
    return t(lang,
        f"✅ تم إرسال رسالتك!\n"
        f"رقم التذكرة: <code>#{ticket_id}</code>\n\n"
        "سنقوم بالرد عليك قريباً.",
        f"✅ Message sent!\n"
        f"Ticket ID: <code>#{ticket_id}</code>\n\n"
        "We'll reply to you soon.")


def support_reply_received(lang: str, reply: str) -> str:
    return t(lang,
        f"💬 رد من الدعم الفني:\n\n{reply}",
        f"💬 Support reply:\n\n{reply}")


# ==================== ADMIN (English only) ====================

def admin_panel() -> str:
    return "⚙️ <b>Admin Panel</b>\n\nSelect an option:"


def admin_products_list() -> str:
    return "📦 <b>Products Management</b>\n\nSelect a product:"


def admin_categories_list() -> str:
    return "📂 <b>Categories Management</b>\n\nSelect a category:"


def admin_channels_list() -> str:
    return "📢 <b>Channels Management</b>\n\nSelect a channel:"


def admin_coupons_list() -> str:
    return "🎟️ <b>Coupons Management</b>\n\nSelect a coupon:"


def admin_users_search() -> str:
    return "👥 <b>User Search</b>\n\nEnter Telegram ID or @username:"


def admin_user_profile(user: Dict[str, Any]) -> str:
    flagged = "🚩 YES" if user.get('miniapp_flagged') else "✅ No"
    banned = "🚫 YES" if user.get('is_banned') else "✅ No"
    
    return (f"👤 <b>User Profile</b>\n\n"
            f"🆔 ID: <code>{user['telegram_id']}</code>\n"
            f"👤 Username: @{user.get('username', 'N/A')}\n"
            f"📛 Name: {user.get('first_name', 'N/A')}\n"
            f"💰 Points: {user.get('points', 0)}\n"
            f"📊 Total Earned: {user.get('total_earned', 0)}\n"
            f"📊 Total Spent: {user.get('total_spent', 0)}\n"
            f"🚫 Banned: {banned}\n"
            f"🚩 Flagged: {flagged}\n"
            f"📅 Joined: {user.get('joined_at', 'N/A')[:10]}")


def admin_stats(stats: Dict[str, Any]) -> str:
    return (f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 Total Users: {stats.get('total_users', 0)}\n"
            f"📈 New Today: {stats.get('new_today', 0)}\n"
            f"📦 Total Orders: {stats.get('total_orders', 0)}\n"
            f"💰 Total Points Spent: {stats.get('total_points_spent', 0)}\n"
            f"🚫 Banned Users: {stats.get('banned_users', 0)}\n"
            f"🚩 Flagged Users: {stats.get('flagged_users', 0)}")


def admin_broadcast_confirm(count: int) -> str:
    return f"📣 Send this message to {count} users?"


def admin_broadcast_progress(sent: int, total: int) -> str:
    return f"📣 Broadcasting... {sent}/{total} sent"


def admin_broadcast_complete(success: int, failed: int) -> str:
    return (f"✅ <b>Broadcast Complete</b>\n\n"
            f"📤 Success: {success}\n"
            f"❌ Failed: {failed}")


def admin_support_ticket(ticket: Dict[str, Any]) -> str:
    return (f"🎫 <b>Support Ticket #{ticket['id']}</b>\n\n"
            f"👤 User: <code>{ticket['user_id']}</code>\n"
            f"📝 Message:\n{ticket['message']}\n\n"
            f"📅 {ticket.get('created_at', 'N/A')[:16]}")


def admin_settings(settings: Dict[str, str]) -> str:
    return (f"⚙️ <b>Settings</b>\n\n"
            f"🎯 Referral Points: {settings.get('referral_points', '1')}\n"
            f"🎁 Daily Bonus: {settings.get('daily_bonus_points', '10')}\n"
            f"⚠️ Penalty Mode: {settings.get('penalty_mode', 'false').upper()}")


# ==================== ERRORS ====================

def error_generic(lang: str) -> str:
    return t(lang,
        "❌ حدث خطأ. يرجى المحاولة مرة أخرى.",
        "❌ An error occurred. Please try again.")


def error_banned(lang: str) -> str:
    return t(lang,
        "🚫 تم حظرك من استخدام هذا البوت.",
        "🚫 You have been banned from using this bot.")


def error_not_admin(lang: str) -> str:
    return t(lang,
        "⛔ ليس لديك صلاحية الوصول.",
        "⛔ You don't have permission to access this.")


def error_setup_incomplete(lang: str) -> str:
    return t(lang,
        "⚠️ يرجى إكمال إعداد حسابك أولاً. اضغط /start",
        "⚠️ Please complete your account setup first. Press /start")


# ==================== WELCOME ====================

def welcome_message(lang: str, message: str = None) -> str:
    if message:
        return message
    return t(lang,
        "مرحباً بك في المتجر! 🎉\n\n"
        "استخدم الأزرار أدناه للتنقل.",
        "Welcome to the store! 🎉\n\n"
        "Use the buttons below to navigate.")
