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
    purchase_confirm_keyboard, back_button
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
    
    # Get product
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return
    
    # Check stock
    if product['stock'] <= 0:
        await callback.answer(messages.purchase_out_of_stock(lang), show_alert=True)
        return
    
    # Check balance
    if user_points < product['points_price']:
        needed = product['points_price'] - user_points
        await callback.answer(messages.purchase_not_enough_points(lang, needed), show_alert=True)
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
        await callback.answer(messages.purchase_not_enough_points(lang, needed), show_alert=True)
        await state.clear()
        return
    
    # Process purchase based on product type
    product_type = product['type']
    content = None
    
    try:
        if product_type in ('code', 'account'):
            # Get stock item
            stock_item = await db.get_available_stock(product_id)
            if not stock_item:
                await callback.answer(messages.purchase_out_of_stock(lang), show_alert=True)
                await state.clear()
                return
            
            content = stock_item['content']
            await db.mark_stock_sold(stock_item['id'], telegram_id)
            
        elif product_type in ('pdf', 'zip'):
            # Use file_id
            content = product.get('file_id', 'File delivery error')
        
        # Deduct points
        await db.remove_points(telegram_id, price)
        
        # Create order
        order_id = await db.create_order(
            user_id=telegram_id,
            product_id=product_id,
            amount=price,
            content=content
        )
        
        # Update product stock
        new_stock = product['stock'] - 1
        await db.update_product(product_id, stock=new_stock)
        
        # Notify admin if stock is low
        if new_stock == 0:
            from config import config
            try:
                product_name = product['name_en']
                await callback.bot.send_message(
                    config.SUPER_ADMIN_ID,
                    f"⚠️ <b>Product Out of Stock</b>\n\n"
                    f"📦 {product_name}\n"
                    f"🆔 Product ID: <code>{product_id}</code>",
                    parse_mode='HTML'
                )
            except Exception:
                pass
        
        # Clear state
        await state.clear()
        
        # Send success message
        await callback.message.edit_text(
            messages.purchase_success(lang, order_id, content),
            parse_mode='HTML'
        )
        
        # Deliver file if applicable
        if product_type in ('pdf', 'zip') and content:
            try:
                await callback.message.answer_document(content)
            except Exception as e:
                print(f"Failed to send file: {e}")
        
        await callback.answer()
        
    except Exception as e:
        print(f"Purchase error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer(messages.error_generic(lang), show_alert=True)
        await state.clear()
