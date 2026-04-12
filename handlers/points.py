"""
Points handler for Telegram Store Bot.
Handles balance, coupons, daily bonus, and orders.
"""

import random
import string
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    points_keyboard, orders_keyboard, order_detail_keyboard,
    daily_bonus_available_keyboard, daily_bonus_wait_keyboard,
    buy_points_keyboard, back_button, cancel_keyboard
)
import messages
from config import config

router = Router()


class PointsState(StatesGroup):
    """Points FSM states."""
    ENTER_COUPON = State()


# ==================== MY POINTS ====================

@router.callback_query(F.data == "menu:points")
async def my_points(callback: CallbackQuery):
    """Show user's points."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    balance = user.get('points', 0)
    total_earned = user.get('total_earned', 0)
    total_spent = user.get('total_spent', 0)
    
    await callback.message.edit_text(
        messages.my_points(lang, balance, total_earned, total_spent),
        reply_markup=points_keyboard(lang),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== COUPON SYSTEM ====================

@router.callback_query(F.data == "points:coupon")
async def enter_coupon(callback: CallbackQuery, state: FSMContext):
    """Prompt user to enter coupon code."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    await state.set_state(PointsState.ENTER_COUPON)
    await callback.message.edit_text(
        messages.coupon_prompt(lang),
        reply_markup=cancel_keyboard(lang)
    )
    await callback.answer()


@router.message(PointsState.ENTER_COUPON)
async def process_coupon(message: Message, state: FSMContext):
    """Process coupon code."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await message.answer("Please use /start first")
        await state.clear()
        return
    
    lang = user.get('language', 'ar')
    code = message.text.strip().upper()
    
    # Get coupon
    coupon = await db.get_coupon(code)
    
    if not coupon:
        await message.answer(
            messages.coupon_invalid(lang),
            reply_markup=back_button(lang, "menu:points")
        )
        await state.clear()
        return
    
    # Check if active
    if not coupon.get('is_active'):
        await message.answer(
            messages.coupon_invalid(lang, "Coupon is inactive"),
            reply_markup=back_button(lang, "menu:points")
        )
        await state.clear()
        return
    
    # Check expiration
    expires_at = coupon.get('expires_at')
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        if expires_at < datetime.utcnow():
            await message.answer(
                messages.coupon_invalid(lang, "Coupon has expired"),
                reply_markup=back_button(lang, "menu:points")
            )
            await state.clear()
            return
    
    # Check max uses
    max_uses = coupon.get('max_uses', 1)
    used_count = coupon.get('used_count', 0)
    if max_uses > 0 and used_count >= max_uses:
        await message.answer(
            messages.coupon_limit_reached(lang),
            reply_markup=back_button(lang, "menu:points")
        )
        await state.clear()
        return
    
    # Check if user already used this coupon
    if await db.has_used_coupon(coupon['id'], telegram_id):
        await message.answer(
            messages.coupon_already_used(lang),
            reply_markup=back_button(lang, "menu:points")
        )
        await state.clear()
        return
    
    # Apply coupon
    points_value = coupon['points_value']
    await db.use_coupon(coupon['id'], telegram_id)
    new_balance = await db.add_points(telegram_id, points_value)
    
    await message.answer(
        messages.coupon_success(lang, points_value, new_balance),
        reply_markup=back_button(lang, "menu:points"),
        parse_mode='HTML'
    )
    await state.clear()


# ==================== ORDERS ====================

@router.callback_query(F.data == "points:orders")
async def show_orders(callback: CallbackQuery):
    """Show user's orders."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    orders = await db.get_user_orders(telegram_id, limit=20)
    
    if not orders:
        await callback.message.edit_text(
            messages.no_orders(lang),
            reply_markup=back_button(lang, "menu:points")
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        t(lang, "📋 طلباتك:", "📋 Your Orders:") if lang == 'ar' else "📋 Your Orders:",
        reply_markup=orders_keyboard(lang, orders)
    )
    await callback.answer()


def t(lang: str, ar: str, en: str) -> str:
    return ar if lang == 'ar' else en


@router.callback_query(F.data.startswith("order:"))
async def show_order_detail(callback: CallbackQuery):
    """Show order details."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    order_id = callback.data.split(":", 1)[1]
    lang = user.get('language', 'ar')
    
    # Get order
    order = await db.get_order(order_id)
    if not order or order['user_id'] != telegram_id:
        await callback.answer("Order not found", show_alert=True)
        return
    
    # Show order content
    content = order.get('content', 'No content available')
    
    await callback.message.edit_text(
        f"📦 <b>{t(lang, 'تفاصيل الطلب', 'Order Details')}</b>\n\n"
        f"📋 {t(lang, 'رقم الطلب', 'Order ID')}: <code>{order_id}</code>\n"
        f"💰 {order['amount']} {t(lang, 'نقطة', 'points')}\n"
        f"📅 {order['created_at'][:10]}\n\n"
        f"📦 {t(lang, 'المحتوى', 'Content')}:\n<code>{content}</code>",
        reply_markup=order_detail_keyboard(lang, order_id),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== DAILY BONUS ====================

@router.callback_query(F.data == "menu:daily_bonus")
async def daily_bonus(callback: CallbackQuery):
    """Show daily bonus screen."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    # Check if can claim
    can_claim = await db.can_claim_daily_bonus(telegram_id)
    
    if can_claim:
        daily_points = int(await db.get_setting('daily_bonus_points', '10'))
        await callback.message.edit_text(
            messages.daily_bonus_available(lang, daily_points),
            reply_markup=daily_bonus_available_keyboard(lang)
        )
    else:
        # Show time remaining
        remaining = await db.get_bonus_time_remaining(telegram_id)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        
        await callback.message.edit_text(
            messages.daily_bonus_wait(lang, hours, minutes, seconds),
            reply_markup=daily_bonus_wait_keyboard(lang),
            parse_mode='HTML'
        )
    
    await callback.answer()


@router.callback_query(F.data == "daily:claim")
async def claim_daily_bonus(callback: CallbackQuery):
    """Claim daily bonus."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    # Re-check if can claim
    can_claim = await db.can_claim_daily_bonus(telegram_id)
    if not can_claim:
        await callback.answer(t(lang, "⏳ ليس الوقت بعد!", "⏳ Not time yet!"), show_alert=True)
        return
    
    # Claim bonus
    streak = await db.claim_daily_bonus(telegram_id)
    daily_points = int(await db.get_setting('daily_bonus_points', '10'))
    
    # Add points
    await db.add_points(telegram_id, daily_points)
    
    await callback.message.edit_text(
        messages.daily_bonus_claimed(lang, daily_points, streak),
        reply_markup=back_button(lang, "menu:main"),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== BUY POINTS WITH STARS ====================

@router.callback_query(F.data == "menu:buy_points")
async def buy_points_home(callback: CallbackQuery):
    """Show buy points packages."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    packages = await db.get_stars_packages(active_only=True)
    
    if not packages:
        await callback.message.edit_text(
            messages.buy_points_no_packages(lang),
            reply_markup=back_button(lang, "menu:main")
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        messages.buy_points_home(lang),
        reply_markup=buy_points_keyboard(lang, packages)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stars_pkg:"))
async def select_stars_package(callback: CallbackQuery):
    """Send Stars invoice."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    package_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')
    
    # Get package
    package = await db.get_stars_package(package_id)
    if not package or not package.get('is_active'):
        await callback.answer("Package not found", show_alert=True)
        return
    
    stars = package['stars_amount']
    points = package['points_amount']
    
    # Create invoice
    title = messages.buy_points_invoice_title(lang, stars, points)
    description = messages.buy_points_invoice_description(lang, stars, points)
    
    # Payload contains package_id for processing
    payload = f"stars_pkg:{package_id}"
    
    prices = [LabeledPrice(label="XTR", amount=stars)]
    
    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",
        prices=prices
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    """Process pre-checkout query."""
    # Always accept
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, bot: Bot):
    """Process successful Stars payment."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await message.answer("Please use /start first")
        return
    
    lang = user.get('language', 'ar')
    payment = message.successful_payment
    
    # Extract package_id from payload
    payload = payment.invoice_payload
    if not payload.startswith("stars_pkg:"):
        await message.answer("Invalid payment")
        return
    
    package_id = int(payload.split(":")[1])
    package = await db.get_stars_package(package_id)
    
    if not package:
        await message.answer("Package not found")
        return
    
    points = package['points_amount']
    stars = package['stars_amount']
    
    # Generate unique coupon code
    coupon_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    # Create coupon for this purchase
    await db.create_coupon(
        code=coupon_code,
        points_value=points,
        max_uses=1,
        expires_at=None,
        created_by=config.SUPER_ADMIN_ID
    )
    
    # Apply coupon immediately
    coupon = await db.get_coupon(coupon_code)
    if coupon:
        await db.use_coupon(coupon['id'], telegram_id)
        new_balance = await db.add_points(telegram_id, points)
    else:
        new_balance = user.get('points', 0)
    
    # Notify admin
    try:
        await bot.send_message(
            config.SUPER_ADMIN_ID,
            f"💰 <b>Stars Payment Received</b>\n\n"
            f"👤 User: <code>{telegram_id}</code>\n"
            f"⭐ Stars: {stars}\n"
            f"💎 Points: {points}",
            parse_mode='HTML'
        )
    except Exception:
        pass
    
    # Send success message
    await message.answer(
        messages.buy_points_success(lang, points, new_balance, coupon_code),
        reply_markup=back_button(lang, "menu:main"),
        parse_mode='HTML'
    )


# ==================== CANCEL HANDLER ====================

@router.callback_query(F.data == "admin:cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel current action."""
    await state.clear()
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    await callback.message.edit_text(
        messages.main_menu(lang, user.get('first_name', 'User'), user.get('points', 0)),
        reply_markup=main_menu_keyboard(lang, await db.is_admin(telegram_id)),
        parse_mode='HTML'
    )
    await callback.answer()


# Need to import main_menu_keyboard here to avoid circular import
from keyboards import main_menu_keyboard
