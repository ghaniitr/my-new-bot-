"""
Main entry point for Telegram Store Bot.
Initializes bot, database, and starts polling.
"""

import asyncio
import signal
import sys
import traceback

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from config import config
from database import db
from middlewares import ChannelCheckMiddleware, ErrorHandlerMiddleware
from scheduler import Scheduler
from handlers import get_all_routers

# Import miniapp server if on Railway
if config.RAILWAY_ENV:
    from miniapp_server import start_miniapp_server


async def on_startup(bot: Bot):
    """Run on bot startup."""
    print("=" * 50)
    print("🤖 Telegram Store Bot Starting...")
    print("=" * 50)
    
    # Initialize database
    await db.connect()
    print(f"✅ Database connected ({config.DB_TYPE})")
    
    # Notify super admin
    try:
        await bot.send_message(
            config.SUPER_ADMIN_ID,
            "🤖 <b>Bot Started</b>\n\n"
            f"Database: {config.DB_TYPE}\n"
            f"Environment: {'Railway' if config.RAILWAY_ENV else 'Local/VPS'}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"⚠️ Could not notify super admin: {e}")
    
    print("✅ Bot is ready!")
    print("=" * 50)


async def on_shutdown(bot: Bot):
    """Run on bot shutdown."""
    print("\n" + "=" * 50)
    print("🛑 Shutting down...")
    print("=" * 50)
    
    # Close database
    await db.close()
    print("✅ Database disconnected")
    
    # Notify super admin
    try:
        await bot.send_message(
            config.SUPER_ADMIN_ID,
            "🛑 <b>Bot Stopped</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    
    print("✅ Shutdown complete")
    print("=" * 50)


async def main():
    """Main function."""
    # Validate config
    try:
        from config import load_config
        load_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Initialize bot
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Get bot info
    try:
        bot_info = await bot.get_me()
        print(f"Bot: @{bot_info.username}")
    except Exception as e:
        print(f"❌ Failed to get bot info: {e}")
        print("Check your BOT_TOKEN!")
        sys.exit(1)
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # Register middlewares
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    dp.message.middleware(ChannelCheckMiddleware())
    dp.callback_query.middleware(ChannelCheckMiddleware())
    
    # Register handlers
    for router in get_all_routers():
        dp.include_router(router)
    
    # Startup and shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Initialize scheduler
    scheduler = Scheduler(bot)
    
    # Start miniapp server if on Railway
    miniapp_runner = None
    if config.RAILWAY_ENV:
        try:
            miniapp_runner = await start_miniapp_server()
            print(f"✅ Mini app server started on port {config.MINIAPP_PORT}")
        except Exception as e:
            print(f"⚠️ Failed to start mini app server: {e}")
    
    # Start scheduler
    await scheduler.start()
    print("✅ Scheduler started")
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\n⚠️ Interrupt received, stopping...")
        raise asyncio.CancelledError()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start polling
        print("🚀 Starting polling...")
        await dp.start_polling(
            bot,
            allowed_updates=[
                'message',
                'callback_query',
                'pre_checkout_query',
                'successful_payment',
                'my_chat_member'
            ]
        )
    except asyncio.CancelledError:
        pass
    finally:
        # Stop scheduler
        await scheduler.stop()
        
        # Stop miniapp server if running
        if miniapp_runner:
            await miniapp_runner.cleanup()
        
        # Shutdown
        await on_shutdown(bot)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
