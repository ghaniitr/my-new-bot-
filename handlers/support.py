"""
Support handler for Telegram Store Bot.
Handles support tickets.
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import support_keyboard, back_button, cancel_keyboard
import messages
from config import config

router = Router()


class SupportState(StatesGroup):
    """Support FSM states."""
    ENTER_MESSAGE = State()


@router.callback_query(F.data == "menu:support")
async def support_intro(callback: CallbackQuery, state: FSMContext):
    """Show support intro."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    await state.set_state(SupportState.ENTER_MESSAGE)
    await callback.message.edit_text(
        messages.support_intro(lang),
        reply_markup=cancel_keyboard(lang)
    )
    await callback.answer()


@router.message(SupportState.ENTER_MESSAGE)
async def process_support_message(message: Message, state: FSMContext, bot: Bot):
    """Process support message and create ticket."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await message.answer("Please use /start first")
        await state.clear()
        return
    
    lang = user.get('language', 'ar')
    support_text = message.text.strip()
    
    if len(support_text) < 10:
        await message.answer(
            t(lang, "⚠️ الرسالة قصيرة جداً. يرجى كتابة رسالة أطول.", 
              "⚠️ Message too short. Please write a longer message."),
            reply_markup=cancel_keyboard(lang)
        )
        return
    
    # Create ticket
    ticket_id = await db.create_ticket(telegram_id, support_text)
    
    # Notify all admins
    admins = await db.get_admins()
    admin_ids = [admin['telegram_id'] for admin in admins]
    admin_ids.append(config.SUPER_ADMIN_ID)
    
    username = user.get('username')
    first_name = user.get('first_name', 'Unknown')
    
    for admin_id in set(admin_ids):
        try:
            await bot.send_message(
                admin_id,
                f"🎫 <b>New Support Ticket</b>\n\n"
                f"🆔 Ticket: <code>#{ticket_id}</code>\n"
                f"👤 User: <code>{telegram_id}</code>\n"
                f"📛 Name: {first_name}\n"
                f"🔗 Username: @{username if username else 'N/A'}\n\n"
                f"📝 Message:\n{support_text[:500]}",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")
    
    await message.answer(
        messages.support_sent(lang, ticket_id),
        reply_markup=back_button(lang, "menu:main"),
        parse_mode='HTML'
    )
    await state.clear()


def t(lang: str, ar: str, en: str) -> str:
    return ar if lang == 'ar' else en
