"""
Store handler for Telegram Store Bot.
Handles categories, products, and purchase flow.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    categories_keyboard, products_keyboard, product_detail_keyboard,
    purchase_confirm_keyboard, back_button, insufficient_points_keyboard
)
import messages

router = Router()


class PurchaseState(StatesGroup):
    """Purchase FSM states."""
    CONFIRM = State()


# ==================== STORE HOME ====================

@router.callback_query(F.data == "menu:store")
async def store_home(callback: CallbackQuery):
    """Show store categories."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')
    categories = await db.get_categories(active_only=True)

    # Check if stars withdrawal is open - add "Buy Stars" category at top
    stars_withdrawal = await db.get_setting('stars_withdrawal_open', 'true')
    if stars_withdrawal.lower() == 'true':
        # We'll show the Buy Stars option as a special category
        pass

    if not categories:
        await callback.message.edit_text(
            messages.category_empty(lang),
            reply_markup=back_button(lang, "menu:main")
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        messages.store_home(lang),
        reply_markup=categories_keyboard(lang, categories)
    )
    await callback.answer()


# ==================== CATEGORY PRODUCTS ====================

@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery):
    """Show products in a category."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    category_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')
    
    # Get category
    category = await db.get_category(category_id)
    if not category:
        await callback.answer("Category not found", show_alert=True)
        return
    
    # Get products
    products = await db.get_products(category_id=category_id, visible_only=True)
    
    if not products:
        await callback.message.edit_text(
            messages.category_empty(lang),
            reply_markup=back_button(lang, "menu:store")
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        messages.store_home(lang),
        reply_markup=products_keyboard(lang, products)
    )
    await callback.answer()


# ==================== PRODUCT DETAIL ====================

@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery):
    """Show product details."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')
    user_points = user.get('points', 0)
    
    # Get product
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return
    
    # Check if on waiting list
    on_waiting = await db.is_on_waiting_list(telegram_id, product_id)
    
    await callback.message.edit_text(
        messages.product_detail(lang, product),
        reply_markup=product_detail_keyboard(lang, product, user_points, on_waiting),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== WAITING LIST ====================

@router.callback_query(F.data.startswith("wait:"))
async def add_to_waiting_list(callback: CallbackQuery):
    """Add user to waiting list."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')
    
    # Check if already on list
    if await db.is_on_waiting_list(telegram_id, product_id):
        await callback.answer(messages.already_on_waiting_list(lang), show_alert=True)
        return
    
    # Add to waiting list
    await db.add_to_waiting_list(telegram_id, product_id)
    await callback.answer(messages.added_to_waiting_list(lang), show_alert=True)
    
    # Refresh product view
    product = await db.get_product(product_id)
    user_points = user.get('points', 0)
    
    try:
        await callback.message.edit_text(
            messages.product_detail(lang, product),
            reply_markup=product_detail_keyboard(lang, product, user_points, True),
            parse_mode='HTML'
        )
    except Exception:
        pass


# ==================== PURCHASE FLOW ====================

@router.callback_query(F.data.startswith("buy:"))
async def initiate_purchase(callback: CallbackQuery, state: FSMContext):
    """Initiate purchase flow."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    product_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')
    user_points = user.get('points', 0)

    # Check if user is restricted
    if user.get('is_restricted'):
        await callback.answer(
            messages.account_restricted(lang),
            show_alert=True
        )
        return

    # Get product
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return

    # Check stock
    if product['stock'] <= 0:
        await callback.answer(messages.purchase_out_of_stock(lang), show_alert=True)
        return

    # Check balance - show smart redirect if insufficient
    if user_points < product['points_price']:
        needed = product['points_price'] - user_points
        await callback.message.edit_text(
            messages.insufficient_points_smart(lang, needed),
            reply_markup=insufficient_points_keyboard(lang, product_id)
        )
        await callback.answer()
        return

    # Show confirmation
    product_name = product['name_ar'] if lang == 'ar' else product['name_en']
    await state.set_state(PurchaseState.CONFIRM)
    await state.update_data(product_id=product_id)

    await callback.message.edit_text(
        messages.purchase_confirm(lang, product_name, product['points_price'], user_points),
        reply_markup=purchase_confirm_keyboard(lang, product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_buy:"))
async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    """Confirm and process purchase."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    product_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')
    user_points = user.get('points', 0)

    # Get product (re-check)
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Product not found", show_alert=True)
        await state.clear()
        return

    # Re-check stock (race condition protection)
    if product['stock'] <= 0:
        await callback.answer(messages.purchase_out_of_stock(lang), show_alert=True)
        await state.clear()
        return

    # Re-check balance
    price = product['points_price']
    if user_points < price:
        needed = price - user_points
        await callback.message.edit_text(
            messages.insufficient_points_smart(lang, needed),
            reply_markup=insufficient_points_keyboard(lang, product_id)
        )
        await state.clear()
        await callback.answer()
        return

    # Process purchase based on delivery type
    delivery_type = product.get('delivery_type', product.get('type', 'unlimited_file'))
    content = None
    file_id = None

    try:
        if delivery_type in ('oncesell_text', 'oncesell_file'):
            # Get stock item
            stock_item = await db.get_available_stock(product_id)
            if not stock_item:
                await callback.answer(messages.purchase_out_of_stock(lang), show_alert=True)
                await state.clear()
                return

            content = stock_item['content']
            if delivery_type == 'oncesell_file':
                file_id = content  # file_id stored in content
            await db.mark_stock_sold(stock_item['id'], telegram_id)
            # Permanently delete the stock item
            await db.delete_stock_item(stock_item['id'])

        elif delivery_type == 'unlimited_file':
            # Use file_id from product
            file_id = product.get('file_id')
            content = "File delivered"

        # Deduct points
        await db.remove_points(telegram_id, price)

        # Create order
        order_id = await db.create_order(
            user_id=telegram_id,
            product_id=product_id,
            amount=price,
            content=content
        )

        # Update product stock count
        new_stock = product['stock'] - 1
        await db.update_product(product_id, stock=new_stock)

        # Handle out-of-stock for one-time products
        waiting_count = 0
        if new_stock <= 0 and delivery_type in ('oncesell_text', 'oncesell_file'):
            # Hide product
            await db.update_product(product_id, is_visible=0)

            # Get waiting list count
            waiting_list = await db.get_waiting_list(product_id)
            waiting_count = len(waiting_list)

            # Notify admins
            from config import config
            product_name = product['name_en']
            try:
                await callback.bot.send_message(
                    config.SUPER_ADMIN_ID,
                    f"⚠️ <b>Product Out of Stock</b>\n\n"
                    f"📦 {product_name}\n"
                    f"🆔 Product ID: <code>{product_id}</code>\n"
                    f"🔔 Waiting list: {waiting_count} users",
                    parse_mode='HTML'
                )
            except Exception:
                pass

        # Low stock alert
        low_stock_threshold = int(await db.get_setting('low_stock_threshold', '5'))
        if new_stock <= low_stock_threshold and new_stock > 0 and delivery_type in ('oncesell_text', 'oncesell_file'):
            waiting_list = await db.get_waiting_list(product_id)
            from config import config
            product_name = product['name_en']
            try:
                await callback.bot.send_message(
                    config.SUPER_ADMIN_ID,
                    messages.admin_low_stock_alert(product_name, new_stock, len(waiting_list)),
                    parse_mode='HTML'
                )
            except Exception:
                pass

        # Clear state
        await state.clear()

        # Send order receipt
        product_name = product['name_ar'] if lang == 'ar' else product['name_en']
        date_str = f"{__import__('datetime').datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC"
        await callback.message.edit_text(
            messages.order_receipt(lang, order_id, product_name, price, date_str),
            parse_mode='HTML'
        )

        # Deliver content
        if delivery_type == 'unlimited_file' and file_id:
            try:
                await callback.message.answer_document(file_id)
            except Exception as e:
                print(f"Failed to send file: {e}")
        elif delivery_type == 'oncesell_file' and file_id:
            try:
                await callback.message.answer_document(file_id)
            except Exception as e:
                print(f"Failed to send file: {e}")
        elif delivery_type == 'oncesell_text' and content:
            try:
                await callback.message.answer(
                    f"📦 <b>Your Item:</b>\n<code>{content}</code>",
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Failed to send text: {e}")

        await callback.answer()

    except Exception as e:
        print(f"Purchase error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer(messages.error_generic(lang), show_alert=True)
        await state.clear()
