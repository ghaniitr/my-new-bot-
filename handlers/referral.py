"""
Referral handler for Telegram Store Bot.
Handles referral links and stats.
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import db
from keyboards import referral_keyboard, back_button
import messages

router = Router()


@router.callback_query(F.data == "menu:referral")
async def referral_home(callback: CallbackQuery, bot: Bot):
    """Show referral screen."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    # Get bot username for referral link
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    referral_code = user.get('referral_code', '')
    
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    # Get stats
    active_count = await db.get_active_referrals_count(telegram_id)
    total_earned = await db.get_referrals_earned(telegram_id)
    
    await callback.message.edit_text(
        messages.referral_home(lang, referral_link, active_count, total_earned),
        reply_markup=referral_keyboard(lang, referral_link),
        parse_mode='HTML'
    )
    await callback.answer()
