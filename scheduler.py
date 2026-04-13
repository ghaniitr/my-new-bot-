"""
Scheduler module for Telegram Store Bot.
Handles background tasks like penalty checking.
"""

import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from database import db
from config import config
import messages


class Scheduler:
    """Background task scheduler."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self._running = False
        self._tasks = []
    
    async def start(self):
        """Start all background tasks."""
        self._running = True
        self._tasks = [
            asyncio.create_task(self._penalty_checker()),
            asyncio.create_task(self._cleanup_task()),
            asyncio.create_task(self._star_order_auto_cancel())
        ]
    
    async def stop(self):
        """Stop all background tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
    
    async def _penalty_checker(self):
        """Check referrals for penalties every 10 minutes."""
        while self._running:
            try:
                await self._check_penalties()
            except Exception as e:
                print(f"Penalty checker error: {e}")
            
            # Wait 10 minutes
            await asyncio.sleep(600)
    
    async def _check_penalties(self):
        """Check and process penalties."""
        # Check if penalty mode is enabled
        penalty_mode = await db.get_setting('penalty_mode', 'false')
        if penalty_mode.lower() != 'true':
            return
        
        # Get all active and penalized referrals
        all_referrals = await db.fetchall(
            "SELECT * FROM referrals WHERE status IN ('active', 'penalized')"
        )
        
        # Get active channels
        channels = await db.get_channels(active_only=True)
        
        for referral in all_referrals:
            try:
                await self._process_referral_penalty(referral, channels)
            except Exception as e:
                print(f"Error processing referral {referral['id']}: {e}")
    
    async def _process_referral_penalty(self, referral: dict, channels: list):
        """Process penalty for a single referral."""
        referred_id = referral['referred_id']
        referrer_id = referral['referrer_id']
        status = referral['status']
        points_awarded = referral.get('points_awarded', 0)
        
        # Get referred user
        referred_user = await db.get_user(referred_id)
        if not referred_user:
            return
        
        # Check if referred user is in all channels
        in_all_channels = True
        for channel in channels:
            try:
                member = await self.bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=referred_id
                )
                if member.status in ('left', 'kicked', 'banned', 'restricted'):
                    in_all_channels = False
                    break
            except Exception:
                continue
        
        # Get referrer for notification
        referrer = await db.get_user(referrer_id)
        if not referrer:
            return
        
        referrer_lang = referrer.get('language', 'ar')
        referred_name = referred_user.get('first_name') or referred_user.get('username') or f"User {referred_id}"
        
        # Handle penalty
        if status == 'active' and not in_all_channels:
            # Penalize: user left channel
            await db.penalize_referral(referral['id'])
            
            # Deduct points from referrer
            if points_awarded > 0:
                await db.remove_points(referrer_id, points_awarded)
            
            # Notify referrer
            try:
                await self.bot.send_message(
                    referrer_id,
                    messages.referral_penalty(referrer_lang, points_awarded, referred_name),
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Failed to notify referrer {referrer_id}: {e}")
                
        elif status == 'penalized' and in_all_channels:
            # Restore: user rejoined
            await db.restore_referral(referral['id'])
            
            # Restore points to referrer
            if points_awarded > 0:
                await db.add_points(referrer_id, points_awarded)
            
            # Notify referrer
            try:
                await self.bot.send_message(
                    referrer_id,
                    messages.referral_restore(referrer_lang, points_awarded, referred_name),
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Failed to notify referrer {referrer_id}: {e}")
    
    async def _cleanup_task(self):
        """Periodic cleanup task."""
        while self._running:
            try:
                # Clean up old miniapp polling tasks if any
                # (This would be implemented if we stored polling tasks)
                pass
            except Exception as e:
                print(f"Cleanup error: {e}")

            # Wait 5 minutes
            await asyncio.sleep(300)

    async def _star_order_auto_cancel(self):
        """Auto-cancel expired star orders every 15 minutes."""
        while self._running:
            try:
                await self._process_expired_star_orders()
            except Exception as e:
                print(f"Star order auto-cancel error: {e}")

            # Wait 15 minutes
            await asyncio.sleep(900)

    async def _process_expired_star_orders(self):
        """Process and cancel expired star orders."""
        from database import db

        expired_orders = await db.get_expired_star_orders()

        for order in expired_orders:
            try:
                user_id = order['user_id']
                points_cost = order['points_cost']
                order_id = order['order_id']

                # Refund points
                await db.add_points(user_id, points_cost)

                # Update order status
                await db.update_star_order_status(
                    order_id,
                    'cancelled',
                    cancelled_at=datetime.utcnow().isoformat()
                )

                # Notify user
                try:
                    user = await db.get_user(user_id)
                    lang = user.get('language', 'ar') if user else 'ar'
                    await self.bot.send_message(
                        user_id,
                        messages.star_order_auto_cancelled(lang, order_id, points_cost),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Failed to notify user {user_id} about auto-cancel: {e}")

                # Notify admins
                admins = await db.get_admins()
                admin_ids = [admin['telegram_id'] for admin in admins]
                from config import config
                admin_ids.append(config.SUPER_ADMIN_ID)

                for admin_id in set(admin_ids):
                    try:
                        await self.bot.send_message(
                            admin_id,
                            f"⏰ <b>Star Order Auto-Cancelled</b>\n\n"
                            f"🆔 Order: #{order_id}\n"
                            f"👤 User: <code>{user_id}</code>\n"
                            f"💰 {points_cost} points refunded",
                            parse_mode='HTML'
                        )
                    except Exception:
                        pass

            except Exception as e:
                print(f"Error processing expired order {order.get('order_id')}: {e}")


async def award_referral_after_delay(bot: Bot, referrer_id: int, referred_id: int):
    """
    Award referral points after delay.
    This is called as an async task when a new user completes setup.
    """
    try:
        # Wait for referral delay
        await asyncio.sleep(config.REFERRAL_DELAY_SECONDS)
        
        # Get referral record
        referral = await db.get_referral(referred_id)
        if not referral:
            return
        
        # Check if already processed
        if referral['status'] != 'pending':
            return
        
        # Get referred user
        referred_user = await db.get_user(referred_id)
        if not referred_user:
            return
        
        # Check all conditions
        # 1. Setup complete
        if not referred_user.get('setup_complete'):
            return
        
        # 2. Not flagged
        if referred_user.get('miniapp_flagged'):
            return
        
        # 3. Still in all channels
        channels = await db.get_channels(active_only=True)
        for channel in channels:
            try:
                member = await bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=referred_id
                )
                if member.status in ('left', 'kicked', 'banned', 'restricted'):
                    return
            except Exception:
                continue
        
        # All checks passed - award points
        referral_points = int(await db.get_setting('referral_points', '1'))
        
        # Activate referral
        await db.activate_referral(referral['id'], referral_points)
        
        # Add points to referrer
        await db.add_points(referrer_id, referral_points)
        
        # Notify referrer
        referrer = await db.get_user(referrer_id)
        if referrer:
            referrer_lang = referrer.get('language', 'ar')
            referred_name = referred_user.get('first_name') or referred_user.get('username') or f"User {referred_id}"
            try:
                await bot.send_message(
                    referrer_id,
                    messages.referral_awarded_notification(referrer_lang, referral_points, referred_name),
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Failed to notify referrer {referrer_id}: {e}")
                
    except Exception as e:
        print(f"Error in award_referral_after_delay: {e}")
