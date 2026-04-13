"""
Database module for Telegram Store Bot.
Supports both SQLite (aiosqlite) and MySQL (aiomysql).
"""

import json
import random
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager

from config import config

# Database driver imports
try:
    import aiosqlite
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

try:
    import aiomysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


class Database:
    """Database abstraction layer supporting SQLite and MySQL."""
    
    def __init__(self):
        self.db_type = config.DB_TYPE
        self.pool = None
        self._sqlite_conn = None
        
        if self.db_type == 'sqlite' and not HAS_SQLITE:
            raise RuntimeError("aiosqlite is required for SQLite support. Install: pip install aiosqlite")
        if self.db_type == 'mysql' and not HAS_MYSQL:
            raise RuntimeError("aiomysql is required for MySQL support. Install: pip install aiomysql")
    
    async def connect(self):
        """Initialize database connection."""
        if self.db_type == 'sqlite':
            self._sqlite_conn = await aiosqlite.connect(config.DB_PATH)
            self._sqlite_conn.row_factory = aiosqlite.Row
            await self._init_sqlite()
        else:
            self.pool = await aiomysql.create_pool(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                db=config.MYSQL_DATABASE,
                autocommit=True,
                minsize=1,
                maxsize=10
            )
    
    async def close(self):
        """Close database connection."""
        if self.db_type == 'sqlite':
            if self._sqlite_conn:
                await self._sqlite_conn.close()
        else:
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
    
    async def _init_sqlite(self):
        """Initialize SQLite database with schema."""
        async with self._sqlite_conn.cursor() as cursor:
            # Users table (no phone verification)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'ar',
                    points INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned INTEGER DEFAULT 0,
                    setup_complete INTEGER DEFAULT 0,
                    miniapp_verified INTEGER DEFAULT 0,
                    miniapp_flagged INTEGER DEFAULT 0,
                    ip_address TEXT,
                    device_fingerprint TEXT
                )
            ''')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by)')
            
            # Admins table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ar TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Products table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name_ar TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    description_ar TEXT,
                    description_en TEXT,
                    delivery_type TEXT NOT NULL DEFAULT 'oncesell_text',
                    points_price INTEGER NOT NULL,
                    stock INTEGER DEFAULT 0,
                    is_visible INTEGER DEFAULT 1,
                    file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')
            
            # Product stock table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_sold INTEGER DEFAULT 0,
                    sold_to INTEGER,
                    sold_at TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')
            
            # Orders table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    payment_method TEXT DEFAULT 'points',
                    amount INTEGER NOT NULL,
                    order_id TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'completed',
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Channels table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT,
                    channel_url TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Coupons table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    points_value INTEGER NOT NULL,
                    max_uses INTEGER DEFAULT 1,
                    used_count INTEGER DEFAULT 0,
                    expires_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER
                )
            ''')
            
            # Coupon uses table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupon_uses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coupon_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(coupon_id, user_id)
                )
            ''')
            
            # Referrals table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER UNIQUE NOT NULL,
                    points_awarded INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP
                )
            ''')
            
            # Waiting list table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS waiting_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    notified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, product_id)
                )
            ''')
            
            # Support tickets table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    admin_reply TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    replied_at TIMESTAMP
                )
            ''')
            
            # Daily bonus table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_bonus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    last_claimed TIMESTAMP,
                    streak INTEGER DEFAULT 0
                )
            ''')
            
            # Stars packages table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS stars_packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stars_amount INTEGER NOT NULL,
                    points_amount INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Settings table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Broadcasts table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    photo_id TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_by INTEGER,
                    total INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0
                )
            ''')
            
            # Mini app sessions table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS miniapp_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    ip_address TEXT,
                    fingerprint TEXT,
                    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_duplicate INTEGER DEFAULT 0
                )
            ''')

            # Star orders table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS star_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stars_amount INTEGER NOT NULL,
                    points_cost INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    order_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    admin_id INTEGER
                )
            ''')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_star_orders_user_id ON star_orders(user_id)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_star_orders_status ON star_orders(status)')

            # Ad tasks table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS ad_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    points_reward INTEGER NOT NULL,
                    is_once_per_user INTEGER DEFAULT 1,
                    cooldown_hours INTEGER DEFAULT 24,
                    is_active INTEGER DEFAULT 1,
                    total_claims INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Ad claims table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS ad_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ad_id INTEGER NOT NULL,
                    screenshot_file_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    reject_reason TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by INTEGER
                )
            ''')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_ad_claims_user_id ON ad_claims(user_id)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_ad_claims_status ON ad_claims(status)')

            await self._sqlite_conn.commit()
        
        # Insert default settings
        await self._insert_default_settings()
        # Insert default stars packages
        await self._insert_default_stars_packages()
        # Run column migrations
        await self._add_missing_columns()
    
    async def _insert_default_settings(self):
        """Insert default settings if not exists."""
        defaults = {
            'referral_points': '1',
            'daily_bonus_points': '10',
            'penalty_mode': 'false',
            'welcome_message_ar': 'مرحباً بك في المتجر! 🎉',
            'welcome_message_en': 'Welcome to the store! 🎉',
            'stars_per_point': '4',
            'stars_withdrawal_open': 'true',
            'low_stock_threshold': '5'
        }
        for key, value in defaults.items():
            await self.execute(
                "INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES (?, ?)",
                (key, value)
            )
    
    async def _insert_default_stars_packages(self):
        """Insert default stars packages if not exists."""
        packages = [
            (1, 100, 1),
            (5, 550, 1),
            (10, 1200, 1),
            (25, 3250, 1),
            (50, 7000, 1)
        ]
        for stars, points, active in packages:
            await self.execute(
                """INSERT OR IGNORE INTO stars_packages (stars_amount, points_amount, is_active)
                   VALUES (?, ?, ?)""",
                (stars, points, active)
            )

    async def _add_missing_columns(self):
        """Add missing columns for backward compatibility."""
        # Add is_restricted to users
        try:
            await self.execute(
                "ALTER TABLE users ADD COLUMN is_restricted INTEGER DEFAULT 0"
            )
        except Exception:
            pass  # Column already exists

        # Add admin_notes to users
        try:
            await self.execute(
                "ALTER TABLE users ADD COLUMN admin_notes TEXT"
            )
        except Exception:
            pass  # Column already exists
    
    @asynccontextmanager
    async def _get_cursor(self):
        """Get database cursor context manager."""
        if self.db_type == 'sqlite':
            async with self._sqlite_conn.cursor() as cursor:
                yield cursor
            await self._sqlite_conn.commit()
        else:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    yield cursor
                await conn.commit()
    
    async def execute(self, query: str, params: tuple = ()):
        """Execute a query."""
        # Convert ? to %s for MySQL
        if self.db_type == 'mysql':
            query = query.replace('?', '%s')
        
        async with self._get_cursor() as cursor:
            await cursor.execute(query, params)
            if self.db_type == 'sqlite':
                return cursor.lastrowid
            else:
                return cursor.lastrowid
    
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        if self.db_type == 'mysql':
            query = query.replace('?', '%s')
        
        async with self._get_cursor() as cursor:
            await cursor.execute(query, params)
            row = await cursor.fetchone()
            if row is None:
                return None
            
            if self.db_type == 'sqlite':
                return dict(row)
            else:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
    
    async def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        if self.db_type == 'mysql':
            query = query.replace('?', '%s')
        
        async with self._get_cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            
            if not rows:
                return []
            
            if self.db_type == 'sqlite':
                return [dict(row) for row in rows]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    # ==================== USER METHODS ====================
    
    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID."""
        return await self.fetchone(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
    
    async def create_user(self, telegram_id: int, username: str, first_name: str, 
                          language: str = 'ar', referred_by: Optional[int] = None) -> Dict[str, Any]:
        """Create a new user."""
        # Generate unique referral code
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        await self.execute(
            """INSERT INTO users (telegram_id, username, first_name, language, 
                referral_code, referred_by) VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, language, referral_code, referred_by)
        )
        return await self.get_user(telegram_id)
    
    async def update_user_language(self, telegram_id: int, language: str):
        """Update user language preference."""
        await self.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id)
        )
    
    async def update_user_setup_complete(self, telegram_id: int):
        """Mark user setup as complete."""
        await self.execute(
            "UPDATE users SET setup_complete = 1 WHERE telegram_id = ?",
            (telegram_id,)
        )
    
    async def update_miniapp_verified(self, telegram_id: int, verified: bool = True, 
                                       flagged: bool = False, ip: str = None, 
                                       fingerprint: str = None):
        """Update mini app verification status."""
        await self.execute(
            """UPDATE users SET miniapp_verified = ?, miniapp_flagged = ?, 
                ip_address = ?, device_fingerprint = ? WHERE telegram_id = ?""",
            (1 if verified else 0, 1 if flagged else 0, ip, fingerprint, telegram_id)
        )
    
    async def add_points(self, telegram_id: int, points: int) -> int:
        """Add points to user balance. Returns new balance."""
        await self.execute(
            """UPDATE users SET points = points + ?, total_earned = total_earned + ? 
               WHERE telegram_id = ?""",
            (points, points, telegram_id)
        )
        user = await self.get_user(telegram_id)
        return user['points'] if user else 0
    
    async def remove_points(self, telegram_id: int, points: int) -> int:
        """Remove points from user balance. Returns new balance."""
        await self.execute(
            """UPDATE users SET points = MAX(0, points - ?), total_spent = total_spent + ? 
               WHERE telegram_id = ?""",
            (points, points, telegram_id)
        )
        user = await self.get_user(telegram_id)
        return user['points'] if user else 0
    
    async def ban_user(self, telegram_id: int, banned: bool = True):
        """Ban or unban a user."""
        await self.execute(
            "UPDATE users SET is_banned = ? WHERE telegram_id = ?",
            (1 if banned else 0, telegram_id)
        )
    
    async def get_all_users(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users."""
        query = "SELECT * FROM users ORDER BY joined_at DESC"
        if limit:
            if self.db_type == 'sqlite':
                query += f" LIMIT {limit} OFFSET {offset}"
            else:
                query += " LIMIT %s OFFSET %s"
                return await self.fetchall(query, (limit, offset))
        return await self.fetchall(query)
    
    async def search_users(self, search_term: str) -> List[Dict[str, Any]]:
        """Search users by ID or username."""
        if search_term.isdigit():
            return await self.fetchall(
                "SELECT * FROM users WHERE telegram_id = ? OR username LIKE ?",
                (int(search_term), f"%{search_term}%")
            )
        return await self.fetchall(
            "SELECT * FROM users WHERE username LIKE ?",
            (f"%{search_term}%",)
        )
    
    # ==================== ADMIN METHODS ====================
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin."""
        if telegram_id == config.SUPER_ADMIN_ID:
            return True
        result = await self.fetchone(
            "SELECT 1 FROM admins WHERE telegram_id = ?",
            (telegram_id,)
        )
        return result is not None
    
    async def add_admin(self, telegram_id: int, added_by: int):
        """Add a new admin."""
        await self.execute(
            "INSERT OR IGNORE INTO admins (telegram_id, added_by) VALUES (?, ?)",
            (telegram_id, added_by)
        )
    
    async def remove_admin(self, telegram_id: int):
        """Remove an admin."""
        await self.execute(
            "DELETE FROM admins WHERE telegram_id = ?",
            (telegram_id,)
        )
    
    async def get_admins(self) -> List[Dict[str, Any]]:
        """Get all admins."""
        return await self.fetchall("SELECT * FROM admins")
    
    # ==================== CATEGORY METHODS ====================
    
    async def get_categories(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all categories."""
        if active_only:
            return await self.fetchall(
                "SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id"
            )
        return await self.fetchall("SELECT * FROM categories ORDER BY sort_order, id")
    
    async def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID."""
        return await self.fetchone(
            "SELECT * FROM categories WHERE id = ?",
            (category_id,)
        )
    
    async def create_category(self, name_ar: str, name_en: str, sort_order: int = 0) -> int:
        """Create a new category. Returns category ID."""
        return await self.execute(
            "INSERT INTO categories (name_ar, name_en, sort_order) VALUES (?, ?, ?)",
            (name_ar, name_en, sort_order)
        )
    
    async def update_category(self, category_id: int, **kwargs):
        """Update category fields."""
        allowed = ['name_ar', 'name_en', 'is_active', 'sort_order']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if updates:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [category_id]
            await self.execute(
                f"UPDATE categories SET {set_clause} WHERE id = ?",
                tuple(values)
            )
    
    async def delete_category(self, category_id: int):
        """Delete a category."""
        await self.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    
    # ==================== PRODUCT METHODS ====================
    
    async def get_products(self, category_id: int = None, visible_only: bool = True) -> List[Dict[str, Any]]:
        """Get products."""
        if category_id:
            if visible_only:
                return await self.fetchall(
                    "SELECT * FROM products WHERE category_id = ? AND is_visible = 1 ORDER BY id",
                    (category_id,)
                )
            return await self.fetchall(
                "SELECT * FROM products WHERE category_id = ? ORDER BY id",
                (category_id,)
            )
        if visible_only:
            return await self.fetchall(
                "SELECT * FROM products WHERE is_visible = 1 ORDER BY id"
            )
        return await self.fetchall("SELECT * FROM products ORDER BY id")
    
    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        return await self.fetchone(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
    
    async def create_product(self, category_id: int, name_ar: str, name_en: str,
                            description_ar: str, description_en: str, delivery_type: str,
                            points_price: int, file_id: str = None) -> int:
        """Create a new product. Returns product ID."""
        stock = 999 if delivery_type == 'unlimited_file' else 0
        return await self.execute(
            """INSERT INTO products (category_id, name_ar, name_en, description_ar,
                description_en, delivery_type, points_price, stock, file_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (category_id, name_ar, name_en, description_ar, description_en,
             delivery_type, points_price, stock, file_id)
        )
    
    async def update_product(self, product_id: int, **kwargs):
        """Update product fields."""
        allowed = ['name_ar', 'name_en', 'description_ar', 'description_en',
                   'points_price', 'stock', 'is_visible', 'file_id', 'delivery_type']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if updates:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [product_id]
            await self.execute(
                f"UPDATE products SET {set_clause} WHERE id = ?",
                tuple(values)
            )
    
    async def delete_product(self, product_id: int):
        """Delete a product."""
        await self.execute("DELETE FROM products WHERE id = ?", (product_id,))
    
    async def add_stock(self, product_id: int, items: List[str]) -> int:
        """Add stock items to a product. Returns number of items added."""
        count = 0
        for item in items:
            item = item.strip()
            if item:
                await self.execute(
                    "INSERT INTO product_stock (product_id, content) VALUES (?, ?)",
                    (product_id, item)
                )
                count += 1
        
        # Update stock count
        await self.execute(
            """UPDATE products SET stock = (SELECT COUNT(*) FROM product_stock 
               WHERE product_id = ? AND is_sold = 0) WHERE id = ?""",
            (product_id, product_id)
        )
        return count
    
    async def get_available_stock(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get one available stock item for a product."""
        return await self.fetchone(
            "SELECT * FROM product_stock WHERE product_id = ? AND is_sold = 0 LIMIT 1",
            (product_id,)
        )
    
    async def mark_stock_sold(self, stock_id: int, user_id: int):
        """Mark stock item as sold."""
        await self.execute(
            """UPDATE product_stock SET is_sold = 1, sold_to = ?, sold_at = ? 
               WHERE id = ?""",
            (user_id, datetime.utcnow().isoformat(), stock_id)
        )
    
    # ==================== ORDER METHODS ====================
    
    async def create_order(self, user_id: int, product_id: int, amount: int, 
                          content: str, payment_method: str = 'points') -> str:
        """Create a new order. Returns order ID."""
        order_id = f"ORD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        await self.execute(
            """INSERT INTO orders (user_id, product_id, payment_method, amount, 
                order_id, content) VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, product_id, payment_method, amount, order_id, content)
        )
        return order_id
    
    async def get_user_orders(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's orders."""
        query = """SELECT o.*, p.name_ar, p.name_en FROM orders o 
                   JOIN products p ON o.product_id = p.id 
                   WHERE o.user_id = ? ORDER BY o.created_at DESC"""
        if self.db_type == 'sqlite':
            query += f" LIMIT {limit}"
            return await self.fetchall(query, (user_id,))
        else:
            query += " LIMIT %s"
            return await self.fetchall(query, (user_id, limit))
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by order ID."""
        return await self.fetchone(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,)
        )
    
    # ==================== CHANNEL METHODS ====================
    
    async def get_channels(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all channels."""
        if active_only:
            return await self.fetchall(
                "SELECT * FROM channels WHERE is_active = 1"
            )
        return await self.fetchall("SELECT * FROM channels")
    
    async def add_channel(self, channel_id: str, channel_name: str, channel_url: str):
        """Add a new channel."""
        await self.execute(
            """INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_url) 
               VALUES (?, ?, ?)""",
            (channel_id, channel_name, channel_url)
        )
    
    async def remove_channel(self, channel_id: str):
        """Remove a channel."""
        await self.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    
    async def toggle_channel(self, channel_id: str):
        """Toggle channel active status."""
        await self.execute(
            "UPDATE channels SET is_active = 1 - is_active WHERE channel_id = ?",
            (channel_id,)
        )
    
    # ==================== COUPON METHODS ====================
    
    async def get_coupon(self, code: str) -> Optional[Dict[str, Any]]:
        """Get coupon by code (case-insensitive)."""
        if self.db_type == 'sqlite':
            return await self.fetchone(
                "SELECT * FROM coupons WHERE UPPER(code) = UPPER(?)",
                (code,)
            )
        return await self.fetchone(
            "SELECT * FROM coupons WHERE UPPER(code) = UPPER(?)",
            (code,)
        )
    
    async def get_coupons(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all coupons."""
        if self.db_type == 'sqlite':
            return await self.fetchall(
                f"SELECT * FROM coupons ORDER BY created_at DESC LIMIT {limit}"
            )
        return await self.fetchall(
            "SELECT * FROM coupons ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
    
    async def create_coupon(self, code: str, points_value: int, max_uses: int = 1,
                           expires_at: str = None, created_by: int = None):
        """Create a new coupon."""
        code = code.upper()
        await self.execute(
            """INSERT INTO coupons (code, points_value, max_uses, expires_at, created_by) 
               VALUES (?, ?, ?, ?, ?)""",
            (code, points_value, max_uses, expires_at, created_by)
        )
    
    async def use_coupon(self, coupon_id: int, user_id: int) -> bool:
        """Record coupon use. Returns True if successful."""
        try:
            await self.execute(
                "INSERT INTO coupon_uses (coupon_id, user_id) VALUES (?, ?)",
                (coupon_id, user_id)
            )
            await self.execute(
                "UPDATE coupons SET used_count = used_count + 1 WHERE id = ?",
                (coupon_id,)
            )
            return True
        except Exception:
            return False
    
    async def has_used_coupon(self, coupon_id: int, user_id: int) -> bool:
        """Check if user has already used this coupon."""
        result = await self.fetchone(
            "SELECT 1 FROM coupon_uses WHERE coupon_id = ? AND user_id = ?",
            (coupon_id, user_id)
        )
        return result is not None
    
    async def toggle_coupon(self, coupon_id: int):
        """Toggle coupon active status."""
        await self.execute(
            "UPDATE coupons SET is_active = 1 - is_active WHERE id = ?",
            (coupon_id,)
        )
    
    async def delete_coupon(self, coupon_id: int):
        """Delete a coupon."""
        await self.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,))
    
    # ==================== REFERRAL METHODS ====================
    
    async def create_referral(self, referrer_id: int, referred_id: int):
        """Create a new referral record."""
        await self.execute(
            "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, referred_id)
        )
    
    async def get_referral(self, referred_id: int) -> Optional[Dict[str, Any]]:
        """Get referral by referred ID."""
        return await self.fetchone(
            "SELECT * FROM referrals WHERE referred_id = ?",
            (referred_id,)
        )
    
    async def get_user_referrals(self, referrer_id: int) -> List[Dict[str, Any]]:
        """Get all referrals by a user."""
        return await self.fetchall(
            "SELECT * FROM referrals WHERE referrer_id = ?",
            (referrer_id,)
        )
    
    async def activate_referral(self, referral_id: int, points: int):
        """Activate a referral and award points."""
        await self.execute(
            """UPDATE referrals SET status = 'active', points_awarded = ?, 
                verified_at = ? WHERE id = ?""",
            (points, datetime.utcnow().isoformat(), referral_id)
        )
    
    async def penalize_referral(self, referral_id: int):
        """Penalize a referral."""
        await self.execute(
            "UPDATE referrals SET status = 'penalized' WHERE id = ?",
            (referral_id,)
        )
    
    async def restore_referral(self, referral_id: int):
        """Restore a penalized referral."""
        await self.execute(
            "UPDATE referrals SET status = 'active' WHERE id = ?",
            (referral_id,)
        )
    
    async def get_active_referrals_count(self, referrer_id: int) -> int:
        """Get count of active referrals."""
        result = await self.fetchone(
            """SELECT COUNT(*) as count FROM referrals 
               WHERE referrer_id = ? AND status = 'active'""",
            (referrer_id,)
        )
        return result['count'] if result else 0
    
    async def get_referrals_earned(self, referrer_id: int) -> int:
        """Get total points earned from referrals."""
        result = await self.fetchone(
            """SELECT SUM(points_awarded) as total FROM referrals 
               WHERE referrer_id = ? AND status = 'active'""",
            (referrer_id,)
        )
        return result['total'] or 0
    
    # ==================== WAITING LIST METHODS ====================
    
    async def add_to_waiting_list(self, user_id: int, product_id: int):
        """Add user to waiting list for a product."""
        try:
            await self.execute(
                "INSERT OR IGNORE INTO waiting_list (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id)
            )
            return True
        except Exception:
            return False
    
    async def is_on_waiting_list(self, user_id: int, product_id: int) -> bool:
        """Check if user is on waiting list."""
        result = await self.fetchone(
            "SELECT 1 FROM waiting_list WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        return result is not None
    
    async def get_waiting_list(self, product_id: int) -> List[Dict[str, Any]]:
        """Get waiting list for a product."""
        return await self.fetchall(
            """SELECT * FROM waiting_list WHERE product_id = ? AND notified = 0""",
            (product_id,)
        )
    
    async def mark_notified(self, waiting_id: int):
        """Mark waiting list entry as notified."""
        await self.execute(
            "UPDATE waiting_list SET notified = 1 WHERE id = ?",
            (waiting_id,)
        )
    
    # ==================== SUPPORT TICKET METHODS ====================
    
    async def create_ticket(self, user_id: int, message: str) -> int:
        """Create a new support ticket. Returns ticket ID."""
        return await self.execute(
            "INSERT INTO support_tickets (user_id, message) VALUES (?, ?)",
            (user_id, message)
        )
    
    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by ID."""
        return await self.fetchone(
            "SELECT * FROM support_tickets WHERE id = ?",
            (ticket_id,)
        )
    
    async def get_open_tickets(self) -> List[Dict[str, Any]]:
        """Get all open tickets."""
        return await self.fetchall(
            """SELECT * FROM support_tickets WHERE status = 'open' 
               ORDER BY created_at DESC"""
        )
    
    async def reply_ticket(self, ticket_id: int, reply: str):
        """Reply to a ticket."""
        await self.execute(
            """UPDATE support_tickets SET admin_reply = ?, status = 'replied', 
                replied_at = ? WHERE id = ?""",
            (reply, datetime.utcnow().isoformat(), ticket_id)
        )
    
    async def close_ticket(self, ticket_id: int):
        """Close a ticket."""
        await self.execute(
            "UPDATE support_tickets SET status = 'closed' WHERE id = ?",
            (ticket_id,)
        )
    
    # ==================== DAILY BONUS METHODS ====================
    
    async def get_daily_bonus(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's daily bonus record."""
        return await self.fetchone(
            "SELECT * FROM daily_bonus WHERE user_id = ?",
            (user_id,)
        )
    
    async def can_claim_daily_bonus(self, user_id: int) -> bool:
        """Check if user can claim daily bonus."""
        record = await self.get_daily_bonus(user_id)
        if not record or not record['last_claimed']:
            return True
        
        last_claimed = datetime.fromisoformat(record['last_claimed'])
        return datetime.utcnow() - last_claimed >= timedelta(hours=24)
    
    async def claim_daily_bonus(self, user_id: int) -> int:
        """Claim daily bonus. Returns new streak."""
        record = await self.get_daily_bonus(user_id)
        
        if record:
            last_claimed = datetime.fromisoformat(record['last_claimed']) if record['last_claimed'] else None
            streak = record['streak']
            
            # Check if streak continues (within 48 hours)
            if last_claimed and datetime.utcnow() - last_claimed < timedelta(hours=48):
                streak += 1
            else:
                streak = 1
            
            await self.execute(
                """UPDATE daily_bonus SET last_claimed = ?, streak = ? 
                   WHERE user_id = ?""",
                (datetime.utcnow().isoformat(), streak, user_id)
            )
            return streak
        else:
            await self.execute(
                "INSERT INTO daily_bonus (user_id, last_claimed, streak) VALUES (?, ?, 1)",
                (user_id, datetime.utcnow().isoformat())
            )
            return 1
    
    async def get_bonus_time_remaining(self, user_id: int) -> int:
        """Get seconds remaining until next bonus claim."""
        record = await self.get_daily_bonus(user_id)
        if not record or not record['last_claimed']:
            return 0
        
        last_claimed = datetime.fromisoformat(record['last_claimed'])
        next_claim = last_claimed + timedelta(hours=24)
        remaining = (next_claim - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    # ==================== STARS PACKAGES METHODS ====================
    
    async def get_stars_packages(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all stars packages."""
        if active_only:
            return await self.fetchall(
                "SELECT * FROM stars_packages WHERE is_active = 1 ORDER BY stars_amount"
            )
        return await self.fetchall("SELECT * FROM stars_packages ORDER BY stars_amount")
    
    async def get_stars_package(self, package_id: int) -> Optional[Dict[str, Any]]:
        """Get stars package by ID."""
        return await self.fetchone(
            "SELECT * FROM stars_packages WHERE id = ?",
            (package_id,)
        )
    
    async def create_stars_package(self, stars_amount: int, points_amount: int):
        """Create a new stars package."""
        await self.execute(
            "INSERT INTO stars_packages (stars_amount, points_amount) VALUES (?, ?)",
            (stars_amount, points_amount)
        )
    
    async def toggle_stars_package(self, package_id: int):
        """Toggle stars package active status."""
        await self.execute(
            "UPDATE stars_packages SET is_active = 1 - is_active WHERE id = ?",
            (package_id,)
        )
    
    async def delete_stars_package(self, package_id: int):
        """Delete a stars package."""
        await self.execute("DELETE FROM stars_packages WHERE id = ?", (package_id,))
    
    # ==================== SETTINGS METHODS ====================
    
    async def get_setting(self, key: str, default: str = None) -> str:
        """Get setting value."""
        result = await self.fetchone(
            "SELECT setting_value FROM settings WHERE setting_key = ?",
            (key,)
        )
        return result['setting_value'] if result else default
    
    async def set_setting(self, key: str, value: str):
        """Set setting value."""
        await self.execute(
            """INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)
               ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value"""
            if self.db_type == 'sqlite' else
            """INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)
               ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)""",
            (key, value)
        )
    
    # ==================== BROADCAST METHODS ====================
    
    async def create_broadcast(self, message: str, photo_id: str, sent_by: int) -> int:
        """Create a broadcast record."""
        return await self.execute(
            "INSERT INTO broadcasts (message, photo_id, sent_by) VALUES (?, ?, ?)",
            (message, photo_id, sent_by)
        )
    
    async def update_broadcast_stats(self, broadcast_id: int, total: int, success: int, failed: int):
        """Update broadcast statistics."""
        await self.execute(
            "UPDATE broadcasts SET total = ?, success = ?, failed = ? WHERE id = ?",
            (total, success, failed, broadcast_id)
        )
    
    # ==================== MINI APP SESSIONS METHODS ====================
    
    async def create_miniapp_session(self, telegram_id: int, ip_address: str, 
                                     fingerprint: str, is_duplicate: bool = False):
        """Create a mini app session record."""
        await self.execute(
            """INSERT INTO miniapp_sessions (telegram_id, ip_address, fingerprint, is_duplicate) 
               VALUES (?, ?, ?, ?)""",
            (telegram_id, ip_address, fingerprint, 1 if is_duplicate else 0)
        )
    
    async def check_duplicate_fingerprint(self, telegram_id: int, fingerprint: str) -> bool:
        """Check if fingerprint exists for different user."""
        result = await self.fetchone(
            """SELECT 1 FROM miniapp_sessions WHERE fingerprint = ? AND telegram_id != ?""",
            (fingerprint, telegram_id)
        )
        return result is not None
    
    async def check_suspicious_ip(self, telegram_id: int, ip_address: str, threshold: int = 3) -> bool:
        """Check if IP has been used by multiple users."""
        result = await self.fetchone(
            """SELECT COUNT(DISTINCT telegram_id) as count FROM miniapp_sessions 
               WHERE ip_address = ? AND telegram_id != ?""",
            (ip_address, telegram_id)
        )
        return (result['count'] if result else 0) >= threshold
    
    # ==================== STATS METHODS ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        # Total users
        total_users = await self.fetchone("SELECT COUNT(*) as count FROM users")
        
        # New users today
        today = datetime.utcnow().strftime('%Y-%m-%d')
        new_today = await self.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE DATE(joined_at) = ?",
            (today,)
        )
        
        # Total orders
        total_orders = await self.fetchone("SELECT COUNT(*) as count FROM orders")
        
        # Total points spent
        total_spent = await self.fetchone(
            "SELECT SUM(amount) as total FROM orders"
        )
        
        # Banned users
        banned = await self.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE is_banned = 1"
        )
        
        # Flagged users
        flagged = await self.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE miniapp_flagged = 1"
        )
        
        # Top referrers
        top_referrers = await self.fetchall(
            """SELECT referrer_id, COUNT(*) as count FROM referrals 
               WHERE status = 'active' GROUP BY referrer_id ORDER BY count DESC LIMIT 10"""
        )
        
        # Top products
        top_products = await self.fetchall(
            """SELECT p.name_ar, p.name_en, COUNT(*) as count FROM orders o 
               JOIN products p ON o.product_id = p.id 
               GROUP BY o.product_id ORDER BY count DESC LIMIT 5"""
        )
        
        return {
            'total_users': total_users['count'] if total_users else 0,
            'new_today': new_today['count'] if new_today else 0,
            'total_orders': total_orders['count'] if total_orders else 0,
            'total_points_spent': total_spent['total'] if total_spent else 0,
            'banned_users': banned['count'] if banned else 0,
            'flagged_users': flagged['count'] if flagged else 0,
            'top_referrers': top_referrers,
            'top_products': top_products
        }

    # ==================== V2 METHODS ====================

    async def points_to_stars(self, points: int) -> int:
        rate = int(await self.get_setting('stars_per_point', '4'))
        return points * rate

    async def stars_to_points(self, stars: int) -> int:
        rate = int(await self.get_setting('stars_per_point', '4'))
        return stars // rate

    async def create_star_order(self, user_id: int, stars_amount: int, points_cost: int):
        import random, string
        order_id = f"SO-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        try:
            await self.execute(
                "INSERT INTO star_orders (user_id, stars_amount, points_cost, order_id) VALUES (?, ?, ?, ?)",
                (user_id, stars_amount, points_cost, order_id))
            return order_id
        except Exception:
            return None

    async def get_star_order(self, order_id: str):
        return await self.fetchone("SELECT * FROM star_orders WHERE order_id = ?", (order_id,))

    async def get_user_star_orders(self, user_id: int, limit: int = 20):
        return await self.fetchall(f"SELECT * FROM star_orders WHERE user_id = ? ORDER BY created_at DESC LIMIT {limit}", (user_id,))

    async def get_pending_star_orders(self):
        return await self.fetchall("SELECT * FROM star_orders WHERE status = 'pending' ORDER BY created_at ASC")

    async def get_pending_star_orders_count(self) -> int:
        result = await self.fetchone("SELECT COUNT(*) as count FROM star_orders WHERE status = 'pending'")
        return result['count'] if result else 0

    async def get_expired_star_orders(self):
        return await self.fetchall("SELECT * FROM star_orders WHERE status = 'pending' AND datetime(created_at) < datetime('now', '-24 hours')")

    async def update_star_order_status(self, order_id: str, status: str, **kwargs):
        allowed = ['delivered_at', 'cancelled_at', 'confirmed_at', 'admin_id']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        set_parts = ["status = ?"]
        values = [status]
        for k, v in updates.items():
            set_parts.append(f"{k} = ?")
            values.append(v)
        values.append(order_id)
        await self.execute(f"UPDATE star_orders SET {', '.join(set_parts)} WHERE order_id = ?", tuple(values))

    async def set_user_restricted(self, telegram_id: int, restricted: bool = True):
        await self.execute("UPDATE users SET is_restricted = ? WHERE telegram_id = ?", (1 if restricted else 0, telegram_id))

    async def is_user_restricted(self, telegram_id: int) -> bool:
        result = await self.fetchone("SELECT is_restricted FROM users WHERE telegram_id = ?", (telegram_id,))
        return bool(result and result.get('is_restricted', 0))

    async def set_admin_notes(self, telegram_id: int, notes: str):
        await self.execute("UPDATE users SET admin_notes = ? WHERE telegram_id = ?", (notes, telegram_id))

    async def update_channel(self, channel_id: str, **kwargs):
        allowed = ['channel_id', 'channel_name', 'channel_url', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if updates:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [channel_id]
            await self.execute(f"UPDATE channels SET {set_clause} WHERE channel_id = ?", tuple(values))

    async def delete_channel(self, channel_id: str):
        await self.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))

    async def delete_stock_item(self, stock_id: int):
        await self.execute("DELETE FROM product_stock WHERE id = ?", (stock_id,))

    async def create_ad_task(self, title: str, url: str, points_reward: int, is_once_per_user: int = 1, cooldown_hours: int = 24):
        return await self.execute(
            "INSERT INTO ad_tasks (title, url, points_reward, is_once_per_user, cooldown_hours) VALUES (?, ?, ?, ?, ?)",
            (title, url, points_reward, is_once_per_user, cooldown_hours))

    async def get_ad_tasks(self, active_only: bool = True):
        if active_only:
            return await self.fetchall("SELECT * FROM ad_tasks WHERE is_active = 1 ORDER BY id")
        return await self.fetchall("SELECT * FROM ad_tasks ORDER BY id")

    async def get_ad_task(self, ad_id: int):
        return await self.fetchone("SELECT * FROM ad_tasks WHERE id = ?", (ad_id,))

    async def update_ad_task(self, ad_id: int, **kwargs):
        allowed = ['title', 'url', 'points_reward', 'is_once_per_user', 'cooldown_hours', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if updates:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [ad_id]
            await self.execute(f"UPDATE ad_tasks SET {set_clause} WHERE id = ?", tuple(values))

    async def delete_ad_task(self, ad_id: int):
        await self.execute("DELETE FROM ad_tasks WHERE id = ?", (ad_id,))

    async def increment_ad_claims(self, ad_id: int):
        await self.execute("UPDATE ad_tasks SET total_claims = total_claims + 1 WHERE id = ?", (ad_id,))

    async def create_ad_claim(self, user_id: int, ad_id: int, screenshot_file_id: str):
        return await self.execute(
            "INSERT INTO ad_claims (user_id, ad_id, screenshot_file_id) VALUES (?, ?, ?)",
            (user_id, ad_id, screenshot_file_id))

    async def get_ad_claim(self, claim_id: int):
        return await self.fetchone("SELECT * FROM ad_claims WHERE id = ?", (claim_id,))

    async def get_user_ad_claims(self, user_id: int, ad_id: int):
        return await self.fetchall(
            "SELECT * FROM ad_claims WHERE user_id = ? AND ad_id = ? ORDER BY submitted_at DESC",
            (user_id, ad_id))

    async def get_pending_ad_claims(self):
        return await self.fetchall("SELECT * FROM ad_claims WHERE status = 'pending' ORDER BY submitted_at ASC")

    async def update_ad_claim(self, claim_id: int, status: str, **kwargs):
        allowed = ['reject_reason', 'reviewed_at', 'reviewed_by']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        set_parts = ["status = ?"]
        values = [status]
        for k, v in updates.items():
            set_parts.append(f"{k} = ?")
            values.append(v)
        values.append(claim_id)
        await self.execute(f"UPDATE ad_claims SET {', '.join(set_parts)} WHERE id = ?", tuple(values))

    async def has_approved_ad_claim(self, user_id: int, ad_id: int):
        result = await self.fetchone(
            "SELECT 1 FROM ad_claims WHERE user_id = ? AND ad_id = ? AND status = 'approved'",
            (user_id, ad_id))
        return result is not None

    async def has_pending_ad_claim(self, user_id: int, ad_id: int):
        result = await self.fetchone(
            "SELECT 1 FROM ad_claims WHERE user_id = ? AND ad_id = ? AND status = 'pending'",
            (user_id, ad_id))
        return result is not None

    async def get_last_approved_claim_time(self, user_id: int, ad_id: int):
        result = await self.fetchone(
            "SELECT submitted_at FROM ad_claims WHERE user_id = ? AND ad_id = ? AND status = 'approved' ORDER BY submitted_at DESC LIMIT 1",
            (user_id, ad_id))
        if result and result.get('submitted_at'):
            ts = result['submitted_at']
            if isinstance(ts, str):
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return ts
        return None


# Global database instance
db = Database()


# ==================== NEW METHODS FOR V2 ====================

# Points <-> Stars conversion
async def points_to_stars(points: int) -> int:
    """Convert points to stars cost."""
    rate = int(await db.get_setting('stars_per_point', '4'))
    return points * rate

async def stars_to_points(stars: int) -> int:
    """Convert stars to points cost."""
    rate = int(await db.get_setting('stars_per_point', '4'))
    return stars // rate

# Star Orders methods
async def create_star_order(user_id: int, stars_amount: int, points_cost: int) -> Optional[str]:
    """Create a star withdrawal order. Returns order_id."""
    order_id = f"SO-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    try:
        await db.execute(
            """INSERT INTO star_orders (user_id, stars_amount, points_cost, order_id)
               VALUES (?, ?, ?, ?)""",
            (user_id, stars_amount, points_cost, order_id)
        )
        return order_id
    except Exception:
        return None

async def get_star_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Get star order by order_id."""
    return await db.fetchone(
        "SELECT * FROM star_orders WHERE order_id = ?",
        (order_id,)
    )

async def get_user_star_orders(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Get user's star orders."""
    return await db.fetchall(
        f"SELECT * FROM star_orders WHERE user_id = ? ORDER BY created_at DESC LIMIT {limit}",
        (user_id,)
    )

async def get_pending_star_orders() -> List[Dict[str, Any]]:
    """Get all pending star orders."""
    return await db.fetchall(
        "SELECT * FROM star_orders WHERE status = 'pending' ORDER BY created_at ASC"
    )

async def update_star_order_status(order_id: str, status: str, **kwargs):
    """Update star order status."""
    allowed = ['delivered_at', 'cancelled_at', 'confirmed_at', 'admin_id']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    set_parts = ["status = ?"]
    values = [status]
    for k, v in updates.items():
        set_parts.append(f"{k} = ?")
        values.append(v)
    values.append(order_id)
    set_clause = ", ".join(set_parts)
    await db.execute(
        f"UPDATE star_orders SET {set_clause} WHERE order_id = ?",
        tuple(values)
    )

async def get_pending_star_orders_count() -> int:
    """Get count of pending star orders."""
    result = await db.fetchone(
        "SELECT COUNT(*) as count FROM star_orders WHERE status = 'pending'"
    )
    return result['count'] if result else 0

async def get_expired_star_orders() -> List[Dict[str, Any]]:
    """Get star orders older than 24 hours that are still pending."""
    return await db.fetchall(
        """SELECT * FROM star_orders WHERE status = 'pending'
           AND datetime(created_at) < datetime('now', '-24 hours')"""
    )

# User restriction methods
async def set_user_restricted(telegram_id: int, restricted: bool = True):
    """Restrict or unrestrict a user."""
    await db.execute(
        "UPDATE users SET is_restricted = ? WHERE telegram_id = ?",
        (1 if restricted else 0, telegram_id)
    )

async def is_user_restricted(telegram_id: int) -> bool:
    """Check if user is restricted."""
    result = await db.fetchone(
        "SELECT is_restricted FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    return bool(result and result.get('is_restricted', 0))

async def set_admin_notes(telegram_id: int, notes: str):
    """Set admin notes for a user."""
    await db.execute(
        "UPDATE users SET admin_notes = ? WHERE telegram_id = ?",
        (notes, telegram_id)
    )

# Channel methods (updated for V2)
async def update_channel(channel_id: str, **kwargs):
    """Update channel fields."""
    allowed = ['channel_id', 'channel_name', 'channel_url', 'is_active']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if updates:
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [channel_id]
        await db.execute(
            f"UPDATE channels SET {set_clause} WHERE channel_id = ?",
            tuple(values)
        )

async def delete_channel(channel_id: str):
    """Delete a channel."""
    await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))

# Product stock - permanent delete method
async def delete_stock_item(stock_id: int):
    """Permanently delete a stock item."""
    await db.execute("DELETE FROM product_stock WHERE id = ?", (stock_id,))

# Ad tasks methods
async def create_ad_task(title: str, url: str, points_reward: int,
                        is_once_per_user: int = 1, cooldown_hours: int = 24) -> int:
    """Create a new ad task. Returns ad id."""
    return await db.execute(
        """INSERT INTO ad_tasks (title, url, points_reward, is_once_per_user, cooldown_hours)
           VALUES (?, ?, ?, ?, ?)""",
        (title, url, points_reward, is_once_per_user, cooldown_hours)
    )

async def get_ad_tasks(active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all ad tasks."""
    if active_only:
        return await db.fetchall(
            "SELECT * FROM ad_tasks WHERE is_active = 1 ORDER BY id"
        )
    return await db.fetchall("SELECT * FROM ad_tasks ORDER BY id")

async def get_ad_task(ad_id: int) -> Optional[Dict[str, Any]]:
    """Get ad task by ID."""
    return await db.fetchone(
        "SELECT * FROM ad_tasks WHERE id = ?",
        (ad_id,)
    )

async def update_ad_task(ad_id: int, **kwargs):
    """Update ad task fields."""
    allowed = ['title', 'url', 'points_reward', 'is_once_per_user', 'cooldown_hours', 'is_active']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if updates:
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [ad_id]
        await db.execute(
            f"UPDATE ad_tasks SET {set_clause} WHERE id = ?",
            tuple(values)
        )

async def delete_ad_task(ad_id: int):
    """Delete an ad task."""
    await db.execute("DELETE FROM ad_tasks WHERE id = ?", (ad_id,))

async def increment_ad_claims(ad_id: int):
    """Increment total claims for an ad."""
    await db.execute(
        "UPDATE ad_tasks SET total_claims = total_claims + 1 WHERE id = ?",
        (ad_id,)
    )

# Ad claims methods
async def create_ad_claim(user_id: int, ad_id: int, screenshot_file_id: str) -> int:
    """Create a new ad claim. Returns claim id."""
    return await db.execute(
        """INSERT INTO ad_claims (user_id, ad_id, screenshot_file_id)
           VALUES (?, ?, ?)""",
        (user_id, ad_id, screenshot_file_id)
    )

async def get_ad_claim(claim_id: int) -> Optional[Dict[str, Any]]:
    """Get ad claim by ID."""
    return await db.fetchone(
        "SELECT * FROM ad_claims WHERE id = ?",
        (claim_id,)
    )

async def get_user_ad_claims(user_id: int, ad_id: int) -> List[Dict[str, Any]]:
    """Get user's claims for a specific ad."""
    return await db.fetchall(
        "SELECT * FROM ad_claims WHERE user_id = ? AND ad_id = ? ORDER BY submitted_at DESC",
        (user_id, ad_id)
    )

async def get_pending_ad_claims() -> List[Dict[str, Any]]:
    """Get all pending ad claims."""
    return await db.fetchall(
        "SELECT * FROM ad_claims WHERE status = 'pending' ORDER BY submitted_at ASC"
    )

async def update_ad_claim(claim_id: int, status: str, **kwargs):
    """Update ad claim status."""
    allowed = ['reject_reason', 'reviewed_at', 'reviewed_by']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    set_parts = ["status = ?"]
    values = [status]
    for k, v in updates.items():
        set_parts.append(f"{k} = ?")
        values.append(v)
    values.append(claim_id)
    set_clause = ", ".join(set_parts)
    await db.execute(
        f"UPDATE ad_claims SET {set_clause} WHERE id = ?",
        tuple(values)
    )

async def has_approved_ad_claim(user_id: int, ad_id: int) -> bool:
    """Check if user has an approved claim for an ad."""
    result = await db.fetchone(
        "SELECT 1 FROM ad_claims WHERE user_id = ? AND ad_id = ? AND status = 'approved'",
        (user_id, ad_id)
    )
    return result is not None

async def has_pending_ad_claim(user_id: int, ad_id: int) -> bool:
    """Check if user has a pending claim for an ad."""
    result = await db.fetchone(
        "SELECT 1 FROM ad_claims WHERE user_id = ? AND ad_id = ? AND status = 'pending'",
        (user_id, ad_id)
    )
    return result is not None

async def get_last_approved_claim_time(user_id: int, ad_id: int) -> Optional[datetime]:
    """Get the timestamp of user's last approved claim for an ad."""
    result = await db.fetchone(
        """SELECT submitted_at FROM ad_claims
           WHERE user_id = ? AND ad_id = ? AND status = 'approved'
           ORDER BY submitted_at DESC LIMIT 1""",
        (user_id, ad_id)
    )
    if result and result.get('submitted_at'):
        ts = result['submitted_at']
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace('Z', '+00:00').replace('+00:00', ''))
        return ts
    return None
