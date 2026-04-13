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


# ==================== V2 NEW MESSAGES ====================

# --- Buy Points with Stars ---

def buy_points_rate_info(lang: str, rate: int) -> str:
    return t(lang,
        f"💎 <b>شراء نقاط بنجوم Telegram</b>\n\n"
        f"📊 السعر الحالي: 1 نقطة = {rate} ⭐\n\n"
        "اختر باقة أو استخدم مبلغ مخصص:",
        f"💎 <b>Buy Points with Telegram Stars</b>\n\n"
        f"📊 Current rate: 1 pt = {rate} ⭐\n\n"
        "Select a package or use custom amount:")


def buy_points_custom_prompt(lang: str) -> str:
    return t(lang,
        "➕ <b>مبلغ مخصص</b>\n\n"
        "أدخل عدد النقاط الذي تريده:",
        f"➕ <b>Custom Amount</b>\n\n"
        "Enter the number of points you want:")


def buy_points_custom_confirm(lang: str, points: int, stars_cost: int, balance: int) -> str:
    return t(lang,
        f"🛒 <b>تأكيد الشراء</b>\n\n"
        f"💰 تريد: {points} نقطة\n"
        f"⭐ التكلفة: {stars_cost} ⭐\n"
        f"💳 رصيدك: {balance} نقطة\n\n"
        "هل تريد المتابعة؟",
        f"🛒 <b>Purchase Confirmation</b>\n\n"
        f"💰 You want: {points} pts\n"
        f"⭐ Cost: {stars_cost} ⭐\n"
        f"💳 Your balance: {balance} pts\n\n"
        "Proceed?")


def buy_points_receipt(lang: str, order_id: str, points: int, stars_paid: int) -> str:
    return t(lang,
        f"🧾 <b>إيصال الشراء</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف: <code>{order_id}</code>\n"
        f"💰 النقاط: {points} نقطة\n"
        f"⭐ المدفوع: {stars_paid} ⭐\n"
        f"📅 التاريخ: {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"✅ تم التسليم",
        f"🧾 <b>Order Receipt</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 Order ID: <code>{order_id}</code>\n"
        f"💰 Points: {points} pts\n"
        f"⭐ Paid: {stars_paid} ⭐\n"
        f"📅 Date: {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"✅ Delivered")


# --- Buy Stars with Points (Withdrawal) ---

def buy_stars_rate_info(lang: str, rate: int) -> str:
    return t(lang,
        f"⭐ <b>شراء نجوم بالنقاط</b>\n\n"
        f"📊 السعر الحالي: {rate} نقطة = 1 ⭐\n\n"
        "أدخل عدد النجوم الذي تريده:",
        f"⭐ <b>Buy Stars with Points</b>\n\n"
        f"📊 Current rate: {rate} pts = 1 ⭐\n\n"
        "Enter how many stars you want:")


def buy_stars_confirm(lang: str, stars: int, points_cost: int, balance: int) -> str:
    return t(lang,
        f"🛒 <b>تأكيد الطلب</b>\n\n"
        f"⭐ تريد: {stars} نجوم\n"
        f"💰 التكلفة: {points_cost} نقطة\n"
        f"💳 رصيدك: {balance} نقطة {'✅' if balance >= points_cost else '❌'}\n\n"
        "هل تريد تأكيد الطلب؟",
        f"🛒 <b>Order Confirmation</b>\n\n"
        f"⭐ You want: {stars} stars\n"
        f"💰 Cost: {points_cost} pts\n"
        f"💳 Your balance: {balance} pts {'✅' if balance >= points_cost else '❌'}\n\n"
        "Confirm order?")


def buy_stars_success(lang: str, order_id: str, stars: int, points_deducted: int) -> str:
    return t(lang,
        f"✅ <b>تم إنشاء طلبك!</b>\n\n"
        f"🆔 رقم الطلب: <code>{order_id}</code>\n"
        f"⭐ النجوم المطلوبة: {stars}\n"
        f"💰 النقاط المخصومة: {points_deducted}\n\n"
        f"🕐 الطلب قيد المراجعة. سيتم إعلامك عند التسليم.\n"
        f"⏰ لديك 24 ساعة لتأكيد الاستلام.",
        f"✅ <b>Order Created!</b>\n\n"
        f"🆔 Order ID: <code>{order_id}</code>\n"
        f"⭐ Stars requested: {stars}\n"
        f"💰 Points deducted: {points_deducted}\n\n"
        f"🕐 Order is pending review. You'll be notified when delivered.\n"
        f"⏰ You have 24 hours to confirm receipt.")


def star_order_status(lang: str, order: dict) -> str:
    status = order.get('status', 'pending')
    status_text = {
        'pending': t(lang, "🕐 قيد الانتظار", "🕐 Pending"),
        'delivered': t(lang, "✅ تم التسليم", "✅ Delivered"),
        'confirmed': t(lang, "💚 مؤكد", "💚 Confirmed"),
        'cancelled': t(lang, "❌ ملغي", "❌ Cancelled")
    }.get(status, status)

    text = (f"⭐ <b>طلب نجوم #{order['order_id']}</b>\n\n"
            f"⭐ النجوم: {order['stars_amount']}\n"
            f"💰 النقاط: {order['points_cost']}\n"
            f"📊 الحالة: {status_text}\n"
            f"📅 التاريخ: {str(order.get('created_at', ''))[:16]}")

    if status == 'cancelled' and order.get('points_cost'):
        text += f"\n💰 {t(lang, 'تم إرجاع', 'Refunded')}: {order['points_cost']} {t(lang, 'نقطة', 'pts')}"

    return text


def star_order_auto_cancelled(lang: str, order_id: str, points_refunded: int) -> str:
    return t(lang,
        f"⏰ <b>تم إلغاء الطلب تلقائياً</b>\n\n"
        f"طلبك #{order_id} تم إلغاؤه بعد 24 ساعة.\n"
        f"💰 تم إرجاع {points_refunded} نقطة إلى رصيدك.",
        f"⏰ <b>Order Auto-Cancelled</b>\n\n"
        f"Your order #{order_id} was cancelled after 24h timeout.\n"
        f"💰 {points_refunded} points have been refunded to your balance.")


def star_order_dispute_notification(lang: str, order_id: str) -> str:
    return t(lang,
        f"⚠️ <b>تم الإبلاغ عن مشكلة</b>\n\n"
        f"تم إرسال إشعار للمسؤولين للتحقيق في طلبك #{order_id}.",
        f"⚠️ <b>Dispute Reported</b>\n\n"
        f"Admins have been notified to investigate your order #{order_id}.")


# --- Insufficient Points ---

def insufficient_points_smart(lang: str, needed: int) -> str:
    return t(lang,
        f"❌ <b>رصيد غير كافٍ</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"تحتاج <b>{needed} نقطة إضافية</b> لشراء هذا المنتج.\n\n"
        "كيف تحصل على نقاط أكثر:",
        f"❌ <b>Not Enough Points</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"You need <b>{needed} more points</b> to buy this.\n\n"
        "How to get more points:")


# --- Restricted Account ---

def account_restricted(lang: str) -> str:
    return t(lang,
        "🚫 <b>حسابك مقيد</b>\n\n"
        "لا يمكنك إجراء عمليات شراء في الوقت الحالي.\n"
        "تواصل مع الدعم للمساعدة.",
        "🚫 <b>Account Restricted</b>\n\n"
        "You cannot make purchases at this time.\n"
        "Contact support for help.")


# --- Ads System ---

def ads_home(lang: str) -> str:
    return t(lang,
        "📺 <b>شاهد الإعلانات</b>\n\n"
        "شاهد الإعلانات واحصل على نقاط مكافأة!\n"
        "اختر إعلاناً من القائمة أدناه:",
        f"📺 <b>Watch Ads</b>\n\n"
        "Watch ads and earn bonus points!\n"
        "Select an ad from the list below:")


def ad_detail(lang: str, ad: dict) -> str:
    return t(lang,
        f"📢 <b>{ad['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 المكافأة: {ad['points_reward']} نقطة\n\n"
        "🔗 اضغط على الرابط أدناه، قم بزيارة الصفحة،\n"
        "خذ لقطة شاشة، ثم أرسلها هنا.",
        f"📢 <b>{ad['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Reward: {ad['points_reward']} points\n\n"
        "🔗 Click the link below, visit the page,\n"
        "take a screenshot, then send it here.")


def ad_claim_submitted(lang: str) -> str:
    return t(lang,
        "✅ <b>تم إرسال لقطة الشاشة!</b>\n\n"
        "🕐 الحالة: قيد مراجعة المسؤول\n"
        "سيتم إعلامك عند الموافقة.",
        "✅ <b>Screenshot submitted!</b>\n\n"
        "🕐 Status: Pending admin review\n"
        "You'll be notified when approved.")


def ad_claim_approved(lang: str, points: int) -> str:
    return t(lang,
        f"✅ <b>تمت الموافقة على مطالبتك!</b>\n\n"
        f"💰 +{points} نقطة تمت إضافتها إلى رصيدك.",
        f"✅ <b>Your ad claim was approved!</b>\n\n"
        f"💰 +{points} points added to your balance.")


def ad_claim_rejected(lang: str, reason: str) -> str:
    return t(lang,
        f"❌ <b>تم رفض مطالبتك</b>\n\n"
        f"السبب: {reason}\n"
        "يمكنك المحاولة مرة أخرى.",
        f"❌ <b>Your ad claim was rejected.</b>\n\n"
        f"Reason: {reason}\n"
        "You can try again.")


def ad_already_claimed(lang: str) -> str:
    return t(lang,
        "✅ لقد طالبت بهذا الإعلان مسبقاً.",
        "✅ You have already claimed this ad.")


def ad_pending_claim(lang: str) -> str:
    return t(lang,
        "🕐 لديك مطالبة معلقة لهذا الإعلان.",
        "🕐 You have a pending claim for this ad.")


def ad_cooldown(lang: str, hours: int, minutes: int) -> str:
    return t(lang,
        f"⏰ متاح خلال {hours} ساعة و {minutes} دقيقة",
        f"⏰ Available in {hours}h {minutes}m")


# --- Admin Messages (English only) ---

def admin_quick_stats(stats: dict) -> str:
    return (f"📊 <b>Right Now:</b>\n\n"
            f"🕐 {stats.get('pending_star_orders', 0)} pending star orders\n"
            f"📦 {stats.get('out_of_stock_products', 0)} products out of stock\n"
            f"🎫 {stats.get('open_tickets', 0)} open support tickets\n"
            f"👥 +{stats.get('new_users_today', 0)} new users today")


def admin_star_order_notification(order: dict) -> str:
    return (f"⭐ <b>New Star Withdrawal Request</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 Order: #{order['order_id']}\n"
            f"👤 User: @{order.get('username', 'N/A')} (ID: {order['user_id']})\n"
            f"⭐ Stars requested: {order['stars_amount']}\n"
            f"💰 Points deducted: {order['points_cost']}\n"
            f"📅 Expires in: 24 hours")


def admin_points_purchase_notification(points: int, stars_paid: int, user_id: int, username: str) -> str:
    return (f"⭐ <b>Points Purchase</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 @{username} (ID: {user_id})\n"
            f"💰 {points} pts purchased\n"
            f"⭐ {stars_paid} Stars paid")


def admin_low_stock_alert(product_name: str, remaining: int, waiting_count: int) -> str:
    return (f"⚠️ <b>Low Stock Alert</b>\n\n"
            f"Product: {product_name}\n"
            f"Remaining: {remaining} items\n"
            f"Waiting list: {waiting_count} users")


def admin_restock_notification(product_name: str, added: int, total: int, waiting_count: int) -> str:
    return (f"✅ <b>Restock Complete</b>\n\n"
            f"Added {added} items to {product_name}\n"
            f"📦 Total stock now: {total}\n"
            f"🔔 Notifying {waiting_count} waiting users...")


def admin_user_dispute_notification(username: str, order_id: str) -> str:
    return (f"⚠️ <b>User Dispute</b>\n\n"
            f"User @{username} disputed delivery for order #{order_id}")


def admin_channel_status(channel: dict) -> str:
    status_icon = "✅" if channel.get('is_active') else "❌"
    status_text = "Active" if channel.get('is_active') else "Inactive"
    return (f"📢 <b>Channel Details</b>\n\n"
            f"{status_icon} Name: {channel.get('channel_name', 'N/A')}\n"
            f"🔗 URL: {channel.get('channel_url', 'N/A')}\n"
            f"🆔 ID: <code>{channel.get('channel_id', 'N/A')}</code>\n"
            f"📊 Status: {status_text}")


def admin_user_profile_v2(user: dict) -> str:
    flagged = "🚩 YES" if user.get('miniapp_flagged') else "✅ No"
    banned = "🚫 YES" if user.get('is_banned') else "✅ No"
    restricted = "🚫 Restricted" if user.get('is_restricted') else "✅ Normal"
    notes = user.get('admin_notes', 'None')

    return (f"👤 <b>User Profile</b>\n\n"
            f"🆔 ID: <code>{user['telegram_id']}</code>\n"
            f"👤 Username: @{user.get('username', 'N/A')}\n"
            f"📛 Name: {user.get('first_name', 'N/A')}\n"
            f"💰 Points: {user.get('points', 0)}\n"
            f"📊 Total Earned: {user.get('total_earned', 0)}\n"
            f"📊 Total Spent: {user.get('total_spent', 0)}\n"
            f"🚫 Banned: {banned}\n"
            f"🔒 Restricted: {restricted}\n"
            f"🚩 Flagged: {flagged}\n"
            f"📝 Notes: {notes}\n"
            f"📅 Joined: {str(user.get('joined_at', 'N/A'))[:10]}")


def admin_ad_detail(ad: dict) -> str:
    type_text = "Once Per User" if ad.get('is_once_per_user') else f"Cooldown ({ad.get('cooldown_hours', 24)}h)"
    status_text = "Active" if ad.get('is_active') else "Inactive"
    return (f"📢 <b>Ad: {ad['title']}</b>\n\n"
            f"🔗 URL: {ad.get('url', 'N/A')}\n"
            f"💰 Reward: {ad['points_reward']} pts\n"
            f"📋 Type: {type_text}\n"
            f"📊 Status: {status_text}\n"
            f"🏆 Total Claims: {ad.get('total_claims', 0)}")


def admin_ad_claim_detail(claim: dict, ad_title: str) -> str:
    return (f"📸 <b>Ad Claim Request</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 @{claim.get('username', 'N/A')} (ID: {claim['user_id']})\n"
            f"📢 Ad: {ad_title}\n"
            f"💰 Reward: {claim.get('points_reward', 0)} pts\n"
            f"📅 Submitted: {str(claim.get('submitted_at', ''))[:16]}")


def admin_reject_reason_prompt() -> str:
    return "Enter rejection reason:"


def admin_edit_field_prompt(field_name: str) -> str:
    return f"Enter new {field_name}:"


# --- Penalty Notifications (V2 improved) ---

def penalty_deducted_v2(lang: str, points: int, referred_name: str, channel_name: str, new_balance: int) -> str:
    return t(lang,
        f"⚠️ <b>تم خصم النقاط</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 @{referred_name} غادر <b>{channel_name}</b>\n"
        f"💰 -{points} نقطة تم خصمها من رصيدك\n"
        f"💳 الرصيد الجديد: {new_balance} نقطة\n\n"
        "يمكنهم استعادة نقاطك بالانضمام مرة أخرى للقناة.",
        f"⚠️ <b>Points Deducted</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 @{referred_name} left <b>{channel_name}</b>\n"
        f"💰 -{points} points deducted from your balance\n"
        f"💳 New balance: {new_balance} points\n\n"
        "They can restore your points by rejoining the channel.")


def penalty_restored_v2(lang: str, points: int, referred_name: str, channel_name: str, new_balance: int) -> str:
    return t(lang,
        f"✅ <b>تم استرجاع النقاط</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 @{referred_name} عاد إلى <b>{channel_name}</b>\n"
        f"💰 +{points} نقطة تمت إضافتها إلى رصيدك\n"
        f"💳 الرصيد الجديد: {new_balance} نقطة",
        f"✅ <b>Points Restored</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 @{referred_name} rejoined <b>{channel_name}</b>\n"
        f"💰 +{points} points restored to your balance\n"
        f"💳 New balance: {new_balance} points")


# --- Restock Notification (V2 improved) ---

def restock_notification_user(lang: str, product_name: str, stock: int) -> str:
    return t(lang,
        f"🎉 <b>عاد المنتج!</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>{product_name}</b> متوفر مرة أخرى!\n"
        f"المخزون: {stock} — الأسبقية للأوائل.",
        f"🎉 <b>Back in Stock!</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>{product_name}</b> is available again!\n"
        f"Stock: {stock} items — first come first served.")


# --- Order Receipt (V2) ---

def order_receipt(lang: str, order_id: str, product_name: str, points_paid: int, date_str: str) -> str:
    return t(lang,
        f"🧾 <b>إيصال الطلب</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 رقم الطلب: <code>{order_id}</code>\n"
        f"📦 المنتج: {product_name}\n"
        f"💰 المدفوع: {points_paid} نقطة\n"
        f"📅 التاريخ: {date_str}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"✅ تم التسليم",
        f"🧾 <b>Order Receipt</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 Order ID: <code>{order_id}</code>\n"
        f"📦 Product: {product_name}\n"
        f"💰 Paid: {points_paid} pts\n"
        f"📅 Date: {date_str}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"✅ Delivered")


# ==================== WELCOME ====================

def welcome_message(lang: str, message: str = None) -> str:
    if message:
        return message
    return t(lang,
        "مرحباً بك في المتجر! 🎉\n\n"
        "استخدم الأزرار أدناه للتنقل.",
        "Welcome to the store! 🎉\n\n"
        "Use the buttons below to navigate.")
