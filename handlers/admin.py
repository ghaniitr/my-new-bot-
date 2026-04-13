"""
Admin handler for Telegram Store Bot.
Complete admin panel functionality.
"""

import random
import string
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    admin_panel_keyboard, admin_products_list_keyboard, admin_product_manage_keyboard,
    admin_categories_list_keyboard, admin_category_manage_keyboard,
    admin_channels_list_keyboard, admin_channel_manage_keyboard,
    admin_coupons_list_keyboard, admin_coupon_manage_keyboard,
    admin_user_profile_keyboard, admin_user_profile_v2_keyboard,
    admin_admins_list_keyboard,
    admin_support_tickets_keyboard, admin_ticket_manage_keyboard,
    admin_stars_packages_keyboard, admin_stars_package_manage_keyboard,
    admin_settings_keyboard, admin_settings_v2_keyboard,
    admin_broadcast_confirm_keyboard,
    back_button, cancel_keyboard,
    admin_star_orders_keyboard, admin_star_order_manage_keyboard,
    admin_ads_keyboard, admin_ad_manage_keyboard,
    admin_pending_claims_keyboard, admin_ad_claim_manage_keyboard,
    product_delivery_type_keyboard
)
import messages
from config import config

router = Router()


# ==================== ADMIN FSM STATES ====================

class AdminState(StatesGroup):
    """Admin FSM states."""
    # Products
    ADD_PRODUCT_NAME_EN = State()
    ADD_PRODUCT_NAME_AR = State()
    ADD_PRODUCT_DESC_EN = State()
    ADD_PRODUCT_DESC_AR = State()
    ADD_PRODUCT_TYPE = State()
    ADD_PRODUCT_PRICE = State()
    ADD_PRODUCT_FILE = State()
    ADD_PRODUCT_STOCK = State()
    EDIT_PRODUCT = State()
    ADD_STOCK = State()

    # Categories
    ADD_CATEGORY_NAME_EN = State()
    ADD_CATEGORY_NAME_AR = State()

    # Channels
    ADD_CHANNEL_ID = State()
    ADD_CHANNEL_NAME = State()
    ADD_CHANNEL_URL = State()

    # Coupons
    ADD_COUPON_CODE = State()
    ADD_COUPON_POINTS = State()
    ADD_COUPON_MAX_USES = State()
    ADD_COUPON_EXPIRY = State()

    # Users
    SEARCH_USER = State()
    USER_ADD_POINTS = State()
    USER_REMOVE_POINTS = State()

    # Admins
    ADD_ADMIN = State()

    # Broadcast
    BROADCAST_MESSAGE = State()
    BROADCAST_CONFIRM = State()

    # Support
    REPLY_TICKET = State()

    # Stars Packages
    ADD_STARS_PKG_STARS = State()
    ADD_STARS_PKG_POINTS = State()

    # Settings
    SETTING_VALUE = State()

    # Ads
    ADD_AD_TITLE = State()
    ADD_AD_URL = State()
    ADD_AD_POINTS = State()
    ADD_AD_TYPE = State()
    ADD_AD_COOLDOWN = State()


# ==================== ADMIN CHECK ====================

async def is_admin_check(telegram_id: int) -> bool:
    """Check if user is admin."""
    return await db.is_admin(telegram_id)


# ==================== ADMIN PANEL ====================

@router.callback_query(F.data == "admin:panel")
async def admin_panel(callback: CallbackQuery):
    """Show admin panel with quick stats."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    # Get quick stats
    pending_orders = await db.get_pending_star_orders_count()

    # Get out of stock products count
    all_products = await db.get_products(visible_only=True)
    oos_count = sum(1 for p in all_products if p.get('stock', 0) <= 0)

    # Get open tickets count
    open_tickets = await db.get_open_tickets()
    ticket_count = len(open_tickets)

    # Get new users today
    from datetime import datetime
    today = datetime.utcnow().strftime('%Y-%m-%d')
    new_users = await db.fetchone(
        "SELECT COUNT(*) as count FROM users WHERE DATE(joined_at) = ?",
        (today,)
    )
    new_today = new_users['count'] if new_users else 0

    stats_text = messages.admin_quick_stats({
        'pending_star_orders': pending_orders,
        'out_of_stock_products': oos_count,
        'open_tickets': ticket_count,
        'new_users_today': new_today
    })

    full_text = stats_text + "\n\n" + messages.admin_panel()

    await callback.message.edit_text(
        full_text,
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


# ==================== PRODUCTS ====================

@router.callback_query(F.data == "admin:products")
async def admin_products(callback: CallbackQuery):
    """Show products list."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    products = await db.get_products(visible_only=False)
    await callback.message.edit_text(
        messages.admin_products_list(),
        reply_markup=admin_products_list_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod:"))
async def admin_product_detail(callback: CallbackQuery):
    """Show product management."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📦 <b>{product['name_en']}</b>\n\n"
        f"Price: {product['points_price']} points\n"
        f"Stock: {product['stock']}\n"
        f"Type: {product['type']}\n"
        f"Visible: {'Yes' if product['is_visible'] else 'No'}",
        reply_markup=admin_product_manage_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Start add product flow."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    categories = await db.get_categories(active_only=True)
    if not categories:
        await callback.answer("No categories available. Create one first.", show_alert=True)
        return
    
    # Show category selection
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=f"📂 {cat['name_en']}",
            callback_data=f"admin_add_prod_cat:{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:products")])
    
    await callback.message.edit_text(
        "📦 <b>Add Product</b>\n\nSelect category:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_add_prod_cat:"))
async def admin_add_product_cat(callback: CallbackQuery, state: FSMContext):
    """Set category and ask for name EN."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)
    
    await state.set_state(AdminState.ADD_PRODUCT_NAME_EN)
    await callback.message.edit_text(
        "📦 <b>Add Product</b>\n\nEnter product name (English):",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_PRODUCT_NAME_EN)
async def admin_add_product_name_en(message: Message, state: FSMContext):
    """Save name EN and ask for name AR."""
    await state.update_data(name_en=message.text.strip())
    await state.set_state(AdminState.ADD_PRODUCT_NAME_AR)
    await message.answer(
        "📦 <b>Add Product</b>\n\nEnter product name (Arabic):",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_PRODUCT_NAME_AR)
async def admin_add_product_name_ar(message: Message, state: FSMContext):
    """Save name AR and ask for desc EN."""
    await state.update_data(name_ar=message.text.strip())
    await state.set_state(AdminState.ADD_PRODUCT_DESC_EN)
    await message.answer(
        "📦 <b>Add Product</b>\n\nEnter description (English) or send '-' to skip:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_PRODUCT_DESC_EN)
async def admin_add_product_desc_en(message: Message, state: FSMContext):
    """Save desc EN and ask for desc AR."""
    desc = message.text.strip()
    await state.update_data(desc_en='' if desc == '-' else desc)
    await state.set_state(AdminState.ADD_PRODUCT_DESC_AR)
    await message.answer(
        "📦 <b>Add Product</b>\n\nEnter description (Arabic) or send '-' to skip:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_PRODUCT_DESC_AR)
async def admin_add_product_desc_ar(message: Message, state: FSMContext):
    """Save desc AR and ask for type."""
    desc = message.text.strip()
    await state.update_data(desc_ar='' if desc == '-' else desc)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(text="📄 PDF", callback_data="admin_prod_type:pdf")],
        [InlineKeyboardButton(text="📦 ZIP", callback_data="admin_prod_type:zip")],
        [InlineKeyboardButton(text="🔑 Code/Key", callback_data="admin_prod_type:code")],
        [InlineKeyboardButton(text="👤 Account", callback_data="admin_prod_type:account")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="admin:products")]
    ]
    
    await message.answer(
        "📦 <b>Add Product</b>\n\nSelect product type:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith("admin_prod_type:"))
async def admin_add_product_type(callback: CallbackQuery, state: FSMContext):
    """Save type and ask for price."""
    product_type = callback.data.split(":")[1]
    await state.update_data(product_type=product_type)
    await state.set_state(AdminState.ADD_PRODUCT_PRICE)
    
    await callback.message.edit_text(
        "📦 <b>Add Product</b>\n\nEnter points price:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_PRODUCT_PRICE)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Save price and handle based on type."""
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number")
        return
    
    await state.update_data(price=price)
    data = await state.get_data()
    product_type = data.get('product_type')
    
    if product_type in ('pdf', 'zip'):
        await state.set_state(AdminState.ADD_PRODUCT_FILE)
        await message.answer(
            f"📦 <b>Add Product</b>\n\nUpload the {product_type.upper()} file:",
            reply_markup=cancel_keyboard('en')
        )
    else:
        await state.set_state(AdminState.ADD_PRODUCT_STOCK)
        await message.answer(
            "📦 <b>Add Product</b>\n\nEnter stock items (one per line):",
            reply_markup=cancel_keyboard('en')
        )


@router.message(AdminState.ADD_PRODUCT_FILE)
async def admin_add_product_file(message: Message, state: FSMContext):
    """Save file and create product."""
    if not message.document:
        await message.answer("❌ Please upload a file")
        return
    
    file_id = message.document.file_id
    data = await state.get_data()
    
    # Create product
    product_id = await db.create_product(
        category_id=data['category_id'],
        name_ar=data['name_ar'],
        name_en=data['name_en'],
        description_ar=data.get('desc_ar', ''),
        description_en=data.get('desc_en', ''),
        product_type=data['product_type'],
        points_price=data['price'],
        file_id=file_id
    )
    
    await state.clear()
    await message.answer(
        f"✅ Product created successfully!\nID: <code>{product_id}</code>",
        reply_markup=back_button('en', "admin:products"),
        parse_mode='HTML'
    )


@router.message(AdminState.ADD_PRODUCT_STOCK)
async def admin_add_product_stock(message: Message, state: FSMContext):
    """Save stock and create product."""
    items = message.text.strip().split('\n')
    items = [item.strip() for item in items if item.strip()]
    
    if not items:
        await message.answer("❌ Please enter at least one item")
        return
    
    data = await state.get_data()
    
    # Create product
    product_id = await db.create_product(
        category_id=data['category_id'],
        name_ar=data['name_ar'],
        name_en=data['name_en'],
        description_ar=data.get('desc_ar', ''),
        description_en=data.get('desc_en', ''),
        product_type=data['product_type'],
        points_price=data['price']
    )
    
    # Add stock
    await db.add_stock(product_id, items)
    
    await state.clear()
    await message.answer(
        f"✅ Product created with {len(items)} items in stock!\nID: <code>{product_id}</code>",
        reply_markup=back_button('en', "admin:products"),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("admin_add_stock:"))
async def admin_add_stock_start(callback: CallbackQuery, state: FSMContext):
    """Start adding stock."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminState.ADD_STOCK)
    
    await callback.message.edit_text(
        "📦 <b>Add Stock</b>\n\nEnter new items (one per line):",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_STOCK)
async def admin_add_stock_process(message: Message, state: FSMContext):
    """Process stock addition."""
    items = message.text.strip().split('\n')
    items = [item.strip() for item in items if item.strip()]
    
    if not items:
        await message.answer("❌ Please enter at least one item")
        return
    
    data = await state.get_data()
    product_id = data['product_id']
    
    # Add stock
    count = await db.add_stock(product_id, items)
    
    # Notify waiting list users
    waiting_list = await db.get_waiting_list(product_id)
    product = await db.get_product(product_id)
    
    for entry in waiting_list:
        try:
            await message.bot.send_message(
                entry['user_id'],
                f"🔔 <b>Product Restocked!</b>\n\n"
                f"📦 {product['name_en']} is now available!",
                parse_mode='HTML'
            )
            await db.mark_notified(entry['id'])
        except Exception:
            pass
    
    await state.clear()
    await message.answer(
        f"✅ Added {count} items to stock!\n"
        f"Notified {len(waiting_list)} waiting users.",
        reply_markup=back_button('en', f"admin_prod:{product_id}"),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("admin_toggle_prod:"))
async def admin_toggle_product(callback: CallbackQuery):
    """Toggle product visibility."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return
    
    new_visibility = 0 if product['is_visible'] else 1
    await db.update_product(product_id, is_visible=new_visibility)
    
    await callback.answer(f"Visibility: {'ON' if new_visibility else 'OFF'}")
    
    # Refresh view
    product = await db.get_product(product_id)
    try:
        await callback.message.edit_text(
            f"📦 <b>{product['name_en']}</b>\n\n"
            f"Price: {product['points_price']} points\n"
            f"Stock: {product['stock']}\n"
            f"Type: {product['type']}\n"
            f"Visible: {'Yes' if product['is_visible'] else 'No'}",
            reply_markup=admin_product_manage_keyboard(product_id)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_del_prod:"))
async def admin_delete_product(callback: CallbackQuery):
    """Delete product."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    await db.delete_product(product_id)
    
    await callback.answer("Product deleted")
    
    # Go back to products list
    products = await db.get_products(visible_only=False)
    await callback.message.edit_text(
        messages.admin_products_list(),
        reply_markup=admin_products_list_keyboard(products)
    )


# ==================== CATEGORIES ====================

@router.callback_query(F.data == "admin:categories")
async def admin_categories(callback: CallbackQuery):
    """Show categories list."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    categories = await db.get_categories(active_only=False)
    await callback.message.edit_text(
        messages.admin_categories_list(),
        reply_markup=admin_categories_list_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_category")
async def admin_add_category_start(callback: CallbackQuery, state: FSMContext):
    """Start add category."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminState.ADD_CATEGORY_NAME_EN)
    await callback.message.edit_text(
        "📂 <b>Add Category</b>\n\nEnter category name (English):",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_CATEGORY_NAME_EN)
async def admin_add_category_name_en(message: Message, state: FSMContext):
    """Save name EN and ask for AR."""
    await state.update_data(name_en=message.text.strip())
    await state.set_state(AdminState.ADD_CATEGORY_NAME_AR)
    await message.answer(
        "📂 <b>Add Category</b>\n\nEnter category name (Arabic):",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_CATEGORY_NAME_AR)
async def admin_add_category_name_ar(message: Message, state: FSMContext):
    """Create category."""
    data = await state.get_data()
    name_en = data['name_en']
    name_ar = message.text.strip()
    
    category_id = await db.create_category(name_ar, name_en)
    
    await state.clear()
    await message.answer(
        f"✅ Category created!\nID: <code>{category_id}</code>",
        reply_markup=back_button('en', "admin:categories"),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("admin_cat:"))
async def admin_category_detail(callback: CallbackQuery):
    """Show category management."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    category_id = int(callback.data.split(":")[1])
    category = await db.get_category(category_id)
    
    if not category:
        await callback.answer("Category not found", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📂 <b>{category['name_en']}</b>\n\n"
        f"Active: {'Yes' if category['is_active'] else 'No'}",
        reply_markup=admin_category_manage_keyboard(category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_cat:"))
async def admin_toggle_category(callback: CallbackQuery):
    """Toggle category active status."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    category_id = int(callback.data.split(":")[1])
    await db.update_category(category_id)
    
    # Toggle manually since update_category needs fix
    category = await db.get_category(category_id)
    new_active = 0 if category['is_active'] else 1
    await db.execute(
        "UPDATE categories SET is_active = ? WHERE id = ?",
        (new_active, category_id)
    )
    
    await callback.answer(f"Active: {'ON' if new_active else 'OFF'}")
    
    # Refresh
    categories = await db.get_categories(active_only=False)
    await callback.message.edit_text(
        messages.admin_categories_list(),
        reply_markup=admin_categories_list_keyboard(categories)
    )


@router.callback_query(F.data.startswith("admin_del_cat:"))
async def admin_delete_category(callback: CallbackQuery):
    """Delete category."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    category_id = int(callback.data.split(":")[1])
    await db.delete_category(category_id)
    
    await callback.answer("Category deleted")
    
    categories = await db.get_categories(active_only=False)
    await callback.message.edit_text(
        messages.admin_categories_list(),
        reply_markup=admin_categories_list_keyboard(categories)
    )


# ==================== CHANNELS ====================

@router.callback_query(F.data == "admin:channels")
async def admin_channels(callback: CallbackQuery):
    """Show channels list."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    channels = await db.get_channels(active_only=False)
    await callback.message.edit_text(
        messages.admin_channels_list(),
        reply_markup=admin_channels_list_keyboard(channels)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_channel")
async def admin_add_channel_start(callback: CallbackQuery, state: FSMContext):
    """Start add channel."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminState.ADD_CHANNEL_ID)
    await callback.message.edit_text(
        "📢 <b>Add Channel</b>\n\nEnter channel ID or @username:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_CHANNEL_ID)
async def admin_add_channel_id(message: Message, state: FSMContext):
    """Save channel ID and ask for name."""
    await state.update_data(channel_id=message.text.strip())
    await state.set_state(AdminState.ADD_CHANNEL_NAME)
    await message.answer(
        "📢 <b>Add Channel</b>\n\nEnter display name:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_CHANNEL_NAME)
async def admin_add_channel_name(message: Message, state: FSMContext):
    """Save name and ask for URL."""
    await state.update_data(channel_name=message.text.strip())
    await state.set_state(AdminState.ADD_CHANNEL_URL)
    await message.answer(
        "📢 <b>Add Channel</b>\n\nEnter invite URL:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_CHANNEL_URL)
async def admin_add_channel_url(message: Message, state: FSMContext):
    """Create channel."""
    data = await state.get_data()
    
    await db.add_channel(
        channel_id=data['channel_id'],
        channel_name=data['channel_name'],
        channel_url=message.text.strip()
    )
    
    await state.clear()
    await message.answer(
        "✅ Channel added!",
        reply_markup=back_button('en', "admin:channels")
    )


# ==================== COUPONS ====================

@router.callback_query(F.data == "admin:coupons")
async def admin_coupons(callback: CallbackQuery):
    """Show coupons list."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    coupons = await db.get_coupons(limit=20)
    await callback.message.edit_text(
        messages.admin_coupons_list(),
        reply_markup=admin_coupons_list_keyboard(coupons)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_coupon")
async def admin_add_coupon_start(callback: CallbackQuery, state: FSMContext):
    """Start add coupon."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminState.ADD_COUPON_CODE)
    await callback.message.edit_text(
        "🎟️ <b>Add Coupon</b>\n\nEnter code or send AUTO for random:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_COUPON_CODE)
async def admin_add_coupon_code(message: Message, state: FSMContext):
    """Save code and ask for points."""
    code = message.text.strip().upper()
    if code == 'AUTO':
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    await state.update_data(code=code)
    await state.set_state(AdminState.ADD_COUPON_POINTS)
    await message.answer(
        f"🎟️ <b>Add Coupon</b>\n\nCode: <code>{code}</code>\n\nEnter points value:",
        reply_markup=cancel_keyboard('en'),
        parse_mode='HTML'
    )


@router.message(AdminState.ADD_COUPON_POINTS)
async def admin_add_coupon_points(message: Message, state: FSMContext):
    """Save points and ask for max uses."""
    try:
        points = int(message.text.strip())
        if points <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid number")
        return
    
    await state.update_data(points=points)
    await state.set_state(AdminState.ADD_COUPON_MAX_USES)
    await message.answer(
        "🎟️ <b>Add Coupon</b>\n\nEnter max uses (0 for unlimited):",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_COUPON_MAX_USES)
async def admin_add_coupon_max_uses(message: Message, state: FSMContext):
    """Save max uses and ask for expiry."""
    try:
        max_uses = int(message.text.strip())
        if max_uses < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid number")
        return
    
    await state.update_data(max_uses=max_uses)
    await state.set_state(AdminState.ADD_COUPON_EXPIRY)
    await message.answer(
        "🎟️ <b>Add Coupon</b>\n\nEnter expiry date (YYYY-MM-DD) or NONE:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_COUPON_EXPIRY)
async def admin_add_coupon_expiry(message: Message, state: FSMContext):
    """Create coupon."""
    expiry_str = message.text.strip()
    expiry = None
    
    if expiry_str.upper() != 'NONE':
        try:
            expiry = datetime.strptime(expiry_str, '%Y-%m-%d')
        except ValueError:
            await message.answer("❌ Invalid date format. Use YYYY-MM-DD")
            return
    
    data = await state.get_data()
    
    await db.create_coupon(
        code=data['code'],
        points_value=data['points'],
        max_uses=data['max_uses'],
        expires_at=expiry.isoformat() if expiry else None,
        created_by=message.from_user.id
    )
    
    await state.clear()
    await message.answer(
        f"✅ Coupon created!\nCode: <code>{data['code']}</code>",
        reply_markup=back_button('en', "admin:coupons"),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("admin_coupon:"))
async def admin_coupon_detail(callback: CallbackQuery):
    """Show coupon management."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    coupon_id = int(callback.data.split(":")[1])
    coupon = await db.fetchone("SELECT * FROM coupons WHERE id = ?", (coupon_id,))
    
    if not coupon:
        await callback.answer("Coupon not found", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🎟️ <b>{coupon['code']}</b>\n\n"
        f"Points: {coupon['points_value']}\n"
        f"Used: {coupon['used_count']}/{coupon['max_uses'] if coupon['max_uses'] > 0 else '∞'}\n"
        f"Active: {'Yes' if coupon['is_active'] else 'No'}",
        reply_markup=admin_coupon_manage_keyboard(coupon_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_coupon:"))
async def admin_toggle_coupon(callback: CallbackQuery):
    """Toggle coupon active."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    coupon_id = int(callback.data.split(":")[1])
    await db.toggle_coupon(coupon_id)
    
    await callback.answer("Toggled")
    
    coupons = await db.get_coupons(limit=20)
    await callback.message.edit_text(
        messages.admin_coupons_list(),
        reply_markup=admin_coupons_list_keyboard(coupons)
    )


@router.callback_query(F.data.startswith("admin_del_coupon:"))
async def admin_delete_coupon(callback: CallbackQuery):
    """Delete coupon."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    coupon_id = int(callback.data.split(":")[1])
    await db.delete_coupon(coupon_id)
    
    await callback.answer("Deleted")
    
    coupons = await db.get_coupons(limit=20)
    await callback.message.edit_text(
        messages.admin_coupons_list(),
        reply_markup=admin_coupons_list_keyboard(coupons)
    )


# ==================== USERS ====================

@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, state: FSMContext):
    """Show user search."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminState.SEARCH_USER)
    await callback.message.edit_text(
        messages.admin_users_search(),
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.SEARCH_USER)
async def admin_search_user(message: Message, state: FSMContext):
    """Search and show user."""
    search = message.text.strip()
    users = await db.search_users(search)
    
    if not users:
        await message.answer(
            "❌ User not found",
            reply_markup=back_button('en', "admin:users")
        )
        await state.clear()
        return
    
    user = users[0]
    await state.update_data(user_id=user['telegram_id'])
    
    await message.answer(
        messages.admin_user_profile(user),
        reply_markup=admin_user_profile_keyboard(user['telegram_id']),
        parse_mode='HTML'
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_user_add:"))
async def admin_user_add_points_start(callback: CallbackQuery, state: FSMContext):
    """Start adding points to user."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminState.USER_ADD_POINTS)
    
    await callback.message.edit_text(
        "➕ <b>Add Points</b>\n\nEnter amount:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.USER_ADD_POINTS)
async def admin_user_add_points(message: Message, state: FSMContext):
    """Add points to user."""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid number")
        return
    
    data = await state.get_data()
    user_id = data['target_user_id']
    
    new_balance = await db.add_points(user_id, amount)
    
    # Notify user
    try:
        await message.bot.send_message(
            user_id,
            f"🎁 <b>Points Added!</b>\n\n"
            f"+{amount} points added to your balance.\n"
            f"New balance: {new_balance} points",
            parse_mode='HTML'
        )
    except Exception:
        pass
    
    await state.clear()
    await message.answer(
        f"✅ Added {amount} points!\nNew balance: {new_balance}",
        reply_markup=back_button('en', "admin:users")
    )


@router.callback_query(F.data.startswith("admin_user_rem:"))
async def admin_user_remove_points_start(callback: CallbackQuery, state: FSMContext):
    """Start removing points from user."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminState.USER_REMOVE_POINTS)
    
    await callback.message.edit_text(
        "➖ <b>Remove Points</b>\n\nEnter amount:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.USER_REMOVE_POINTS)
async def admin_user_remove_points(message: Message, state: FSMContext):
    """Remove points from user."""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid number")
        return
    
    data = await state.get_data()
    user_id = data['target_user_id']
    
    new_balance = await db.remove_points(user_id, amount)
    
    await state.clear()
    await message.answer(
        f"✅ Removed {amount} points!\nNew balance: {new_balance}",
        reply_markup=back_button('en', "admin:users")
    )


@router.callback_query(F.data.startswith("admin_user_ban:"))
async def admin_user_ban(callback: CallbackQuery):
    """Ban/unban user."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("User not found", show_alert=True)
        return
    
    new_ban = not user.get('is_banned', False)
    await db.ban_user(user_id, new_ban)
    
    await callback.answer(f"Banned: {'YES' if new_ban else 'NO'}")
    
    # Refresh
    user = await db.get_user(user_id)
    try:
        await callback.message.edit_text(
            messages.admin_user_profile(user),
            reply_markup=admin_user_profile_keyboard(user_id),
            parse_mode='HTML'
        )
    except Exception:
        pass


# ==================== ADMINS ====================

@router.callback_query(F.data == "admin:admins")
async def admin_admins(callback: CallbackQuery):
    """Show admins list."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    # Only super admin can manage admins
    if callback.from_user.id != config.SUPER_ADMIN_ID:
        await callback.answer("Only super admin can manage admins", show_alert=True)
        return
    
    admins = await db.get_admins()
    await callback.message.edit_text(
        "👮 <b>Admins Management</b>",
        reply_markup=admin_admins_list_keyboard(admins, config.SUPER_ADMIN_ID)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_admin")
async def admin_add_admin_start(callback: CallbackQuery, state: FSMContext):
    """Start add admin."""
    if callback.from_user.id != config.SUPER_ADMIN_ID:
        await callback.answer("Only super admin can add admins", show_alert=True)
        return
    
    await state.set_state(AdminState.ADD_ADMIN)
    await callback.message.edit_text(
        "👮 <b>Add Admin</b>\n\nEnter Telegram ID:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_ADMIN)
async def admin_add_admin(message: Message, state: FSMContext):
    """Add admin."""
    try:
        admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Please enter a valid Telegram ID")
        return
    
    await db.add_admin(admin_id, message.from_user.id)
    
    await state.clear()
    await message.answer(
        f"✅ Added admin: <code>{admin_id}</code>",
        reply_markup=back_button('en', "admin:admins"),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("admin_remove_admin:"))
async def admin_remove_admin(callback: CallbackQuery):
    """Remove admin."""
    if callback.from_user.id != config.SUPER_ADMIN_ID:
        await callback.answer("Only super admin can remove admins", show_alert=True)
        return
    
    admin_id = int(callback.data.split(":")[1])
    await db.remove_admin(admin_id)
    
    await callback.answer("Admin removed")
    
    admins = await db.get_admins()
    await callback.message.edit_text(
        "👮 <b>Admins Management</b>",
        reply_markup=admin_admins_list_keyboard(admins, config.SUPER_ADMIN_ID)
    )


# ==================== STATS ====================

@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    """Show stats."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    stats = await db.get_stats()
    
    await callback.message.edit_text(
        messages.admin_stats(stats),
        reply_markup=back_button('en', "admin:panel"),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== BROADCAST ====================

@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Start broadcast."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminState.BROADCAST_MESSAGE)
    await callback.message.edit_text(
        "📣 <b>Broadcast</b>\n\nSend your message (text, photo, video, or document):",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.BROADCAST_MESSAGE)
async def admin_broadcast_message(message: Message, state: FSMContext):
    """Save broadcast message."""
    # Store message info
    broadcast_data = {
        'text': message.text or message.caption,
        'photo': message.photo[-1].file_id if message.photo else None,
        'video': message.video.file_id if message.video else None,
        'document': message.document.file_id if message.document else None
    }
    
    await state.update_data(broadcast=broadcast_data)
    await state.set_state(AdminState.BROADCAST_CONFIRM)
    
    # Get user count
    users = await db.get_all_users()
    count = len(users)
    
    await message.answer(
        messages.admin_broadcast_confirm(count),
        reply_markup=admin_broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "admin_broadcast:confirm")
async def admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    data = await state.get_data()
    broadcast = data.get('broadcast', {})
    
    # Get all users
    users = await db.get_all_users()
    users = [u for u in users if not u.get('is_banned') and u.get('setup_complete')]
    
    total = len(users)
    success = 0
    failed = 0
    
    # Create broadcast record
    broadcast_id = await db.create_broadcast(
        message=broadcast.get('text', ''),
        photo_id=broadcast.get('photo'),
        sent_by=callback.from_user.id
    )
    
    # Send messages
    status_msg = await callback.message.edit_text(
        messages.admin_broadcast_progress(0, total)
    )
    
    for i, user in enumerate(users):
        try:
            user_id = user['telegram_id']
            
            if broadcast.get('photo'):
                await callback.bot.send_photo(
                    user_id,
                    photo=broadcast['photo'],
                    caption=broadcast.get('text')
                )
            elif broadcast.get('video'):
                await callback.bot.send_video(
                    user_id,
                    video=broadcast['video'],
                    caption=broadcast.get('text')
                )
            elif broadcast.get('document'):
                await callback.bot.send_document(
                    user_id,
                    document=broadcast['document'],
                    caption=broadcast.get('text')
                )
            else:
                await callback.bot.send_message(user_id, broadcast.get('text', ''))
            
            success += 1
            
        except Exception:
            failed += 1
        
        # Update progress every 50 users
        if (i + 1) % 50 == 0:
            try:
                await status_msg.edit_text(
                    messages.admin_broadcast_progress(i + 1, total)
                )
            except Exception:
                pass
    
    # Update stats
    await db.update_broadcast_stats(broadcast_id, total, success, failed)
    
    await state.clear()
    
    try:
        await status_msg.edit_text(
            messages.admin_broadcast_complete(success, failed),
            reply_markup=back_button('en', "admin:panel")
        )
    except Exception:
        pass


# ==================== SUPPORT TICKETS ====================

@router.callback_query(F.data == "admin:support")
async def admin_support(callback: CallbackQuery):
    """Show support tickets."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    tickets = await db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "✅ No open tickets",
            reply_markup=back_button('en', "admin:panel")
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🎫 <b>Support Tickets</b>",
        reply_markup=admin_support_tickets_keyboard(tickets)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ticket:"))
async def admin_ticket_detail(callback: CallbackQuery):
    """Show ticket detail."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    ticket_id = int(callback.data.split(":")[1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("Ticket not found", show_alert=True)
        return
    
    await callback.message.edit_text(
        messages.admin_support_ticket(ticket),
        reply_markup=admin_ticket_manage_keyboard(ticket_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_reply_ticket:"))
async def admin_reply_ticket_start(callback: CallbackQuery, state: FSMContext):
    """Start replying to ticket."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    ticket_id = int(callback.data.split(":")[1])
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(AdminState.REPLY_TICKET)
    
    await callback.message.edit_text(
        "💬 <b>Reply to Ticket</b>\n\nEnter your reply:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.REPLY_TICKET)
async def admin_reply_ticket(message: Message, state: FSMContext):
    """Send reply to ticket."""
    data = await state.get_data()
    ticket_id = data['ticket_id']
    
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await message.answer("Ticket not found")
        await state.clear()
        return
    
    reply_text = message.text.strip()
    
    # Save reply
    await db.reply_ticket(ticket_id, reply_text)
    
    # Notify user
    try:
        user = await db.get_user(ticket['user_id'])
        lang = user.get('language', 'ar') if user else 'ar'
        
        await message.bot.send_message(
            ticket['user_id'],
            messages.support_reply_received(lang, reply_text),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Failed to notify user: {e}")
    
    await state.clear()
    await message.answer(
        "✅ Reply sent!",
        reply_markup=back_button('en', "admin:support")
    )


@router.callback_query(F.data.startswith("admin_close_ticket:"))
async def admin_close_ticket(callback: CallbackQuery):
    """Close ticket."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    ticket_id = int(callback.data.split(":")[1])
    await db.close_ticket(ticket_id)
    
    await callback.answer("Ticket closed")
    
    tickets = await db.get_open_tickets()
    if not tickets:
        await callback.message.edit_text(
            "✅ No open tickets",
            reply_markup=back_button('en', "admin:panel")
        )
        return
    
    await callback.message.edit_text(
        "🎫 <b>Support Tickets</b>",
        reply_markup=admin_support_tickets_keyboard(tickets)
    )


# ==================== STARS PACKAGES ====================

@router.callback_query(F.data == "admin:stars")
async def admin_stars(callback: CallbackQuery):
    """Show stars packages."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    packages = await db.get_stars_packages(active_only=False)
    await callback.message.edit_text(
        "⭐ <b>Stars Packages</b>",
        reply_markup=admin_stars_packages_keyboard(packages)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_stars_pkg")
async def admin_add_stars_pkg_start(callback: CallbackQuery, state: FSMContext):
    """Start add stars package."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminState.ADD_STARS_PKG_STARS)
    await callback.message.edit_text(
        "⭐ <b>Add Stars Package</b>\n\nEnter stars amount:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_STARS_PKG_STARS)
async def admin_add_stars_pkg_stars(message: Message, state: FSMContext):
    """Save stars amount and ask for points."""
    try:
        stars = int(message.text.strip())
        if stars <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid number")
        return
    
    await state.update_data(stars=stars)
    await state.set_state(AdminState.ADD_STARS_PKG_POINTS)
    await message.answer(
        "⭐ <b>Add Stars Package</b>\n\nEnter points amount:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_STARS_PKG_POINTS)
async def admin_add_stars_pkg_points(message: Message, state: FSMContext):
    """Create stars package."""
    try:
        points = int(message.text.strip())
        if points <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid number")
        return
    
    data = await state.get_data()
    
    await db.create_stars_package(data['stars'], points)
    
    await state.clear()
    await message.answer(
        f"✅ Package created!\n⭐ {data['stars']} Stars → {points} Points",
        reply_markup=back_button('en', "admin:stars")
    )


@router.callback_query(F.data.startswith("admin_stars_pkg:"))
async def admin_stars_pkg_detail(callback: CallbackQuery):
    """Show stars package management."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    pkg_id = int(callback.data.split(":")[1])
    pkg = await db.get_stars_package(pkg_id)
    
    if not pkg:
        await callback.answer("Package not found", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⭐ <b>Package</b>\n\n"
        f"Stars: {pkg['stars_amount']}\n"
        f"Points: {pkg['points_amount']}\n"
        f"Active: {'Yes' if pkg['is_active'] else 'No'}",
        reply_markup=admin_stars_package_manage_keyboard(pkg_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_stars:"))
async def admin_toggle_stars_pkg(callback: CallbackQuery):
    """Toggle stars package."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    pkg_id = int(callback.data.split(":")[1])
    await db.toggle_stars_package(pkg_id)
    
    await callback.answer("Toggled")
    
    packages = await db.get_stars_packages(active_only=False)
    await callback.message.edit_text(
        "⭐ <b>Stars Packages</b>",
        reply_markup=admin_stars_packages_keyboard(packages)
    )


@router.callback_query(F.data.startswith("admin_del_stars:"))
async def admin_delete_stars_pkg(callback: CallbackQuery):
    """Delete stars package."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    pkg_id = int(callback.data.split(":")[1])
    await db.delete_stars_package(pkg_id)
    
    await callback.answer("Deleted")
    
    packages = await db.get_stars_packages(active_only=False)
    await callback.message.edit_text(
        "⭐ <b>Stars Packages</b>",
        reply_markup=admin_stars_packages_keyboard(packages)
    )


# ==================== SETTINGS ====================

@router.callback_query(F.data == "admin:settings")
async def admin_settings(callback: CallbackQuery):
    """Show settings."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    settings = {
        'referral_points': await db.get_setting('referral_points', '1'),
        'daily_bonus_points': await db.get_setting('daily_bonus_points', '10'),
        'penalty_mode': await db.get_setting('penalty_mode', 'false'),
        'stars_per_point': await db.get_setting('stars_per_point', '4'),
        'stars_withdrawal_open': await db.get_setting('stars_withdrawal_open', 'true'),
        'low_stock_threshold': await db.get_setting('low_stock_threshold', '5')
    }

    await callback.message.edit_text(
        messages.admin_settings(settings),
        reply_markup=admin_settings_v2_keyboard(settings)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_setting:"))
async def admin_setting_edit(callback: CallbackQuery, state: FSMContext):
    """Edit setting."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    setting_key = callback.data.split(":")[1]
    
    # Map to actual setting key
    key_map = {
        'welcome_ar': 'welcome_message_ar',
        'welcome_en': 'welcome_message_en'
    }
    actual_key = key_map.get(setting_key, setting_key)
    
    current = await db.get_setting(actual_key, '')
    
    await state.update_data(setting_key=actual_key)
    await state.set_state(AdminState.SETTING_VALUE)
    
    await callback.message.edit_text(
        f"⚙️ <b>Edit Setting</b>\n\n"
        f"Key: <code>{actual_key}</code>\n"
        f"Current: {current[:100] if current else 'Not set'}\n\n"
        f"Enter new value:",
        reply_markup=cancel_keyboard('en'),
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AdminState.SETTING_VALUE)
async def admin_setting_save(message: Message, state: FSMContext):
    """Save setting."""
    data = await state.get_data()
    setting_key = data['setting_key']
    value = message.text.strip()
    
    await db.set_setting(setting_key, value)
    
    await state.clear()
    await message.answer(
        f"✅ Setting saved!\n<code>{setting_key}</code> = {value[:50]}",
        reply_markup=back_button('en', "admin:settings"),
        parse_mode='HTML'
    )


@router.callback_query(F.data == "admin_toggle_penalty")
async def admin_toggle_penalty(callback: CallbackQuery):
    """Toggle penalty mode."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    current = await db.get_setting('penalty_mode', 'false')
    new_value = 'false' if current.lower() == 'true' else 'true'

    await db.set_setting('penalty_mode', new_value)

    await callback.answer(f"Penalty Mode: {new_value.upper()}")

    settings = {
        'referral_points': await db.get_setting('referral_points', '1'),
        'daily_bonus_points': await db.get_setting('daily_bonus_points', '10'),
        'penalty_mode': new_value,
        'stars_per_point': await db.get_setting('stars_per_point', '4'),
        'stars_withdrawal_open': await db.get_setting('stars_withdrawal_open', 'true'),
        'low_stock_threshold': await db.get_setting('low_stock_threshold', '5')
    }

    await callback.message.edit_text(
        messages.admin_settings(settings),
        reply_markup=admin_settings_v2_keyboard(settings)
    )


# ==================== V2 NEW ADMIN HANDLERS ====================

# --- Stars Withdrawal Toggle ---
@router.callback_query(F.data == "admin_toggle_stars_withdrawal")
async def admin_toggle_stars_withdrawal(callback: CallbackQuery):
    """Toggle stars withdrawal."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    current = await db.get_setting('stars_withdrawal_open', 'true')
    new_value = 'false' if current.lower() == 'true' else 'true'

    if new_value == 'false':
        # Warn if pending orders exist
        pending = await db.get_pending_star_orders_count()
        if pending > 0:
            await callback.answer(
                f"⚠️ There are {pending} pending star orders. They will be auto-cancelled in 24h.",
                show_alert=True
            )

    await db.set_setting('stars_withdrawal_open', new_value)
    await callback.answer(f"Stars Withdrawal: {new_value.upper()}")

    settings = {
        'referral_points': await db.get_setting('referral_points', '1'),
        'daily_bonus_points': await db.get_setting('daily_bonus_points', '10'),
        'penalty_mode': await db.get_setting('penalty_mode', 'false'),
        'stars_per_point': await db.get_setting('stars_per_point', '4'),
        'stars_withdrawal_open': new_value,
        'low_stock_threshold': await db.get_setting('low_stock_threshold', '5')
    }

    await callback.message.edit_text(
        messages.admin_settings(settings),
        reply_markup=admin_settings_v2_keyboard(settings)
    )


# --- Admin User Profile V2 ---
@router.callback_query(F.data.startswith("admin_user_profile:"))
async def admin_user_detail_v2(callback: CallbackQuery):
    """Show user profile V2."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)

    if not user:
        await callback.answer("User not found", show_alert=True)
        return

    await callback.message.edit_text(
        messages.admin_user_profile_v2(user),
        reply_markup=admin_user_profile_v2_keyboard(user_id, bool(user.get('is_restricted'))),
        parse_mode='HTML'
    )
    await callback.answer()


# --- User Restrict/Unrestrict ---
@router.callback_query(F.data.startswith("admin_user_restrict:"))
async def admin_user_restrict(callback: CallbackQuery):
    """Toggle user restriction."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)

    if not user:
        await callback.answer("User not found", show_alert=True)
        return

    new_restricted = not user.get('is_restricted', False)
    await db.set_user_restricted(user_id, new_restricted)

    await callback.answer(f"Restricted: {'YES' if new_restricted else 'NO'}")

    user = await db.get_user(user_id)
    try:
        await callback.message.edit_text(
            messages.admin_user_profile_v2(user),
            reply_markup=admin_user_profile_v2_keyboard(user_id, bool(user.get('is_restricted'))),
            parse_mode='HTML'
        )
    except Exception:
        pass


# --- Admin User Notes ---
@router.callback_query(F.data.startswith("admin_user_note:"))
async def admin_user_note_start(callback: CallbackQuery, state: FSMContext):
    """Start adding/editing admin note."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])
    await state.update_data(target_user_id=user_id)

    user = await db.get_user(user_id)
    current_note = user.get('admin_notes', 'None') if user else 'None'

    await state.set_state(AdminState.SETTING_VALUE)
    await callback.message.edit_text(
        f"📝 <b>Admin Note</b>\n\n"
        f"Current note: {current_note}\n\n"
        f"Enter new note (or send NONE to clear):",
        reply_markup=cancel_keyboard('en'),
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AdminState.SETTING_VALUE)
async def admin_user_note_save(message: Message, state: FSMContext):
    """Save admin note."""
    data = await state.get_data()
    user_id = data.get('target_user_id')

    if not user_id:
        await message.answer("❌ Invalid operation")
        await state.clear()
        return

    value = message.text.strip()
    if value.upper() == 'NONE':
        value = ''

    await db.set_admin_notes(user_id, value)

    await state.clear()

    user = await db.get_user(user_id)
    await message.answer(
        f"✅ Admin note saved!",
        reply_markup=back_button('en', f"admin_user_profile:{user_id}")
    )


# --- Channel Management V2 ---
@router.callback_query(F.data.startswith("admin_channel:"))
async def admin_channel_detail(callback: CallbackQuery):
    """Show channel detail."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    channel_id = callback.data.split(":", 1)[1]
    channel = await db.fetchone(
        "SELECT * FROM channels WHERE channel_id = ?",
        (channel_id,)
    )

    if not channel:
        await callback.answer("Channel not found", show_alert=True)
        return

    await callback.message.edit_text(
        messages.admin_channel_status(channel),
        reply_markup=admin_channel_manage_keyboard(channel_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_channel:"))
async def admin_edit_channel(callback: CallbackQuery, state: FSMContext):
    """Start editing channel field."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    parts = callback.data.split(":", 2)
    channel_id = parts[1]
    field = parts[2]

    field_names = {'name': 'channel_name', 'url': 'channel_url', 'channel_id': 'channel_id'}
    field_name = field_names.get(field, field)

    await state.update_data(channel_id=channel_id, field=field_name)
    await state.set_state(AdminState.SETTING_VALUE)

    await callback.message.edit_text(
        f"✏️ Enter new {field_name.replace('_', ' ')}:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.SETTING_VALUE)
async def admin_save_channel_edit(message: Message, state: FSMContext):
    """Save channel edit."""
    data = await state.get_data()
    channel_id = data.get('channel_id')
    field = data.get('field')

    if not channel_id or not field:
        await message.answer("❌ Invalid operation")
        await state.clear()
        return

    value = message.text.strip()

    await db.update_channel(channel_id, **{field: value})

    await state.clear()

    channel = await db.fetchone(
        "SELECT * FROM channels WHERE channel_id = ?",
        (channel_id,)
    )

    if channel:
        await message.answer(
            f"✅ Channel updated!",
            reply_markup=back_button('en', f"admin_channel:{channel_id}")
        )
    else:
        await message.answer("❌ Error updating channel")


@router.callback_query(F.data.startswith("admin_toggle_channel:"))
async def admin_toggle_channel(callback: CallbackQuery):
    """Toggle channel active."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    channel_id = callback.data.split(":", 1)[1]
    await db.execute(
        "UPDATE channels SET is_active = 1 - is_active WHERE channel_id = ?",
        (channel_id,)
    )

    await callback.answer("Toggled")

    channels = await db.fetchall("SELECT * FROM channels")
    await callback.message.edit_text(
        messages.admin_channels_list(),
        reply_markup=admin_channels_list_keyboard(channels)
    )


@router.callback_query(F.data.startswith("admin_del_channel:"))
async def admin_delete_channel(callback: CallbackQuery):
    """Delete channel."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    channel_id = callback.data.split(":", 1)[1]
    await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))

    await callback.answer("Channel deleted")

    channels = await db.fetchall("SELECT * FROM channels")
    await callback.message.edit_text(
        messages.admin_channels_list(),
        reply_markup=admin_channels_list_keyboard(channels)
    )


# --- Admin Star Orders Dashboard ---
@router.callback_query(F.data == "admin:star_orders")
async def admin_star_orders(callback: CallbackQuery):
    """Show admin star orders dashboard."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    await _show_admin_star_orders(callback, 'pending')


async def _show_admin_star_orders(callback: CallbackQuery, status: str):
    """Show admin star orders filtered by status."""
    from database import db as db_module
    from datetime import datetime, timedelta

    if status == 'pending':
        orders = await db_module.get_pending_star_orders()
    else:
        orders = await db_module.fetchall(
            "SELECT * FROM star_orders WHERE status = ? ORDER BY created_at DESC LIMIT 30",
            (status,)
        )

    # Enrich orders with usernames and time left
    for order in orders:
        user = await db_module.get_user(order['user_id'])
        order['username'] = user.get('username') if user else f"User {order['user_id']}"

        if order.get('created_at') and order['status'] == 'pending':
            created = datetime.fromisoformat(str(order['created_at']).replace('+00:00', '').replace('Z', ''))
            expires = created + timedelta(hours=24)
            remaining = expires - datetime.utcnow()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                order['time_left'] = f"{hours}h left"
            else:
                order['time_left'] = "Expired"

    await callback.message.edit_text(
        f"⭐ <b>Star Orders</b> ({len(orders)} {status})",
        reply_markup=admin_star_orders_keyboard(orders, status),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("admin_star_orders:"))
async def admin_star_orders_filter(callback: CallbackQuery):
    """Change star orders filter."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    status = callback.data.split(":", 1)[1]
    await _show_admin_star_orders(callback, status)


@router.callback_query(F.data.startswith("admin_star_order:"))
async def admin_star_order_detail(callback: CallbackQuery):
    """Show admin star order detail."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    order = await db.get_star_order(order_id)

    if not order:
        await callback.answer("Order not found", show_alert=True)
        return

    user = await db.get_user(order['user_id'])
    username = user.get('username') if user else f"User {order['user_id']}"

    await callback.message.edit_text(
        messages.admin_star_order_notification({
            'order_id': order_id,
            'username': username,
            'user_id': order['user_id'],
            'stars_amount': order['stars_amount'],
            'points_cost': order['points_cost']
        }),
        reply_markup=admin_star_order_manage_keyboard(order_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_star_deliver:"))
async def admin_star_deliver(callback: CallbackQuery, bot: Bot):
    """Mark star order as delivered."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    order = await db.get_star_order(order_id)

    if not order or order['status'] != 'pending':
        await callback.answer("Order not found or not pending", show_alert=True)
        return

    await db.update_star_order_status(
        order_id, 'delivered',
        delivered_at=datetime.utcnow().isoformat(),
        admin_id=callback.from_user.id
    )

    user = await db.get_user(order['user_id'])
    lang = user.get('language', 'ar') if user else 'ar'

    try:
        await bot.send_message(
            order['user_id'],
            f"⭐ <b>Your order #{order_id} for {order['stars_amount']} stars has been marked as delivered!</b>\n\n"
            f"Please confirm you received them.",
            reply_markup=_get_user_order_confirm_keyboard(lang, order_id),
            parse_mode='HTML'
        )
    except Exception:
        pass

    await callback.answer("Marked as delivered")
    await _show_admin_star_orders(callback, 'pending')


@router.callback_query(F.data.startswith("admin_star_cancel:"))
async def admin_star_cancel(callback: CallbackQuery, bot: Bot):
    """Cancel star order."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    order = await db.get_star_order(order_id)

    if not order or order['status'] != 'pending':
        await callback.answer("Order not found or not pending", show_alert=True)
        return

    # Refund points
    await db.add_points(order['user_id'], order['points_cost'])

    await db.update_star_order_status(
        order_id, 'cancelled',
        cancelled_at=datetime.utcnow().isoformat(),
        admin_id=callback.from_user.id
    )

    try:
        await bot.send_message(
            order['user_id'],
            f"❌ <b>Your star order #{order_id} has been cancelled.</b>\n\n"
            f"💰 {order['points_cost']} points have been refunded.",
            parse_mode='HTML'
        )
    except Exception:
        pass

    await callback.answer("Order cancelled, points refunded")
    await _show_admin_star_orders(callback, 'pending')


def _get_user_order_confirm_keyboard(lang: str, order_id: str):
    """Get keyboard for user to confirm/reject delivery."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
        ]
    ])


# --- Admin Ads Management ---
@router.callback_query(F.data == "admin:ads")
async def admin_ads(callback: CallbackQuery):
    """Show admin ads management."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    ads = await db.get_ad_tasks(active_only=False)
    await callback.message.edit_text(
        "📺 <b>Ads Management</b>",
        reply_markup=admin_ads_keyboard(ads),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ad:"))
async def admin_ad_detail(callback: CallbackQuery):
    """Show admin ad detail."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    ad_id = int(callback.data.split(":")[1])
    ad = await db.get_ad_task(ad_id)

    if not ad:
        await callback.answer("Ad not found", show_alert=True)
        return

    await callback.message.edit_text(
        messages.admin_ad_detail(ad),
        reply_markup=admin_ad_manage_keyboard(ad_id, not ad.get('is_once_per_user', True)),
        parse_mode='HTML'
    )
    await callback.answer()


# --- Admin Ad Claim Management ---
@router.callback_query(F.data == "admin:ad_claims_pending")
async def admin_ad_claims_pending(callback: CallbackQuery):
    """Show pending ad claims."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    claims = await db.get_pending_ad_claims()

    # Enrich with usernames
    for claim in claims:
        user = await db.get_user(claim['user_id'])
        claim['username'] = user.get('username') if user else f"User {claim['user_id']}"

    if not claims:
        await callback.message.edit_text(
            "✅ No pending ad claims",
            reply_markup=back_button('en', "admin:ads")
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📸 <b>Pending Ad Claims</b>",
        reply_markup=admin_pending_claims_keyboard(claims)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ad_claim:"))
async def admin_ad_claim_detail(callback: CallbackQuery):
    """Show ad claim detail."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    claim_id = int(callback.data.split(":")[1])
    claim = await db.get_ad_claim(claim_id)

    if not claim:
        await callback.answer("Claim not found", show_alert=True)
        return

    ad = await db.get_ad_task(claim['ad_id'])
    ad_title = ad.get('title', 'Ad') if ad else 'Unknown Ad'

    user = await db.get_user(claim['user_id'])
    claim['username'] = user.get('username') if user else f"User {claim['user_id']}"
    claim['points_reward'] = ad.get('points_reward', 0) if ad else 0

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_ad_claim_approve:{claim_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_ad_claim_reject:{claim_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:ad_claims_pending")]
    ])

    await callback.message.edit_text(
        messages.admin_ad_claim_detail(claim, ad_title),
        reply_markup=kb,
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ad_claim_approve:"))
async def admin_ad_claim_approve(callback: CallbackQuery, bot: Bot):
    """Approve ad claim."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    claim_id = int(callback.data.split(":")[1])
    claim = await db.get_ad_claim(claim_id)

    if not claim or claim['status'] != 'pending':
        await callback.answer("Claim not found or not pending", show_alert=True)
        return

    ad = await db.get_ad_task(claim['ad_id'])
    if not ad:
        await callback.answer("Ad not found", show_alert=True)
        return

    # Update claim
    await db.update_ad_claim(
        claim_id, 'approved',
        reviewed_at=datetime.utcnow().isoformat(),
        reviewed_by=callback.from_user.id
    )

    # Increment ad claims count
    await db.increment_ad_claims(claim['ad_id'])

    # Credit points
    new_balance = await db.add_points(claim['user_id'], ad['points_reward'])

    # Notify user
    user = await db.get_user(claim['user_id'])
    lang = user.get('language', 'ar') if user else 'ar'
    try:
        await bot.send_message(
            claim['user_id'],
            messages.ad_claim_approved(lang, ad['points_reward']),
            parse_mode='HTML'
        )
    except Exception:
        pass

    await callback.answer("Claim approved, points credited")
    await admin_ad_claims_pending(callback)


@router.callback_query(F.data.startswith("admin_ad_claim_reject:"))
async def admin_ad_claim_reject_start(callback: CallbackQuery, state: FSMContext):
    """Start rejecting ad claim - ask for reason."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    claim_id = int(callback.data.split(":")[1])
    await state.update_data(claim_id=claim_id)
    await state.set_state(AdminState.REPLY_TICKET)  # Reuse state for text input

    await callback.message.edit_text(
        messages.admin_reject_reason_prompt(),
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.REPLY_TICKET)
async def admin_ad_claim_reject_save(message: Message, state: FSMContext, bot: Bot):
    """Save rejection reason."""
    data = await state.get_data()
    claim_id = data.get('claim_id')

    if not claim_id:
        await message.answer("❌ Invalid operation")
        await state.clear()
        return

    claim = await db.get_ad_claim(claim_id)
    if not claim:
        await message.answer("Claim not found")
        await state.clear()
        return

    reason = message.text.strip()

    await db.update_ad_claim(
        claim_id, 'rejected',
        reject_reason=reason,
        reviewed_at=datetime.utcnow().isoformat(),
        reviewed_by=message.from_user.id
    )

    # Notify user
    user = await db.get_user(claim['user_id'])
    lang = user.get('language', 'ar') if user else 'ar'
    try:
        await bot.send_message(
            claim['user_id'],
            messages.ad_claim_rejected(lang, reason),
            parse_mode='HTML'
        )
    except Exception:
        pass

    await state.clear()
    await message.answer(
        "✅ Claim rejected",
        reply_markup=back_button('en', "admin:ad_claims_pending")
    )


# ==================== ADD AD ====================

@router.callback_query(F.data == "admin:add_ad")
async def admin_add_ad_start(callback: CallbackQuery, state: FSMContext):
    """Start add ad flow."""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    await state.set_state(AdminState.ADD_AD_TITLE)
    await callback.message.edit_text(
        "📺 <b>Add Ad</b>\n\nEnter ad title:",
        reply_markup=cancel_keyboard('en')
    )
    await callback.answer()


@router.message(AdminState.ADD_AD_TITLE)
async def admin_add_ad_title(message: Message, state: FSMContext):
    """Save ad title and ask for URL."""
    await state.update_data(ad_title=message.text.strip())
    await state.set_state(AdminState.ADD_AD_URL)
    await message.answer(
        "📺 <b>Add Ad</b>\n\nEnter ad URL:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_AD_URL)
async def admin_add_ad_url(message: Message, state: FSMContext):
    """Save URL and ask for points reward."""
    await state.update_data(ad_url=message.text.strip())
    await state.set_state(AdminState.ADD_AD_POINTS)
    await message.answer(
        "📺 <b>Add Ad</b>\n\nEnter points reward:",
        reply_markup=cancel_keyboard('en')
    )


@router.message(AdminState.ADD_AD_POINTS)
async def admin_add_ad_points(message: Message, state: FSMContext):
    """Save points reward and ask for type."""
    try:
        points = int(message.text.strip())
        if points <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number")
        return

    await state.update_data(ad_points=points)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        "📺 <b>Add Ad</b>\n\nSelect type:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣ Once Per User", callback_data="admin_ad_type:1")],
            [InlineKeyboardButton(text="🔄 Cooldown", callback_data="admin_ad_type:0")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="admin:ads")]
        ])
    )


@router.callback_query(F.data.startswith("admin_ad_type:"))
async def admin_add_ad_type(callback: CallbackQuery, state: FSMContext):
    """Save type and either finish or ask for cooldown."""
    is_once = int(callback.data.split(":")[1])
    await state.update_data(ad_is_once=is_once)

    if is_once:
        # Finish creating ad with defaults
        data = await state.get_data()
        ad_id = await db.create_ad_task(
            title=data['ad_title'],
            url=data['ad_url'],
            points_reward=data['ad_points'],
            is_once_per_user=1,
            cooldown_hours=24
        )
        await state.clear()
        await callback.message.edit_text(
            f"✅ Ad created!\n📢 {data['ad_title']} — {data['ad_points']} pts — Once Per User\n"
            f"🆔 Ad ID: <code>{ad_id}</code>",
            reply_markup=back_button('en', "admin:ads"),
            parse_mode='HTML'
        )
    else:
        await state.set_state(AdminState.ADD_AD_COOLDOWN)
        await callback.message.edit_text(
            "📺 <b>Add Ad</b>\n\nEnter cooldown hours (e.g. 24):",
            reply_markup=cancel_keyboard('en')
        )
    await callback.answer()


@router.message(AdminState.ADD_AD_COOLDOWN)
async def admin_add_ad_cooldown(message: Message, state: FSMContext):
    """Save cooldown and create ad."""
    try:
        hours = int(message.text.strip())
        if hours <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number")
        return

    data = await state.get_data()
    ad_id = await db.create_ad_task(
        title=data['ad_title'],
        url=data['ad_url'],
        points_reward=data['ad_points'],
        is_once_per_user=0,
        cooldown_hours=hours
    )
    await state.clear()
    await message.answer(
        f"✅ Ad created!\n📢 {data['ad_title']} — {data['ad_points']} pts — Cooldown: {hours}h\n"
        f"🆔 Ad ID: <code>{ad_id}</code>",
        reply_markup=back_button('en', "admin:ads"),
        parse_mode='HTML'
    )


# ==================== CANCEL ====================

@router.callback_query(F.data == "admin:cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel admin action."""
    await state.clear()
    
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        messages.admin_panel(),
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()
