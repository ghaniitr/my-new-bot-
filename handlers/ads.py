"""
Ad Rewards handler for Telegram Store Bot V2.
Handles user ad viewing, screenshot submission, and admin approval flow.
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    ads_list_keyboard, ad_detail_keyboard, back_button, cancel_keyboard
)
import messages

router = Router()


class AdState(StatesGroup):
    """Ad FSM states."""
    SUBMIT_SCREENSHOT = State()


# ==================== ADS HOME ====================

@router.callback_query(F.data == "menu:ads")
async def ads_home(callback: CallbackQuery):
    """Show ads list."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang = user.get('language', 'ar')
    ads = await db.get_ad_tasks(active_only=True)

    if not ads:
        await callback.message.edit_text(
            messages.ads_home(lang) + "\n\n" + (
                "📭 لا توجد إعلانات متاحة حالياً." if lang == 'ar' else "📭 No ads available currently."
            ),
            reply_markup=back_button(lang, "menu:main")
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        messages.ads_home(lang),
        reply_markup=ads_list_keyboard(lang, ads)
    )
    await callback.answer()


# ==================== AD DETAIL ====================

@router.callback_query(F.data.startswith("ad:"))
async def ad_detail(callback: CallbackQuery):
    """Show ad detail."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    ad_id = int(callback.data.split(":")[1])
    lang = user.get('language', 'ar')

    ad = await db.get_ad_task(ad_id)
    if not ad or not ad.get('is_active'):
        await callback.answer("Ad not found", show_alert=True)
        return

    # Check eligibility
    has_approved = await db.has_approved_ad_claim(telegram_id, ad_id)
    has_pending = await db.has_pending_ad_claim(telegram_id, ad_id)
    cooldown_remaining = None

    if has_approved:
        pass  # Already claimed
    elif has_pending:
        pass  # Already pending
    elif not ad.get('is_once_per_user'):
        # Check cooldown
        last_claimed = await db.get_last_approved_claim_time(telegram_id, ad_id)
        if last_claimed:
            from datetime import datetime, timedelta
            cooldown_hours = ad.get('cooldown_hours', 24)
            next_available = last_claimed + timedelta(hours=cooldown_hours)
            now = datetime.utcnow()
            if now < next_available:
                remaining = next_available - now
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                cooldown_remaining = f"{hours}h {minutes}m"

    await callback.message.edit_text(
        messages.ad_detail(lang, ad),
        reply_markup=ad_detail_keyboard(lang, ad, has_pending, has_approved, cooldown_remaining),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== SUBMIT SCREENSHOT ====================

@router.callback_query(F.data.startswith("ad_submit:"))
async def ad_submit_screenshot(callback: CallbackQuery, state: FSMContext):
    """Prompt user to send screenshot."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    # Check if restricted
    if user.get('is_restricted'):
        await callback.answer(messages.account_restricted(user.get('language', 'ar')), show_alert=True)
        return

    ad_id = int(callback.data.split(":")[1])
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdState.SUBMIT_SCREENSHOT)  

    lang = user.get('language', 'ar')
    await callback.message.edit_text(
        (
            f"📸 {t(lang, 'يرجى إرسال لقطة شاشة الآن:', 'Please send your screenshot now:')}"
        ),
        reply_markup=cancel_keyboard(lang)
    )
    await callback.answer()


@router.message(AdState.SUBMITSCREENSHOT)
async def process_screenshot(message: Message, state: FSMContext, bot: Bot):
    """Process submitted screenshot."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await message.answer("Please use /start first")
        await state.clear()
        return

    lang = user.get('language', 'ar')

    # Get photo or document
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and message.document.thumbnail:
        file_id = message.document.thumbnail.file_id
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        await message.answer(
            t(lang, "❌ يرجى إرسال صورة (لقطة شاشة).", "❌ Please send a photo (screenshot)."),
            reply_markup=cancel_keyboard(lang)
        )
        return

    data = await state.get_data()
    ad_id = data.get('ad_id')

    ad = await db.get_ad_task(ad_id)
    if not ad:
        await message.answer(messages.error_generic(lang))
        await state.clear()
        return

    # Re-check eligibility
    if await db.has_approved_ad_claim(telegram_id, ad_id):
        await message.answer(messages.ad_already_claimed(lang))
        await state.clear()
        return

    if await db.has_pending_ad_claim(telegram_id, ad_id):
        await message.answer(messages.ad_pending_claim(lang))
        await state.clear()
        return

    # Create claim
    claim_id = await db.create_ad_claim(telegram_id, ad_id, file_id)

    await state.clear()

    # Notify user
    await message.answer(
        messages.ad_claim_submitted(lang),
        reply_markup=back_button(lang, "menu:ads"),
        parse_mode='HTML'
    )

    # Forward to ALL admins
    admins = await db.get_admins()
    admin_ids = [admin['telegram_id'] for admin in admins]
    from config import config
    admin_ids.append(config.SUPER_ADMIN_ID)

    username = user.get('username')
    first_name = user.get('first_name', 'Unknown')
    points_reward = ad.get('points_reward', 0)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    claim_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_ad_claim_approve:{claim_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_ad_claim_reject:{claim_id}")
        ]
    ])

    for admin_id in set(admin_ids):
        try:
            await bot.send_photo(
                admin_id,
                photo=file_id,
                caption=messages.admin_ad_claim_detail({
                    'username': username,
                    'user_id': telegram_id,
                    'points_reward': points_reward,
                    'submitted_at': str(__import__('datetime').datetime.utcnow())
                }, ad.get('title', 'Ad')),
                reply_markup=claim_kb,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")


def t(lang: str, ar: str, en: str) -> str:
    return ar if lang == 'ar' else en
