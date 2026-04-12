"""
Start handler for Telegram Store Bot.
Handles user onboarding without phone verification.
"""

import asyncio
import random
import string

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    language_keyboard, main_menu_keyboard, miniapp_keyboard,
    miniapp_verified_keyboard, channels_keyboard
)
import messages
from config import config
from scheduler import award_referral_after_delay

router = Router()


class SetupState(StatesGroup):
    """Setup FSM states."""
    LANGUAGE = State()
    MINIAPP = State()
    CHANNELS = State()


# ==================== /START COMMAND ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Handle /start command."""
    await state.clear()
    
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Get or create user
    user = await db.get_user(telegram_id)
    
    if not user:
        # Extract referral code from start command
        referred_by = None
        if message.text and len(message.text.split()) > 1:
            ref_code = message.text.split()[1].strip()
            # Find referrer by referral code
            referrer = await db.fetchone(
                "SELECT telegram_id FROM users WHERE referral_code = ?",
                (ref_code.upper(),)
            )
            if referrer:
                referred_by = referrer['telegram_id']
        
        # Create new user
        user = await db.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language='ar',  # Default to Arabic
            referred_by=referred_by
        )
        
        # Start setup flow
        await state.set_state(SetupState.LANGUAGE)
        await message.answer(
            messages.select_language(),
            reply_markup=language_keyboard()
        )
        return
    
    # Existing user
    if user.get('setup_complete'):
        # Show main menu
        lang = user.get('language', 'ar')
        points = user.get('points', 0)
        is_admin = await db.is_admin(telegram_id)
        
        await message.answer(
            messages.main_menu(lang, first_name, points),
            reply_markup=main_menu_keyboard(lang, is_admin),
            parse_mode='HTML'
        )
    else:
        # Resume setup flow
        await resume_setup(message, state, user)


async def resume_setup(message: Message, state: FSMContext, user: dict):
    """Resume setup flow from current state."""
    lang = user.get('language', 'ar')
    telegram_id = user['telegram_id']
    
    # Check mini app verification
    if not user.get('miniapp_verified'):
        await state.set_state(SetupState.MINIAPP)
        await message.answer(
            messages.miniapp_prompt(lang),
            reply_markup=miniapp_keyboard(lang, telegram_id)
        )
        return
    
    # Check channels
    channels = await db.get_channels(active_only=True)
    if channels:
        # Verify channel membership
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
    
    # All checks passed - complete setup
    await complete_setup(message, user)


# ==================== LANGUAGE SELECTION ====================

@router.callback_query(F.data.startswith("lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    """Process language selection."""
    lang = callback.data.split(":")[1]
    telegram_id = callback.from_user.id
    
    # Update user language
    await db.update_user_language(telegram_id, lang)
    
    # Move to mini app verification
    await state.set_state(SetupState.MINIAPP)
    await callback.message.edit_text(
        messages.miniapp_prompt(lang),
        reply_markup=miniapp_keyboard(lang, telegram_id)
    )
    await callback.answer()


# ==================== MINI APP VERIFICATION ====================

@router.callback_query(F.data == "miniapp:waiting")
async def miniapp_waiting(callback: CallbackQuery):
    """Handle waiting button press."""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language', 'ar') if user else 'ar'
    await callback.answer(messages.miniapp_waiting(lang), show_alert=True)


@router.callback_query(F.data == "miniapp:continue")
async def miniapp_continue(callback: CallbackQuery, state: FSMContext):
    """Handle continue after mini app verification."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Error: User not found", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    # Check channels
    channels = await db.get_channels(active_only=True)
    if channels:
        # Verify channel membership
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
            await callback.answer()
            return
    
    # All checks passed - complete setup
    await callback.answer()
    await complete_setup(callback.message, user)


# ==================== CHANNEL VERIFICATION ====================

@router.callback_query(F.data == "check_channels")
async def check_channels(callback: CallbackQuery, state: FSMContext):
    """Check if user joined all channels."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Error: User not found", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    
    # Check channels
    channels = await db.get_channels(active_only=True)
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
        await callback.answer(messages.channel_not_joined(lang), show_alert=True)
        try:
            await callback.message.edit_text(
                messages.channel_join_prompt(lang, missing),
                reply_markup=channels_keyboard(lang, missing)
            )
        except Exception:
            pass
        return
    
    # All channels joined
    await callback.answer(messages.channel_join_success(lang))
    await complete_setup(callback.message, user)


# ==================== COMPLETE SETUP ====================

async def complete_setup(message, user: dict):
    """Complete user setup and show main menu."""
    telegram_id = user['telegram_id']
    lang = user.get('language', 'ar')
    
    # Mark setup complete
    await db.update_user_setup_complete(telegram_id)
    
    # Get welcome message
    welcome_key = f'welcome_message_{lang}'
    welcome_msg = await db.get_setting(welcome_key)
    
    # Process referral if exists
    referred_by = user.get('referred_by')
    if referred_by:
        # Create referral record
        await db.create_referral(referred_by, telegram_id)
        
        # Start referral award task
        asyncio.create_task(
            award_referral_after_delay(message.bot, referred_by, telegram_id)
        )
    
    # Show welcome and main menu
    is_admin = await db.is_admin(telegram_id)
    points = user.get('points', 0)
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


# ==================== MAIN MENU NAVIGATION ====================

@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery):
    """Show main menu."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    
    lang = user.get('language', 'ar')
    points = user.get('points', 0)
    first_name = user.get('first_name', 'User')
    is_admin = await db.is_admin(telegram_id)
    
    await callback.message.edit_text(
        messages.main_menu(lang, first_name, points),
        reply_markup=main_menu_keyboard(lang, is_admin),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == "menu:language")
async def change_language(callback: CallbackQuery, state: FSMContext):
    """Change language."""
    await state.set_state(SetupState.LANGUAGE)
    await callback.message.edit_text(
        messages.select_language(),
        reply_markup=language_keyboard()
    )
    await callback.answer()
