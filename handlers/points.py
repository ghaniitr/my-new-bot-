"""
Points handler for Telegram Store Bot.
Handles balance, coupons, daily bonus, orders, and star transactions.
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
    buy_points_keyboard, back_button, cancel_keyboard,
    buy_points_custom_amount_keyboard, buy_points_confirm_keyboard,
    buy_stars_confirm_keyboard, star_orders_keyboard,
    star_order_pending_keyboard, star_order_delivered_keyboard,
    star_order_confirmed_keyboard, star_order_cancelled_keyboard
)
import messages
from config import config

router = Router()


class PointsState(StatesGroup):
    """Points FSM states."""
    ENTER_COUPON = State()
    BUY_POINTS_CUSTOM = State()
    BUY_STARS_AMOUNT = State()


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
    stars_per_point = int(await db.get_setting('stars_per_point', '4'))

    # Build keyboard with packages + custom amount
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for pkg in packages:
        stars_cost = pkg['points_amount'] * stars_per_point
        buttons.append([InlineKeyboardButton(
            text=f"{pkg['points_amount']} pts — {stars_cost} ⭐",
            callback_data=f"stars_pkg:{pkg['id']}"
        )])

    buttons.append([InlineKeyboardButton(
        text="➕ " + (t(lang, "مبلغ مخصص", "Custom Amount")),
        callback_data="buy_points:custom"
    )])

    buttons.append([InlineKeyboardButton(
        text="◀️ " + (t(lang, "رجوع", "Back")),
        callback_data="menu:main"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        messages.buy_points_rate_info(lang, stars_per_point),
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== BUY POINTS - CUSTOM AMOUNT ====================

@router.callback_query(F.data == "buy_points:custom")
async def buy_points_custom(callback: CallbackQuery, state: FSMContext):
    """Prompt for custom points amount."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')

    await state.set_state(PointsState.BUY_POINTS_CUSTOM)
    await callback.message.edit_text(
        messages.buy_points_custom_prompt(lang),
        reply_markup=cancel_keyboard(lang)
    )
    await callback.answer()


@router.message(PointsState.BUY_POINTS_CUSTOM)
async def process_buy_points_custom(message: Message, state: FSMContext):
    """Process custom points amount and show confirmation."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await message.answer("Please use /start first")
        await state.clear()
        return

    lang = user.get('language', 'ar')

    try:
        points = int(message.text.strip())
        if points <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            t(lang, "❌ يرجى إدخال رقم صحيح.", "❌ Please enter a valid number.")
        )
        return

    stars_per_point = int(await db.get_setting('stars_per_point', '4'))
    stars_cost = points * stars_per_point
    balance = user.get('points', 0)

    await state.update_data(custom_points=points, custom_stars=stars_cost)
    await message.answer(
        messages.buy_points_custom_confirm(lang, points, stars_cost, balance),
        reply_markup=buy_points_confirm_keyboard(lang, points, stars_cost),
        parse_mode='HTML'
    )
    await state.set_state(PointsState.BUY_POINTS_CUSTOM)  # Keep state for confirm


@router.callback_query(F.data.startswith("buy_points_confirm:"))
async def process_buy_points_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Send Stars invoice for custom amount."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')

    data = await state.get_data()
    points = data.get('custom_points')
    stars = data.get('custom_stars')

    if not points or not stars:
        await callback.answer("Invalid data", show_alert=True)
        await state.clear()
        return

    # Create invoice
    title = messages.buy_points_invoice_title(lang, stars, points)
    description = messages.buy_points_invoice_description(lang, stars, points)
    payload = f"buy_points:{points}:{telegram_id}"
    prices = [LabeledPrice(label="XTR", amount=stars)]

    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices
    )

    await state.clear()
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
    payload = payment.invoice_payload
    stars_paid = payment.total_amount  # Amount in stars

    points = 0

    # Check if it's a buy_points payment
    if payload.startswith("buy_points:"):
        parts = payload.split(":")
        if len(parts) >= 3:
            try:
                points = int(parts[1])
            except ValueError:
                pass
    elif payload.startswith("stars_pkg:"):
        package_id = int(payload.split(":")[1])
        package = await db.get_stars_package(package_id)
        if package:
            points = package['points_amount']

    if not points:
        await message.answer("Invalid payment")
        return

    # Credit points
    new_balance = await db.add_points(telegram_id, points)

    # Generate receipt
    coupon_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    await db.create_coupon(
        code=coupon_code,
        points_value=points,
        max_uses=1,
        expires_at=None,
        created_by=config.SUPER_ADMIN_ID
    )

    # Notify admin
    username = user.get('username', 'N/A')
    try:
        await bot.send_message(
            config.SUPER_ADMIN_ID,
            messages.admin_points_purchase_notification(points, stars_paid, telegram_id, username),
            parse_mode='HTML'
        )
    except Exception:
        pass

    # Send receipt
    await message.answer(
        messages.buy_points_receipt(lang, f"PAY-{telegram_id}", points, stars_paid),
        reply_markup=back_button(lang, "menu:main"),
        parse_mode='HTML'
    )


# ==================== STAR ORDERS ====================

@router.callback_query(F.data == "points:star_orders")
async def show_star_orders(callback: CallbackQuery):
    """Show user's star orders."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')
    orders = await db.get_user_star_orders(telegram_id)

    if not orders:
        await callback.message.edit_text(
            t(lang, "📭 ليس لديك طلبات نجوم حتى الآن.", "📭 You don't have any star orders yet."),
            reply_markup=back_button(lang, "menu:points")
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        t(lang, "⭐ <b>طلبات النجوم</b>", "⭐ <b>Star Orders</b>"),
        reply_markup=star_orders_keyboard(lang, orders),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("star_order:"))
async def show_star_order(callback: CallbackQuery):
    """Show star order details."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    lang = user.get('language', 'ar')

    order = await db.get_star_order(order_id)
    if not order or order['user_id'] != telegram_id:
        await callback.answer("Order not found", show_alert=True)
        return

    await callback.message.edit_text(
        messages.star_order_status(lang, order),
        reply_markup=get_star_order_keyboard(lang, order),
        parse_mode='HTML'
    )
    await callback.answer()


def get_star_order_keyboard(lang: str, order: dict):
    """Get appropriate keyboard for star order status."""
    status = order.get('status', 'pending')
    order_id = order['order_id']

    if status == 'pending':
        return star_order_pending_keyboard(lang, order_id)
    elif status == 'delivered':
        return star_order_delivered_keyboard(lang, order_id)
    elif status == 'confirmed':
        return star_order_confirmed_keyboard(lang)
    else:
        return star_order_cancelled_keyboard(lang)


@router.callback_query(F.data.startswith("star_order_cancel:"))
async def cancel_star_order(callback: CallbackQuery):
    """Cancel pending star order."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    lang = user.get('language', 'ar')

    order = await db.get_star_order(order_id)
    if not order or order['user_id'] != telegram_id or order['status'] != 'pending':
        await callback.answer("Order not found or not pending", show_alert=True)
        return

    # Refund points
    await db.add_points(telegram_id, order['points_cost'])

    # Cancel order
    await db.update_star_order_status(
        order_id, 'cancelled', cancelled_at=datetime.utcnow().isoformat()
    )

    await callback.answer(t(lang, "تم إلغاء الطلب", "Order cancelled"))

    # Notify admins
    admins = await db.get_admins()
    from config import config
    for admin in admins:
        try:
            await callback.bot.send_message(
                admin['telegram_id'],
                f"📋 User @{user.get('username', 'N/A')} cancelled order #{order_id}",
                parse_mode='HTML'
            )
        except Exception:
            pass

    # Refresh view
    await show_star_orders(callback)


@router.callback_query(F.data.startswith("star_order_confirm:"))
async def confirm_star_order(callback: CallbackQuery):
    """Confirm receipt of stars."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    lang = user.get('language', 'ar')

    order = await db.get_star_order(order_id)
    if not order or order['user_id'] != telegram_id or order['status'] != 'delivered':
        await callback.answer("Order not found", show_alert=True)
        return

    # Confirm order
    await db.update_star_order_status(
        order_id, 'confirmed', confirmed_at=datetime.utcnow().isoformat()
    )

    await callback.answer(t(lang, "شكراً لتأكيدك! 💚", "Thanks for confirming! 💚"))

    await callback.message.edit_text(
        messages.star_order_status(lang, order),
        reply_markup=star_order_confirmed_keyboard(lang),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("star_order_dispute:"))
async def dispute_star_order(callback: CallbackQuery):
    """Dispute star delivery."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    lang = user.get('language', 'ar')

    order = await db.get_star_order(order_id)
    if not order or order['user_id'] != telegram_id or order['status'] != 'delivered':
        await callback.answer("Order not found", show_alert=True)
        return

    # Refund points
    await db.add_points(telegram_id, order['points_cost'])

    # Cancel order
    await db.update_star_order_status(
        order_id, 'cancelled', cancelled_at=datetime.utcnow().isoformat()
    )

    # Notify admins
    admins = await db.get_admins()
    from config import config
    username = user.get('username', 'N/A')
    for admin in admins:
        try:
            await callback.bot.send_message(
                admin['telegram_id'],
                messages.admin_user_dispute_notification(username, order_id),
                parse_mode='HTML'
            )
        except Exception:
            pass

    await callback.answer(
        messages.star_order_dispute_notification(lang, order_id),
        show_alert=True
    )

    await show_star_orders(callback)


# ==================== BUY STARS WITH POINTS ====================

@router.callback_query(F.data == "menu:buy_stars")
async def buy_stars_home(callback: CallbackQuery, state: FSMContext):
    """Show buy stars (withdrawal) screen."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')

    # Check if restricted
    if user.get('is_restricted'):
        await callback.answer(messages.account_restricted(lang), show_alert=True)
        return

    # Check if withdrawal is open
    stars_withdrawal = await db.get_setting('stars_withdrawal_open', 'true')
    if stars_withdrawal.lower() != 'true':
        await callback.answer(
            t(lang, "❌ سحب النجوم مغلق حالياً.", "❌ Star withdrawal is currently closed."),
            show_alert=True
        )
        return

    stars_per_point = int(await db.get_setting('stars_per_point', '4'))

    await state.set_state(PointsState.BUY_STARS_AMOUNT)
    await callback.message.edit_text(
        messages.buy_stars_rate_info(lang, stars_per_point),
        reply_markup=cancel_keyboard(lang),
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(PointsState.BUY_STARS_AMOUNT)
async def process_buy_stars(message: Message, state: FSMContext):
    """Process buy stars amount and show confirmation."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await message.answer("Please use /start first")
        await state.clear()
        return

    lang = user.get('language', 'ar')

    # Check if restricted
    if user.get('is_restricted'):
        await message.answer(messages.account_restricted(lang))
        await state.clear()
        return

    try:
        stars = int(message.text.strip())
        if stars <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            t(lang, "❌ يرجى إدخال رقم صحيح.", "❌ Please enter a valid number.")
        )
        return

    stars_per_point = int(await db.get_setting('stars_per_point', '4'))
    points_cost = stars // stars_per_point
    balance = user.get('points', 0)

    if balance < points_cost:
        await message.answer(
            t(lang,
              f"❌ رصيد غير كافٍ. تحتاج {points_cost} نقطة.",
              f"❌ Insufficient balance. You need {points_cost} points.")
        )
        await state.clear()
        return

    # Check pending orders limit
    pending_orders = await db.get_user_star_orders(telegram_id)
    pending_count = sum(1 for o in pending_orders if o.get('status') == 'pending')
    if pending_count >= 3:
        await message.answer(
            t(lang,
              "❌ لديك 3 طلبات معلقة كحد أقصى. انتظر حتى تكتمل.",
              "❌ You have the maximum 3 pending orders. Please wait for them to complete.")
        )
        await state.clear()
        return

    await state.update_data(buy_stars=stars, buy_stars_points=points_cost)

    await message.answer(
        messages.buy_stars_confirm(lang, stars, points_cost, balance),
        reply_markup=buy_stars_confirm_keyboard(lang, stars, points_cost),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("buy_stars_confirm:"))
async def confirm_buy_stars(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Confirm and create star order."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')

    # Check if restricted
    if user.get('is_restricted'):
        await callback.answer(messages.account_restricted(lang), show_alert=True)
        await state.clear()
        return

    # Re-check withdrawal open
    stars_withdrawal = await db.get_setting('stars_withdrawal_open', 'true')
    if stars_withdrawal.lower() != 'true':
        await callback.answer(
            t(lang, "❌ سحب النجوم مغلق حالياً.", "❌ Star withdrawal is currently closed."),
            show_alert=True
        )
        await state.clear()
        return

    data = await state.get_data()
    stars = data.get('buy_stars')
    points_cost = data.get('buy_stars_points')

    if not stars or not points_cost:
        await callback.answer("Invalid data", show_alert=True)
        await state.clear()
        return

    # Deduct points
    await db.remove_points(telegram_id, points_cost)

    # Create star order
    order_id = await db.create_star_order(telegram_id, stars, points_cost)

    if not order_id:
        await db.add_points(telegram_id, points_cost)  # Refund on failure
        await callback.answer("Failed to create order", show_alert=True)
        await state.clear()
        return

    await state.clear()

    # Notify user
    await callback.message.edit_text(
        messages.buy_stars_success(lang, order_id, stars, points_cost),
        reply_markup=back_button(lang, "menu:main"),
        parse_mode='HTML'
    )

    # Notify ALL admins
    admins = await db.get_admins()
    from config import config
    admin_ids = [admin['telegram_id'] for admin in admins]
    admin_ids.append(config.SUPER_ADMIN_ID)

    username = user.get('username', 'N/A')
    from datetime import timedelta
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Mark Delivered", callback_data=f"admin_star_deliver:{order_id}"),
            InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"admin_star_cancel:{order_id}")
        ]
    ])

    for admin_id in set(admin_ids):
        try:
            await bot.send_message(
                admin_id,
                messages.admin_star_order_notification({
                    'order_id': order_id,
                    'username': username,
                    'user_id': telegram_id,
                    'stars_amount': stars,
                    'points_cost': points_cost
                }),
                reply_markup=admin_kb,
                parse_mode='HTML'
            )
        except Exception:
            pass


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
