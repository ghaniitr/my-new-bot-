"""
Configuration module for Telegram Store Bot.
Loads and validates all environment variables.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Bot configuration loaded from environment variables."""
    
    # Required settings
    BOT_TOKEN: str
    SUPER_ADMIN_ID: int
    
    # Database settings
    DB_TYPE: str  # 'sqlite' or 'mysql'
    DB_PATH: str  # For SQLite
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    
    # Mini app settings
    MINIAPP_URL: str
    MINIAPP_SECRET: str
    MINIAPP_PORT: int
    
    # Referral settings
    REFERRAL_DELAY_SECONDS: int
    MIN_ACCOUNT_AGE_DAYS: int
    
    # Environment detection
    RAILWAY_ENV: bool
    
    # Optional webhook settings
    WEBHOOK_URL: str
    WEBHOOK_SECRET: str


def load_config() -> Config:
    """
    Load and validate configuration from environment variables.
    Raises ValueError if required variables are missing.
    """
    
    # Required variables
    bot_token = os.getenv('BOT_TOKEN', '').strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required! Get it from @BotFather")
    
    super_admin_id_str = os.getenv('SUPER_ADMIN_ID', '').strip()
    if not super_admin_id_str:
        raise ValueError("SUPER_ADMIN_ID is required! Get your ID from @userinfobot")
    try:
        super_admin_id = int(super_admin_id_str)
    except ValueError:
        raise ValueError("SUPER_ADMIN_ID must be a valid integer!")
    
    # Database configuration
    db_type = os.getenv('DB_TYPE', 'sqlite').lower().strip()
    if db_type not in ('sqlite', 'mysql'):
        raise ValueError("DB_TYPE must be either 'sqlite' or 'mysql'")
    
    # Mini app URL validation
    miniapp_url = os.getenv('MINIAPP_URL', '').strip()
    if not miniapp_url:
        raise ValueError("MINIAPP_URL is required! Example: https://your-domain.com/miniapp.php")
    
    # Mini app secret
    miniapp_secret = os.getenv('MINIAPP_SECRET', '').strip()
    if not miniapp_secret:
        raise ValueError("MINIAPP_SECRET is required! Generate a random string")
    
    # Railway environment detection
    railway_env = os.getenv('RAILWAY_ENV', 'false').lower() in ('true', '1', 'yes', 'on')
    
    config = Config(
        BOT_TOKEN=bot_token,
        SUPER_ADMIN_ID=super_admin_id,
        
        DB_TYPE=db_type,
        DB_PATH=os.getenv('DB_PATH', 'bot.db'),
        MYSQL_HOST=os.getenv('MYSQL_HOST', 'localhost'),
        MYSQL_PORT=int(os.getenv('MYSQL_PORT', '3306')),
        MYSQL_USER=os.getenv('MYSQL_USER', 'botuser'),
        MYSQL_PASSWORD=os.getenv('MYSQL_PASSWORD', ''),
        MYSQL_DATABASE=os.getenv('MYSQL_DATABASE', 'storebot'),
        
        MINIAPP_URL=miniapp_url,
        MINIAPP_SECRET=miniapp_secret,
        MINIAPP_PORT=int(os.getenv('PORT', os.getenv('MINIAPP_PORT', '8080'))),
        
        REFERRAL_DELAY_SECONDS=int(os.getenv('REFERRAL_DELAY_SECONDS', '60')),
        MIN_ACCOUNT_AGE_DAYS=int(os.getenv('MIN_ACCOUNT_AGE_DAYS', '0')),
        
        RAILWAY_ENV=railway_env,
        
        WEBHOOK_URL=os.getenv('WEBHOOK_URL', ''),
        WEBHOOK_SECRET=os.getenv('WEBHOOK_SECRET', ''),
    )
    
    return config


# Global config instance
config = load_config()
