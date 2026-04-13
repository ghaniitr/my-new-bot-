"""
Keyboard layouts for Telegram Store Bot.
All inline keyboards with emoji-prefixed buttons.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import config


def t(lang: str, ar: str, en: str) -> str:
    """Helper to return message based on language."""
    return ar if lang == 'ar' else en


# ==================== LANGUAGE SELECTION ====================

def language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇩🇿 العربية", callback_data="lang:ar"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
        ]
    ])


# ==================== MAIN MENU ====================

def main_menu_keyboard(lang: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="🛍️ " + ("المتجر" if lang == 'ar' else "Store"), callback_data="menu:store"),
            InlineKeyboardButton(text="💰 " + ("نقاطي" if lang == 'ar' else "My Points"), callback_data="menu:points")
        ],
        [
            InlineKeyboardButton(text="🔗 " + ("إحالة" if lang == 'ar' else "Referral"), callback_data="menu:referral"),
            InlineKeyboardButton(text="🎁 " + ("مكافأة يومية" if lang == 'ar' else "Daily Bonus"), callback_data="menu:daily_bonus")
        ],
        [
            InlineKeyboardButton(text="💎 " + ("شراء نقاط" if lang == 'ar' else "Buy Points"), callback_data="menu:buy_points"),
            InlineKeyboardButton(text="📺 " + ("شاهد الإعلانات" if lang == 'ar' else "Watch Ads"), callback_data="menu:ads")
        ],
        [
            InlineKeyboardButton(text="📩 " + ("الدعم" if lang == 'ar' else "Support"), callback_data="menu:support"),
            InlineKeyboardButton(text="🌐 " + ("تغيير اللغة" if lang == 'ar' else "Language"), callback_data="menu:language")
        ]
    ]

    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin:panel")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== BACK BUTTON ====================

def back_button(lang: str, callback_data: str = "menu:main") -> InlineKeyboardMarkup:
    """Single back button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ " + ("رجوع" if lang == 'ar' else "Back"), callback_data=callback_data)]
    ])


# ==================== MINI APP ====================

def miniapp_keyboard(lang: str, user_id: int) -> InlineKeyboardMarkup:
    """Mini app verification keyboard."""
    miniapp_url = f"{config.MINIAPP_URL}?user_id={user_id}&lang={lang}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔒 " + ("فتح التطبيق" if lang == 'ar' else "Open App"),
            web_app=WebAppInfo(url=miniapp_url)
        )],
        [InlineKeyboardButton(
            text="⏳ " + ("في انتظار التحقق..." if lang == 'ar' else "Waiting for verification..."),
            callback_data="miniapp:waiting"
        )]
    ])


def miniapp_verified_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Mini app verified - continue button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➡️ " + ("متابعة" if lang == 'ar' else "Continue"),
            callback_data="miniapp:continue"
        )]
    ])


# ==================== CHANNELS ====================

def channels_keyboard(lang: str, channels: list) -> InlineKeyboardMarkup:
    """Channel join buttons."""
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch.get('channel_name', 'Channel')}",
            url=ch.get('channel_url', '#')
        )])
    
    buttons.append([InlineKeyboardButton(
        text="✅ " + ("انضممت إلى جميع القنوات" if lang == 'ar' else "I joined all channels"),
        callback_data="check_channels"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== STORE ====================

def categories_keyboard(lang: str, categories: list) -> InlineKeyboardMarkup:
    """Categories list keyboard."""
    buttons = []
    for cat in categories:
        name = cat['name_ar'] if lang == 'ar' else cat['name_en']
        buttons.append([InlineKeyboardButton(
            text=f"📂 {name}",
            callback_data=f"cat:{cat['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(lang: str, products: list) -> InlineKeyboardMarkup:
    """Products list keyboard."""
    buttons = []
    for prod in products:
        name = prod['name_ar'] if lang == 'ar' else prod['name_en']
        stock_icon = "✅" if prod['stock'] > 0 else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{stock_icon} {name} — {prod['points_price']} pts",
            callback_data=f"prod:{prod['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:store"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(lang: str, product: dict, user_points: int, 
                            on_waiting_list: bool = False) -> InlineKeyboardMarkup:
    """Product detail keyboard."""
    buttons = []
    stock = product['stock']
    price = product['points_price']
    
    if stock > 0:
        if user_points >= price:
            buttons.append([InlineKeyboardButton(
                text="🛒 " + (f"شراء بـ {price} نقطة" if lang == 'ar' else f"Buy for {price} points"),
                callback_data=f"buy:{product['id']}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="❌ " + ("رصيد غير كافٍ" if lang == 'ar' else "Insufficient balance"),
                callback_data="ignore"
            )])
    else:
        if on_waiting_list:
            buttons.append([InlineKeyboardButton(
                text="✅ " + ("في قائمة الانتظار" if lang == 'ar' else "On waiting list"),
                callback_data="ignore"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="🔔 " + ("أبلغني عند التوفر" if lang == 'ar' else "Notify me when available"),
                callback_data=f"wait:{product['id']}"
            )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data=f"cat:{product['category_id']}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def purchase_confirm_keyboard(lang: str, product_id: int) -> InlineKeyboardMarkup:
    """Purchase confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ " + ("تأكيد" if lang == 'ar' else "Confirm"),
                callback_data=f"confirm_buy:{product_id}"
            ),
            InlineKeyboardButton(
                text="❌ " + ("إلغاء" if lang == 'ar' else "Cancel"),
                callback_data=f"prod:{product_id}"
            )
        ]
    ])


# ==================== POINTS ====================

def points_keyboard(lang: str) -> InlineKeyboardMarkup:
    """My points keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎟️ " + ("إدخال كوبون" if lang == 'ar' else "Enter Coupon"),
                callback_data="points:coupon"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 " + ("طلباتي" if lang == 'ar' else "My Orders"),
                callback_data="points:orders"
            ),
            InlineKeyboardButton(
                text="⭐ " + ("طلبات النجوم" if lang == 'ar' else "Star Orders"),
                callback_data="points:star_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ " + ("شراء نجوم" if lang == 'ar' else "Buy Stars"),
                callback_data="menu:buy_stars"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
                callback_data="menu:main"
            )
        ]
    ])


def orders_keyboard(lang: str, orders: list) -> InlineKeyboardMarkup:
    """Orders list keyboard."""
    buttons = []
    for order in orders:
        buttons.append([InlineKeyboardButton(
            text=f"📦 {order['order_id'][:15]}...",
            callback_data=f"order:{order['order_id']}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:points"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_detail_keyboard(lang: str, order_id: str) -> InlineKeyboardMarkup:
    """Order detail - back button only."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="points:orders"
        )]
    ])


# ==================== DAILY BONUS ====================

def daily_bonus_available_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Daily bonus available keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎁 " + ("استلام المكافأة" if lang == 'ar' else "Claim Bonus"),
            callback_data="daily:claim"
        )],
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="menu:main"
        )]
    ])


def daily_bonus_wait_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Daily bonus waiting keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="menu:main"
        )]
    ])


# ==================== BUY POINTS ====================

def buy_points_keyboard(lang: str, packages: list) -> InlineKeyboardMarkup:
    """Buy points packages keyboard."""
    buttons = []
    for pkg in packages:
        buttons.append([InlineKeyboardButton(
            text=f"⭐ {pkg['stars_amount']} Stars → {pkg['points_amount']} Points",
            callback_data=f"stars_pkg:{pkg['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== REFERRAL ====================

def referral_keyboard(lang: str, referral_link: str) -> InlineKeyboardMarkup:
    """Referral keyboard."""
    share_text = ("انضم إلى هذا المتجر الرائع واحصل على مكافآت! 🎉" 
                  if lang == 'ar' else 
                  "Join this awesome store and get rewards! 🎉")
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📤 " + ("مشاركة الرابط" if lang == 'ar' else "Share Link"),
            url=f"https://t.me/share/url?url={referral_link}&text={share_text}"
        )],
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="menu:main"
        )]
    ])


# ==================== SUPPORT ====================

def support_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Support keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="menu:main"
        )]
    ])


# ==================== ADMIN PANEL ====================

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Products", callback_data="admin:products"),
            InlineKeyboardButton(text="📂 Categories", callback_data="admin:categories")
        ],
        [
            InlineKeyboardButton(text="📢 Channels", callback_data="admin:channels"),
            InlineKeyboardButton(text="🎟️ Coupons", callback_data="admin:coupons")
        ],
        [
            InlineKeyboardButton(text="👥 Users", callback_data="admin:users"),
            InlineKeyboardButton(text="👮 Admins", callback_data="admin:admins")
        ],
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="admin:stats"),
            InlineKeyboardButton(text="📣 Broadcast", callback_data="admin:broadcast")
        ],
        [
            InlineKeyboardButton(text="🎫 Support", callback_data="admin:support"),
            InlineKeyboardButton(text="⭐ Stars Packages", callback_data="admin:stars")
        ],
        [
            InlineKeyboardButton(text="⭐ Star Orders", callback_data="admin:star_orders"),
            InlineKeyboardButton(text="📺 Ads", callback_data="admin:ads")
        ],
        [
            InlineKeyboardButton(text="⚙️ Settings", callback_data="admin:settings")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu:main")
        ]
    ])


def admin_products_list_keyboard(products: list, page: int = 0) -> InlineKeyboardMarkup:
    """Admin products list keyboard."""
    buttons = []
    for prod in products[:10]:
        icon = "👁️" if prod.get('is_visible') else "🙈"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {prod.get('name_en', 'Unnamed')} ({prod.get('stock', 0)} left)",
            callback_data=f"admin_prod:{prod['id']}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"admin_prods:{page-1}"))
    if len(products) > 10:
        nav_buttons.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"admin_prods:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="➕ Add Product", callback_data="admin:add_product")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_manage_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Admin product management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit Name EN", callback_data=f"admin_edit_prod:{product_id}:name_en"),
            InlineKeyboardButton(text="✏️ Edit Name AR", callback_data=f"admin_edit_prod:{product_id}:name_ar")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Desc EN", callback_data=f"admin_edit_prod:{product_id}:desc_en"),
            InlineKeyboardButton(text="✏️ Edit Desc AR", callback_data=f"admin_edit_prod:{product_id}:desc_ar")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Price", callback_data=f"admin_edit_prod:{product_id}:price"),
            InlineKeyboardButton(text="📦 Add Stock", callback_data=f"admin_add_stock:{product_id}")
        ],
        [
            InlineKeyboardButton(text="👁️ Toggle Visibility", callback_data=f"admin_toggle_prod:{product_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Delete Product", callback_data=f"admin_del_prod:{product_id}")
        ],
        [
            InlineKeyboardButton(text="◀️ Back", callback_data="admin:products")
        ]
    ])


def admin_categories_list_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Admin categories list keyboard."""
    buttons = []
    for cat in categories:
        icon = "✅" if cat.get('is_active') else "❌"
        name = cat.get('name_en', 'Unnamed')
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {name}",
            callback_data=f"admin_cat:{cat['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Add Category", callback_data="admin:add_category")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_category_manage_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Admin category management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅/❌ Toggle Active", callback_data=f"admin_toggle_cat:{category_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"admin_del_cat:{category_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:categories")]
    ])


def admin_channels_list_keyboard(channels: list) -> InlineKeyboardMarkup:
    """Admin channels list keyboard."""
    buttons = []
    for ch in channels:
        icon = "✅" if ch.get('is_active') else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {ch.get('channel_name', 'Unnamed')}",
            callback_data=f"admin_channel:{ch['channel_id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Add Channel", callback_data="admin:add_channel")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_coupons_list_keyboard(coupons: list) -> InlineKeyboardMarkup:
    """Admin coupons list keyboard."""
    buttons = []
    for coupon in coupons:
        icon = "✅" if coupon.get('is_active') else "❌"
        code = coupon.get('code', 'UNKNOWN')
        used = coupon.get('used_count', 0)
        max_uses = coupon.get('max_uses', 1)
        points = coupon.get('points_value', 0)
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {code} — {points}pts ({used}/{max_uses})",
            callback_data=f"admin_coupon:{coupon['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Generate Coupon", callback_data="admin:add_coupon")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_coupon_manage_keyboard(coupon_id: int) -> InlineKeyboardMarkup:
    """Admin coupon management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅/❌ Toggle Active", callback_data=f"admin_toggle_coupon:{coupon_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"admin_del_coupon:{coupon_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:coupons")]
    ])


def admin_user_profile_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Admin user profile actions keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add Points", callback_data=f"admin_user_add:{user_id}"),
            InlineKeyboardButton(text="➖ Remove Points", callback_data=f"admin_user_rem:{user_id}")
        ],
        [
            InlineKeyboardButton(text="🚫 Ban/Unban", callback_data=f"admin_user_ban:{user_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:users")]
    ])


def admin_admins_list_keyboard(admins: list, super_admin_id: int) -> InlineKeyboardMarkup:
    """Admin admins list keyboard."""
    buttons = []
    for admin in admins:
        admin_id = admin.get('telegram_id')
        if admin_id != super_admin_id:
            buttons.append([InlineKeyboardButton(
                text=f"👤 {admin_id} ➖ Remove",
                callback_data=f"admin_remove_admin:{admin_id}"
            )])
    
    buttons.append([InlineKeyboardButton(text="➕ Add Admin", callback_data="admin:add_admin")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_support_tickets_keyboard(tickets: list) -> InlineKeyboardMarkup:
    """Admin support tickets list keyboard."""
    buttons = []
    for ticket in tickets[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"🎫 #{ticket['id']} — {ticket.get('message', '')[:30]}...",
            callback_data=f"admin_ticket:{ticket['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_ticket_manage_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Admin ticket management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Reply", callback_data=f"admin_reply_ticket:{ticket_id}"),
            InlineKeyboardButton(text="✅ Close", callback_data=f"admin_close_ticket:{ticket_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:support")]
    ])


def admin_stars_packages_keyboard(packages: list) -> InlineKeyboardMarkup:
    """Admin stars packages list keyboard."""
    buttons = []
    for pkg in packages:
        icon = "✅" if pkg.get('is_active') else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} ⭐{pkg['stars_amount']} → {pkg['points_amount']}pts",
            callback_data=f"admin_stars_pkg:{pkg['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Add Package", callback_data="admin:add_stars_pkg")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_stars_package_manage_keyboard(pkg_id: int) -> InlineKeyboardMarkup:
    """Admin stars package management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅/❌ Toggle Active", callback_data=f"admin_toggle_stars:{pkg_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"admin_del_stars:{pkg_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:stars")]
    ])


def admin_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Admin settings keyboard."""
    penalty_mode = settings.get('penalty_mode', 'false')
    penalty_text = "⚠️ Penalty Mode: ON" if penalty_mode.lower() == 'true' else "⚠️ Penalty Mode: OFF"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Referral Points", callback_data="admin_setting:referral_points")
        ],
        [
            InlineKeyboardButton(text="🎁 Daily Bonus Points", callback_data="admin_setting:daily_bonus_points")
        ],
        [
            InlineKeyboardButton(text="💬 Welcome Message AR", callback_data="admin_setting:welcome_ar")
        ],
        [
            InlineKeyboardButton(text="💬 Welcome Message EN", callback_data="admin_setting:welcome_en")
        ],
        [
            InlineKeyboardButton(text=penalty_text, callback_data="admin_toggle_penalty")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")]
    ])


def admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Admin broadcast confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="admin_broadcast:confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="admin:panel")
        ]
    ])


def cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Cancel action keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ " + ("إلغاء" if lang == 'ar' else "Cancel"),
            callback_data="admin:cancel"
        )]
    ])


# ==================== V2 NEW KEYBOARDS ====================

# --- Buy Points with Stars (Custom Amount) ---

def buy_points_custom_amount_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Buy points - custom amount button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ " + ("مبلغ مخصص" if lang == 'ar' else "Custom Amount"),
            callback_data="buy_points:custom"
        )],
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="menu:main"
        )]
    ])


def buy_points_confirm_keyboard(lang: str, points: int, stars: int) -> InlineKeyboardMarkup:
    """Confirm buy points payment."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✅ {t(lang, 'ادفع الآن', 'Pay Now')} ({stars} ⭐)",
            callback_data=f"buy_points_confirm:{points}"
        )],
        [InlineKeyboardButton(
            text="❌ " + ("إلغاء" if lang == 'ar' else "Cancel"),
            callback_data="menu:buy_points"
        )]
    ])


# --- Buy Stars with Points (Withdrawal) ---

def buy_stars_confirm_keyboard(lang: str, stars: int, points_cost: int) -> InlineKeyboardMarkup:
    """Confirm buy stars order."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ " + ("تأكيد" if lang == 'ar' else "Confirm"),
            callback_data=f"buy_stars_confirm:{stars}"
        )],
        [InlineKeyboardButton(
            text="❌ " + ("إلغاء" if lang == 'ar' else "Cancel"),
            callback_data="menu:main"
        )]
    ])


# --- Star Orders (User View) ---

def star_orders_keyboard(lang: str, orders: list) -> InlineKeyboardMarkup:
    """User's star orders list."""
    buttons = []
    for order in orders:
        status_icon = {"pending": "🕐", "delivered": "✅", "confirmed": "💚", "cancelled": "❌"}.get(order.get('status', 'pending'), "🕐")
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} {order['order_id']} — {order['stars_amount']}⭐",
            callback_data=f"star_order:{order['order_id']}"
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:points"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def star_order_pending_keyboard(lang: str, order_id: str) -> InlineKeyboardMarkup:
    """Star order pending - user can cancel."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ " + ("إلغاء الطلب" if lang == 'ar' else "Cancel Order"),
            callback_data=f"star_order_cancel:{order_id}"
        )],
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="points:star_orders"
        )]
    ])


def star_order_delivered_keyboard(lang: str, order_id: str) -> InlineKeyboardMarkup:
    """Star order delivered - user can confirm receipt."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ " + ("استلمت نجومي" if lang == 'ar' else "I Received My Stars"),
                callback_data=f"star_order_confirm:{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ " + ("لم أستلم" if lang == 'ar' else "I Did Not Receive"),
                callback_data=f"star_order_dispute:{order_id}"
            )
        ],
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="points:star_orders"
        )]
    ])


def star_order_confirmed_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Star order confirmed - closed."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="points:star_orders"
        )]
    ])


def star_order_cancelled_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Star order cancelled."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
            callback_data="points:star_orders"
        )]
    ])


# --- Admin Star Orders Dashboard ---

def admin_star_orders_keyboard(orders: list, filter_status: str = 'pending') -> InlineKeyboardMarkup:
    """Admin star orders dashboard."""
    buttons = []
    for order in orders[:15]:
        username = order.get('username', f"User {order['user_id']}")
        time_left = order.get('time_left', '?')
        buttons.append([InlineKeyboardButton(
            text=f"{order['order_id']} | {username} | {order['stars_amount']}⭐ | ⏰ {time_left}",
            callback_data=f"admin_star_order:{order['order_id']}"
        )])

    # Filter buttons
    filter_buttons = [
        InlineKeyboardButton(text="🕐 Pending" if filter_status != 'pending' else "✅ Pending", callback_data="admin_star_orders:pending"),
        InlineKeyboardButton(text="✅ Delivered" if filter_status != 'delivered' else "✅ Delivered", callback_data="admin_star_orders:delivered"),
    ]
    buttons.append(filter_buttons)

    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_star_order_manage_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Admin star order management."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Mark Delivered", callback_data=f"admin_star_deliver:{order_id}"),
            InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"admin_star_cancel:{order_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:star_orders")]
    ])


# --- Channel Management (V2 Overhaul) ---

def admin_channel_manage_keyboard(channel_id: str) -> InlineKeyboardMarkup:
    """Admin channel management."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit Name", callback_data=f"admin_edit_channel:{channel_id}:name"),
            InlineKeyboardButton(text="✏️ Edit URL", callback_data=f"admin_edit_channel:{channel_id}:url")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Channel ID", callback_data=f"admin_edit_channel:{channel_id}:channel_id")
        ],
        [
            InlineKeyboardButton(text="👁️ Toggle Active/Inactive", callback_data=f"admin_toggle_channel:{channel_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Remove", callback_data=f"admin_del_channel:{channel_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:channels")]
    ])


# --- Product Delivery Type Selection ---

def product_delivery_type_keyboard() -> InlineKeyboardMarkup:
    """Product delivery type selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Unlimited File", callback_data="admin_prod_type:unlimited_file")],
        [InlineKeyboardButton(text="🔒 One-Time File", callback_data="admin_prod_type:oncesell_file")],
        [InlineKeyboardButton(text="📝 One-Time Text", callback_data="admin_prod_type:oncesell_text")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="admin:products")]
    ])


# --- Insufficient Points Smart Redirect ---

def insufficient_points_keyboard(lang: str, product_id: int) -> InlineKeyboardMarkup:
    """Insufficient points - smart redirect."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💎 " + ("شراء نقاط" if lang == 'ar' else "Buy Points with Stars"),
            callback_data="menu:buy_points"
        )],
        [InlineKeyboardButton(
            text="🔗 " + ("إحالة أصدقاء" if lang == 'ar' else "Invite Friends"),
            callback_data="menu:referral"
        )],
        [InlineKeyboardButton(
            text="🎁 " + ("مكافأة يومية" if lang == 'ar' else "Daily Bonus"),
            callback_data="menu:daily_bonus"
        )],
        [InlineKeyboardButton(
            text="📺 " + ("شاهد الإعلانات" if lang == 'ar' else "Watch Ads"),
            callback_data="menu:ads"
        )],
        [InlineKeyboardButton(
            text="◀️ " + ("رجوع للمنتج" if lang == 'ar' else "Back to Product"),
            callback_data=f"prod:{product_id}"
        )]
    ])


# --- Admin User Profile Additions ---

def admin_user_profile_v2_keyboard(user_id: int, is_restricted: bool) -> InlineKeyboardMarkup:
    """Admin user profile V2 with restriction and notes."""
    restrict_text = "✅ Unrestrict" if is_restricted else "🚫 Restrict"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add Points", callback_data=f"admin_user_add:{user_id}"),
            InlineKeyboardButton(text="➖ Remove Points", callback_data=f"admin_user_rem:{user_id}")
        ],
        [
            InlineKeyboardButton(text=restrict_text, callback_data=f"admin_user_restrict:{user_id}"),
            InlineKeyboardButton(text="📝 Add/Edit Note", callback_data=f"admin_user_note:{user_id}")
        ],
        [
            InlineKeyboardButton(text="🚫 Ban/Unban", callback_data=f"admin_user_ban:{user_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:users")]
    ])


# --- Admin Settings V2 ---

def admin_settings_v2_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Admin settings V2 with stars and stock settings."""
    penalty_mode = settings.get('penalty_mode', 'false')
    penalty_text = "⚠️ Penalty Mode: ON" if penalty_mode.lower() == 'true' else "⚠️ Penalty Mode: OFF"
    stars_per_point = settings.get('stars_per_point', '4')
    stars_withdrawal = settings.get('stars_withdrawal_open', 'true')
    stars_withdrawal_text = "⭐ Stars Withdrawal: ON" if stars_withdrawal.lower() == 'true' else "⭐ Stars Withdrawal: OFF"
    low_stock = settings.get('low_stock_threshold', '5')

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"⭐ Stars per Point: {stars_per_point}", callback_data="admin_setting:stars_per_point")
        ],
        [
            InlineKeyboardButton(text=stars_withdrawal_text, callback_data="admin_toggle_stars_withdrawal")
        ],
        [
            InlineKeyboardButton(text=f"📦 Low Stock Threshold: {low_stock}", callback_data="admin_setting:low_stock_threshold")
        ],
        [
            InlineKeyboardButton(text="🎯 Referral Points", callback_data="admin_setting:referral_points")
        ],
        [
            InlineKeyboardButton(text="🎁 Daily Bonus Points", callback_data="admin_setting:daily_bonus_points")
        ],
        [
            InlineKeyboardButton(text="💬 Welcome Message AR", callback_data="admin_setting:welcome_ar")
        ],
        [
            InlineKeyboardButton(text="💬 Welcome Message EN", callback_data="admin_setting:welcome_en")
        ],
        [
            InlineKeyboardButton(text=penalty_text, callback_data="admin_toggle_penalty")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")]
    ])


# --- Ads Management (Admin) ---

def admin_ads_keyboard(ads: list) -> InlineKeyboardMarkup:
    """Admin ads list."""
    buttons = []
    for ad in ads:
        icon = "✅" if ad.get('is_active') else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} 📢 {ad['title']} — {ad['points_reward']}pts — {ad.get('total_claims', 0)} claims",
            callback_data=f"admin_ad:{ad['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="➕ Add Ad", callback_data="admin:add_ad")])
    buttons.append([InlineKeyboardButton(text="📸 Pending Claims", callback_data="admin:ad_claims_pending")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_ad_manage_keyboard(ad_id: int, is_cooldown: bool) -> InlineKeyboardMarkup:
    """Admin ad management."""
    type_text = "🔄 Cooldown" if is_cooldown else "1️⃣ Once Per User"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit Title", callback_data=f"admin_edit_ad:{ad_id}:title"),
            InlineKeyboardButton(text="✏️ Edit URL", callback_data=f"admin_edit_ad:{ad_id}:url")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Points", callback_data=f"admin_edit_ad:{ad_id}:points_reward")
        ],
        [
            InlineKeyboardButton(text=type_text, callback_data=f"admin_toggle_ad_type:{ad_id}")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Cooldown Hours", callback_data=f"admin_edit_ad:{ad_id}:cooldown_hours")
        ],
        [
            InlineKeyboardButton(text="👁️ Toggle Active", callback_data=f"admin_toggle_ad:{ad_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"admin_del_ad:{ad_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:ads")]
    ])


def admin_pending_claims_keyboard(claims: list) -> InlineKeyboardMarkup:
    """Admin pending ad claims."""
    buttons = []
    for claim in claims[:15]:
        username = claim.get('username', f"User {claim['user_id']}")
        buttons.append([InlineKeyboardButton(
            text=f"📸 {username} — Ad #{claim['ad_id']}",
            callback_data=f"admin_ad_claim:{claim['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:ads")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_ad_claim_manage_keyboard(claim_id: int) -> InlineKeyboardMarkup:
    """Admin ad claim management."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_ad_claim_approve:{claim_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_ad_claim_reject:{claim_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:ad_claims_pending")]
    ])


# --- Ads (User View) ---

def ads_list_keyboard(lang: str, ads: list) -> InlineKeyboardMarkup:
    """User ads list."""
    buttons = []
    for ad in ads:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ad['title']} — {ad['points_reward']} pts",
            callback_data=f"ad:{ad['id']}"
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:main"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ad_detail_keyboard(lang: str, ad: dict, has_pending: bool = False, has_approved: bool = False, cooldown_remaining: str = None) -> InlineKeyboardMarkup:
    """Ad detail screen."""
    buttons = []

    # Open ad link button
    buttons.append([InlineKeyboardButton(
        text="🌐 " + ("افتح رابط الإعلان" if lang == 'ar' else "Open Ad Link"),
        url=ad.get('url', '#')
    )])

    if has_approved:
        buttons.append([InlineKeyboardButton(
            text="✅ " + ("تم المطالبة مسبقاً" if lang == 'ar' else "Already Claimed"),
            callback_data="ignore"
        )])
    elif has_pending:
        buttons.append([InlineKeyboardButton(
            text="🕐 " + ("في انتظار المراجعة" if lang == 'ar' else "Pending Review"),
            callback_data="ignore"
        )])
    elif cooldown_remaining:
        buttons.append([InlineKeyboardButton(
            text=f"⏰ {cooldown_remaining}",
            callback_data="ignore"
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="📸 " + ("إرسال لقطة الشاشة" if lang == 'ar' else "Submit Screenshot"),
            callback_data=f"ad_submit:{ad['id']}"
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ " + ("رجوع" if lang == 'ar' else "Back"),
        callback_data="menu:ads"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
