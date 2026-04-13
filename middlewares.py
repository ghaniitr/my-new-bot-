"""
Middleware for Telegram Store Bot.
Handles channel membership checks on every update.
"""

import asyncio
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, TelegramObject
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import channels_keyboard
import messages


class ChannelCheckMiddleware(BaseMiddleware):
    """Middleware to check channel membership on every update."""
    
    def __init__(self):
        super().__init__()
        self._channels_cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()
        self._cache_timestamp: datetime = datetime.min
    
    async def _get_cached_channels(self) -> list:
        """Get cached channels list, refresh if older than 30 seconds."""
        async with self._cache_lock:
            if (datetime.now() - self._cache_timestamp).total_seconds() > 30:
                self._channels_cache = await db.get_channels(active_only=True)
                self._cache_timestamp = datetime.now()
            return self._channels_cache
    
    async def _check_channel_membership(self, bot, user_id: int, channels: list) -> tuple:
        """
        Check if user is member of all channels.
        Returns (is_member, missing_channels)
        """
        missing = []
        
        for channel in channels:
            try:
                member = await bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=user_id
                )
                
                if member.status in ('left', 'kicked', 'banned', 'restricted'):
                    missing.append(channel)
                    
            except Exception as e:
                # Bot not in channel or channel deleted - log but don't block
                print(f"Channel check error for {channel.get('channel_id')}: {e}")
                continue
        
        return len(missing) == 0, missing
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process each update through channel check."""
        
        # Get user_id from event
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        elif isinstance(event, PreCheckoutQuery):
            # Always pass through pre-checkout queries
            return await handler(event, data)
        
        if not user_id:
            return await handler(event, data)
        
        # Get bot instance
        bot = data.get('bot')
        if not bot:
            return await handler(event, data)
        
        # Get user from database
        user = await db.get_user(user_id)
        
        # No user record yet - let start.py handle onboarding
        if not user:
            return await handler(event, data)
        
        # Check if user is banned
        if user.get('is_banned'):
            lang = user.get('language', 'ar')
            if isinstance(event, Message):
                await event.answer(messages.error_banned(lang))
            elif isinstance(event, CallbackQuery):
                await event.answer(messages.error_banned(lang), show_alert=True)
            return None
        
        # Setup not complete - let setup flow handle it
        if not user.get('setup_complete'):
            # Check if this is a setup-related callback
            if isinstance(event, CallbackQuery):
                if event.data in ('lang:ar', 'lang:en', 'check_channels', 'menu:main', 'miniapp:continue'):
                    return await handler(event, data)
            # Allow /start command
            if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                return await handler(event, data)
            # Block other interactions during setup
            return await handler(event, data)
        
        # Get active channels
        channels = await self._get_cached_channels()
        
        # No channels configured - pass through
        if not channels:
            return await handler(event, data)
        
        # Check bypass callbacks
        if isinstance(event, CallbackQuery):
            if event.data in ('check_channels', 'menu:main'):
                return await handler(event, data)
        
        # Check channel membership
        is_member, missing = await self._check_channel_membership(bot, user_id, channels)
        
        if is_member:
            return await handler(event, data)
        
        # User is not member of all channels - block and show join screen
        lang = user.get('language', 'ar')
        
        if isinstance(event, CallbackQuery):
            # Answer callback and show join screen
            await event.answer(
                messages.channel_not_joined(lang),
                show_alert=True
            )
            try:
                await event.message.edit_text(
                    messages.channel_join_prompt(lang, missing),
                    reply_markup=channels_keyboard(lang, missing),
                    parse_mode='HTML'
                )
            except Exception:
                pass
            return None
            
        elif isinstance(event, Message):
            # Send join screen
            await event.answer(
                messages.channel_join_prompt(lang, missing),
                reply_markup=channels_keyboard(lang, missing),
                parse_mode='HTML'
            )
            return None
        
        return await handler(event, data)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware to catch and handle errors gracefully."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Wrap handler in try/except."""
        try:
            return await handler(event, data)
        except Exception as e:
            # Log the error
            print(f"Error in handler: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to notify user
            try:
                bot = data.get('bot')
                user_id = None
                
                if isinstance(event, Message):
                    user_id = event.from_user.id
                elif isinstance(event, CallbackQuery):
                    user_id = event.from_user.id
                
                if bot and user_id:
                    user = await db.get_user(user_id)
                    if user:
                        lang = user.get('language', 'ar')
                        if isinstance(event, CallbackQuery):
                            await event.answer(messages.error_generic(lang), show_alert=True)
                        else:
                            await event.answer(messages.error_generic(lang))
            except Exception:
                pass
            
            # Try to notify super admin
            try:
                from config import config
                if bot:
                    await bot.send_message(
                        config.SUPER_ADMIN_ID,
                        f"❌ <b>Error occurred:</b>\n<pre>{str(e)[:500]}</pre>",
                        parse_mode='HTML'
                    )
            except Exception:
                pass
            
            return None
