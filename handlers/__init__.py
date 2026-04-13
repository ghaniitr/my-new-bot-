"""
Handlers package for Telegram Store Bot.
"""

from aiogram import Router

from .start import router as start_router
from .store import router as store_router
from .points import router as points_router
from .referral import router as referral_router
from .support import router as support_router
from .admin import router as admin_router
from .ads import router as ads_router


def get_all_routers() -> list[Router]:
    """Get all handler routers."""
    return [
        start_router,
        store_router,
        points_router,
        referral_router,
        support_router,
        admin_router,
        ads_router
    ]
