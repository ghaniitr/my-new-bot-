"""
Start handler for Telegram Store Bot.
Handles user onboarding — language → channels → main menu.
Mini app verification is SKIPPED (auto-verified).
"""

import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    language_keyboard, main_menu_keyboard,
    channels_keyboard
)
import messages
from config import config
from scheduler import award_referral_after_delay

router = Router()


class SetupState(StatesGroup):
    LANGUAGE = State()
    CHANNELS = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    telegram_id = message.from_user.id
    username    = message.from_user.username
    first_name  = message.from_user.first_name
    user = await db.get_user(telegram_id)

    if not user:
        referred_by = None
        if message.text and len(message.text.split()) > 1:
            ref_code = message.text.split()[1].strip().upper()
            referrer = await db.fetchone(
                "SELECT telegram_id FROM users WHERE referral_code = ?",
                (ref_code,)
            )
            if referrer and referrer['telegram_id'] != telegram_id:
                referred_by = referrer['telegram_id']

        user = await db.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language='ar',
            referred_by=referred_by
        )
        await db.execute(
            "UPDATE users SET miniapp_verified=1 WHERE telegram_id=?",
            (telegram_id,)
        )
        await state.set_state(SetupState.LANGUAGE)
        await message.answer(
            messages.select_language(),
            reply_markup=language_keyboard()
        )
        return

    if user.get('setup_complete'):
        lang     = user.get('language', 'ar')
        points   = user.get('points', 0)
        is_admin = await db.is_admin(telegram_id)
        await message.answer(
            messages.main_menu(lang, first_name, points),
            reply_markup=main_menu_keyboard(lang, is_admin),
            parse_mode='HTML'
        )
    else:
        await resume_setup(message, state, user)


async def resume_setup(message: Message, state: FSMContext, user: dict):
    lang        = user.get('language', 'ar')
    telegram_id = user['telegram_id']

    if not user.get('miniapp_verified'):
        await db.execute(
            "UPDATE users SET miniapp_verified=1 WHERE telegram_id=?",
            (telegram_id,)
        )

    channels = await db.get_channels(active_only=True)
    if channels:
        missing = []
        for channel in channels:
            try:
                member = await message.bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=telegram_id
                )
                if member.status in ('left', 'kicked', 'banned', 'restricted'):
                    missing.append(channel)
            except Exception:
                continue
        if missing:
            await state.set_state(SetupState.CHANNELS)
            await message.answer(
                messages.channel_join_prompt(lang, missing),
                reply_markup=channels_keyboard(lang, missing)
            )
            return

    await complete_setup(message, user)


@router.callback_query(F.data.startswith("lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    lang        = callback.data.split(":")[1]
    telegram_id = callback.from_user.id

    await db.update_user_language(telegram_id, lang)
    await db.execute(
        "UPDATE users SET miniapp_verified=1 WHERE telegram_id=?",
        (telegram_id,)
    )
    await callback.answer()

    channels = await db.get_channels(active_only=True)
    if channels:
        missing = []
        for channel in channels:
            try:
                member = await callback.bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=telegram_id
                )
                if member.status in ('left', 'kicked', 'banned', 'restricted'):
                    missing.append(channel)
            except Exception:
                continue
        if missing:
            await state.set_state(SetupState.CHANNELS)
            await callback.message.edit_text(
                messages.channel_join_prompt(lang, missing),
                reply_markup=channels_keyboard(lang, missing)
            )
            return

    user = await db.get_user(telegram_id)
    await complete_setup(callback.message, user)


@router.callback_query(F.data == "check_channels")
async def check_channels(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    user        = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang     = user.get('language', 'ar')
    channels = await db.get_channels(active_only=True)
    missing  = []

    for channel in channels:
        try:
            member = await callback.bot.get_chat_member(
                chat_id=channel['channel_id'],
                user_id=telegram_id
            )
            if member.status in ('left', 'kicked', 'banned', 'restricted'):
                missing.append(channel)
        except Exception:
            continue

    if missing:
        await callback.answer(messages.channel_not_joined(lang), show_alert=True)
        try:
            await callback.message.edit_text(
                messages.channel_join_prompt(lang, missing),
                reply_markup=channels_keyboard(lang, missing)
            )
        except Exception:
            pass
        return

    await callback.answer(messages.channel_join_success(lang))
    await complete_setup(callback.message, user)


async def complete_setup(message, user: dict):
    telegram_id = user['telegram_id']
    lang        = user.get('language', 'ar')

    await db.update_user_setup_complete(telegram_id)

    welcome_key = f'welcome_message_{lang}'
    welcome_msg = await db.get_setting(welcome_key)

    referred_by = user.get('referred_by')
    if referred_by:
        await db.create_referral(referred_by, telegram_id)
        asyncio.create_task(
            award_referral_after_delay(message.bot, referred_by, telegram_id)
        )

    is_admin   = await db.is_admin(telegram_id)
    points     = user.get('points', 0)
    first_name = user.get('first_name', 'User')

    await message.answer(
        messages.welcome_message(lang, welcome_msg),
        parse_mode='HTML'
    )
    await message.answer(
        messages.main_menu(lang, first_name, points),
        reply_markup=main_menu_keyboard(lang, is_admin),
        parse_mode='HTML'
    )


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    user        = await db.get_user(telegram_id)

    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return

    lang       = user.get('language', 'ar')
    points     = user.get('points', 0)
    first_name = user.get('first_name', 'User')
    is_admin   = await db.is_admin(telegram_id)

    await callback.message.edit_text(
        messages.main_menu(lang, first_name, points),
        reply_markup=main_menu_keyboard(lang, is_admin),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == "menu:language")
async def change_language(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SetupState.LANGUAGE)
    await callback.message.edit_text(
        messages.select_language(),
        reply_markup=language_keyboard()
    )
    await callback.answer()
