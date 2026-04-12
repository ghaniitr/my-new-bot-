# Telegram Store Bot - Complete Guide

A comprehensive, production-ready Telegram store bot with points system, referrals, anti-farming protection, and full admin panel.

**Phone number verification has been REMOVED** from this version for easier onboarding.

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [Detailed Setup Guide](#detailed-setup-guide)
   - [Railway Deployment](#railway-deployment-cloud)
   - [VPS Deployment](#vps-deployment-self-hosted)
   - [Local Development](#local-development)
5. [How to Use the Bot](#how-to-use-the-bot)
6. [Admin Panel Guide](#admin-panel-guide)
7. [Configuration Reference](#configuration-reference)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)

---

## Features

### User Features
- **Bilingual Support**: Arabic and English
- **Points System**: Earn and spend points
- **Store**: Browse categories and purchase products
- **Daily Bonus**: Claim points every 24 hours
- **Referral System**: Invite friends and earn points
- **Coupons**: Redeem coupon codes for points
- **Support Tickets**: Contact support directly
- **Buy Points**: Purchase points with Telegram Stars

### Product Types
- **PDF Files**: Digital documents
- **ZIP Files**: Compressed archives
- **Codes/Keys**: Serial numbers, activation codes
- **Accounts**: Login credentials

### Admin Features
- **Products Management**: Add, edit, delete products
- **Categories Management**: Organize products
- **Channels Management**: Force users to join channels
- **Coupons Management**: Create and manage coupon codes
- **User Management**: Search users, add/remove points, ban/unban
- **Admin Management**: Add/remove bot admins
- **Statistics**: View bot usage stats
- **Broadcast**: Send messages to all users
- **Support Tickets**: Reply to user tickets
- **Stars Packages**: Configure Telegram Stars packages
- **Settings**: Configure referral points, daily bonus, penalty mode

### Anti-Farming System (2 Layers)
1. **Mini App Verification**: Browser fingerprinting to detect duplicate accounts
2. **Channel Lock + Delay**: Referral points only awarded after delay if user stays in channels

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram User  │────▶│  Telegram API   │────▶│   Bot (Python)  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌─────────────────────────┼─────────────────────────┐
                              │                         │                         │
                              ▼                         ▼                         ▼
                    ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
                    │   SQLite/MySQL  │       │  Mini App Server│       │   Scheduler     │
                    │    (Database)   │       │  (Anti-farming) │       │ (Background)    │
                    └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### File Structure
```
project/
├── main.py                 # Bot entry point
├── config.py               # Environment configuration
├── database.py             # Database abstraction (SQLite + MySQL)
├── middlewares.py          # Channel check middleware
├── messages.py             # Bilingual messages
├── keyboards.py            # All keyboard layouts
├── scheduler.py            # Background tasks
├── miniapp_server.py       # aiohttp server (Railway)
├── handlers/
│   ├── __init__.py
│   ├── start.py            # User onboarding (NO phone verification)
│   ├── store.py            # Store and purchases
│   ├── points.py           # Points, coupons, daily bonus
│   ├── referral.py         # Referral system
│   ├── support.py          # Support tickets
│   └── admin.py            # Admin panel
├── php/                    # PHP mini app (VPS only)
│   ├── miniapp.php
│   ├── verify.php
│   └── db.php
├── nginx/
│   └── bot.conf            # Nginx configuration
├── schema.sql              # MySQL schema
├── requirements.txt        # Python dependencies
├── Procfile                # Railway process
├── railway.toml            # Railway config
├── .env.example            # Environment template
└── README.md               # This file
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Your Telegram User ID (from @userinfobot)

### 1. Get Your Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send `/newbot`
3. Follow instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`)

### 2. Get Your User ID
1. Search for [@userinfobot](https://t.me/userinfobot)
2. Start the bot
3. It will reply with your ID (looks like: `123456789`)

### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=your_bot_token_here
SUPER_ADMIN_ID=your_telegram_id_here
DB_TYPE=sqlite
DB_PATH=bot.db
MINIAPP_URL=https://your-domain.com/miniapp.php  # For VPS
MINIAPP_SECRET=your_random_secret_here
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Bot
```bash
python main.py
```

---

## Detailed Setup Guide

### Railway Deployment (Cloud)

Railway is the easiest way to deploy - it's free for small projects and handles everything automatically.

#### Step 1: Prepare Your Code
1. Create a GitHub repository
2. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

#### Step 2: Create Railway Project
1. Go to [Railway](https://railway.app) and sign up/login
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Click "Deploy"

#### Step 3: Configure Environment Variables
1. In your Railway project, go to "Variables"
2. Add the following variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `BOT_TOKEN` | `123456789:ABC...` | Your bot token from @BotFather |
| `SUPER_ADMIN_ID` | `123456789` | Your Telegram user ID |
| `DB_TYPE` | `sqlite` | Keep as sqlite |
| `DB_PATH` | `/data/bot.db` | SQLite file path |
| `MINIAPP_URL` | Your Railway URL | Will be `https://your-app.up.railway.app` |
| `MINIAPP_SECRET` | Random string | Generate: `openssl rand -hex 32` |
| `RAILWAY_ENV` | `true` | Auto-detected |

#### Step 4: Add Volume (Important!)
SQLite data doesn't persist without a volume:
1. Go to your service in Railway
2. Click "Add Volume"
3. Mount path: `/data`
4. Size: 1GB (or more)

#### Step 5: Deploy
Railway will automatically deploy your bot. Check logs to verify it's running.

#### Step 6: Get Your Mini App URL
1. In Railway, go to your service
2. Click "Settings"
3. Find "Public Domain" (e.g., `your-app.up.railway.app`)
4. Update `MINIAPP_URL` to: `https://your-app.up.railway.app`
5. Redeploy

---

### VPS Deployment (Self-Hosted)

For full control and better performance, deploy on your own VPS.

#### Requirements
- Ubuntu 22.04+ server
- Domain name (recommended)
- Root or sudo access

#### Step 1: Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install Python
```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
```

#### Step 3: Install PHP and Nginx
```bash
sudo apt install -y php8.2-fpm php8.2-mysql nginx
```

#### Step 4: Install MySQL
```bash
sudo apt install -y mysql-server
sudo mysql_secure_installation
```

Create database:
```bash
sudo mysql -u root -p
```
```sql
CREATE DATABASE storebot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'botuser'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON storebot.* TO 'botuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Import schema:
```bash
mysql -u botuser -p storebot < schema.sql
```

#### Step 5: Setup Project
```bash
sudo mkdir -p /var/www/storebot
sudo chown -R $USER:$USER /var/www/storebot
cd /var/www/storebot

# Clone your repo or upload files
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
# OR upload via SCP/SFTP

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 6: Configure Environment
```bash
cp .env.example .env
nano .env
```

```env
BOT_TOKEN=your_bot_token
SUPER_ADMIN_ID=your_telegram_id
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=botuser
MYSQL_PASSWORD=your_strong_password
MYSQL_DATABASE=storebot
MINIAPP_URL=https://yourdomain.com/miniapp.php
MINIAPP_SECRET=your_random_secret
```

#### Step 7: Configure Nginx
```bash
sudo cp nginx/bot.conf /etc/nginx/sites-available/storebot
sudo nano /etc/nginx/sites-available/storebot
```

Replace `YOUR_DOMAIN.COM` with your actual domain.

```bash
sudo ln -s /etc/nginx/sites-available/storebot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 8: Get SSL Certificate
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### Step 9: Create Systemd Service
```bash
sudo nano /etc/systemd/system/storebot.service
```

```ini
[Unit]
Description=Telegram Store Bot
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/storebot
ExecStart=/var/www/storebot/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/var/www/storebot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable storebot
sudo systemctl start storebot
```

Check status:
```bash
sudo systemctl status storebot
sudo journalctl -u storebot -f
```

---

### Local Development

For testing and development on your local machine.

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd telegram-store-bot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run bot
python main.py
```

---

## How to Use the Bot

### For Users

#### First Time Setup
1. Start the bot with `/start`
2. Select your language (Arabic or English)
3. Complete mini app verification (opens web app)
4. Join required channels
5. Done! You're in the main menu

#### Main Menu Options

**🛍️ Store**
- Browse product categories
- View product details
- Purchase with points
- Get notified when out-of-stock items return

**💰 My Points**
- View current balance
- See total earned/spent
- Enter coupon codes
- View order history

**🔗 Referral**
- Get your unique referral link
- See how many friends joined
- Track points earned from referrals

**🎁 Daily Bonus**
- Claim free points every 24 hours
- Build streak for potential bonuses

**💎 Buy Points**
- Purchase points with Telegram Stars
- Choose from different packages

**📩 Support**
- Send message to support team
- Receive replies directly in bot

### For Admins

#### Access Admin Panel
1. Start bot with `/start`
2. Click "⚙️ Admin Panel" button

#### Managing Products
1. Click "📦 Products"
2. Click "➕ Add Product" to create new
3. Follow prompts: category → name → description → type → price → stock
4. For PDF/ZIP: upload file
5. For codes/accounts: paste items (one per line)

#### Managing Categories
1. Click "📂 Categories"
2. Click "➕ Add Category"
3. Enter names in English and Arabic

#### Managing Channels
1. Click "📢 Channels"
2. Click "➕ Add Channel"
3. Enter channel ID (e.g., `-1001234567890` or `@channelusername`)
4. Enter display name
5. Enter invite link (e.g., `https://t.me/+AbCdEfGhIjK`)

**Important**: Bot must be admin in each channel!

#### Creating Coupons
1. Click "🎟️ Coupons"
2. Click "➕ Generate Coupon"
3. Enter code (or AUTO for random)
4. Enter points value
5. Enter max uses (0 = unlimited)
6. Enter expiry date (YYYY-MM-DD) or NONE

#### Managing Users
1. Click "👥 Users"
2. Enter Telegram ID or @username
3. View profile and actions:
   - ➕ Add Points
   - ➖ Remove Points
   - 🚫 Ban/Unban

#### Broadcasting
1. Click "📣 Broadcast"
2. Send message (text, photo, video, or document)
3. Confirm to send to all users

#### Support Tickets
1. Click "🎫 Support"
2. Click on a ticket to view
3. Click "💬 Reply" to respond
4. Click "✅ Close" to close ticket

#### Settings
1. Click "⚙️ Settings"
2. Configure:
   - 🎯 Referral Points Value
   - 🎁 Daily Bonus Points
   - 💬 Welcome Messages
   - ⚠️ Penalty Mode (ON/OFF)

---

## Admin Panel Guide

### Products Management

**Adding a Product:**
```
Admin Panel → 📦 Products → ➕ Add Product
→ Select Category
→ Enter Name (English)
→ Enter Name (Arabic)
→ Enter Description (English) or "-" to skip
→ Enter Description (Arabic) or "-" to skip
→ Select Type: PDF/ZIP/Code/Account
→ Enter Points Price
→ Upload file (for PDF/ZIP) OR paste stock items (for Code/Account)
```

**Restocking:**
```
Admin Panel → 📦 Products → [Select Product] → 📦 Add Stock
→ Paste new items (one per line)
→ Waiting list users are automatically notified
```

### Understanding Product Types

| Type | Use Case | Stock Management |
|------|----------|------------------|
| PDF | E-books, documents | Single file, unlimited downloads |
| ZIP | Software bundles | Single file, unlimited downloads |
| Code | License keys, gift cards | Individual items, one per purchase |
| Account | Login credentials | Individual items, one per purchase |

### Channel Requirements

For channel lock to work:
1. Bot must be **admin** in the channel
2. Channel must be public OR bot must be member via invite link
3. Add bot as admin with these permissions:
   - Read messages
   - Delete messages (optional)
   - Restrict members (optional)

### Penalty Mode

When enabled:
- System checks every 10 minutes
- If referred user leaves any channel, referrer loses points
- If user rejoins, points are restored
- Prevents referral farming

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | Telegram bot token |
| `SUPER_ADMIN_ID` | Yes | - | Your Telegram user ID |
| `DB_TYPE` | No | sqlite | `sqlite` or `mysql` |
| `DB_PATH` | No | bot.db | SQLite file path |
| `MYSQL_HOST` | No | localhost | MySQL host |
| `MYSQL_PORT` | No | 3306 | MySQL port |
| `MYSQL_USER` | No | botuser | MySQL username |
| `MYSQL_PASSWORD` | No | - | MySQL password |
| `MYSQL_DATABASE` | No | storebot | MySQL database name |
| `MINIAPP_URL` | Yes | - | URL to mini app |
| `MINIAPP_SECRET` | Yes | - | Secret for mini app |
| `REFERRAL_DELAY_SECONDS` | No | 60 | Seconds before referral points awarded |
| `MIN_ACCOUNT_AGE_DAYS` | No | 0 | Block new accounts (0 = disabled) |
| `RAILWAY_ENV` | No | false | Auto-detected on Railway |
| `MINIAPP_PORT` | No | 8080 | Port for mini app server |
| `WEBHOOK_URL` | No | - | Optional webhook URL |
| `WEBHOOK_SECRET` | No | - | Webhook secret |

### Database Settings (Admin Panel)

| Setting | Default | Description |
|---------|---------|-------------|
| `referral_points` | 1 | Points awarded per referral |
| `daily_bonus_points` | 10 | Points for daily bonus |
| `penalty_mode` | false | Enable penalty system |
| `welcome_message_ar` | - | Arabic welcome message |
| `welcome_message_en` | - | English welcome message |

---

## Troubleshooting

### Bot Not Responding
1. Check logs: `sudo journalctl -u storebot -f` (VPS) or Railway logs
2. Verify `BOT_TOKEN` is correct
3. Ensure bot is not blocked by user

### Database Errors
1. Check database connection settings
2. Verify MySQL is running: `sudo systemctl status mysql`
3. Check database exists: `SHOW DATABASES;` in MySQL

### Channel Check Not Working
1. Verify bot is admin in channel
2. Check channel ID format (use `-100` prefix for private channels)
3. Test manually: Add bot, check with `/start`

### Mini App Not Loading
1. Verify `MINIAPP_URL` is correct
2. Check SSL certificate is valid
3. Test URL in browser

### Referral Points Not Awarded
1. Check `REFERRAL_DELAY_SECONDS` (default 60 seconds)
2. Verify referred user is still in all channels
3. Check if penalty mode is enabled
4. Verify referred user is not flagged

### Payment Not Working
1. Ensure bot has payment provider set up (Telegram Stars)
2. Check Stars packages are configured in admin panel
3. Verify user has sufficient Stars balance

---

## Security Considerations

### Anti-Farming System
This bot includes anti-farming protection:
1. **Mini App Verification**: Collects browser fingerprint to detect duplicate accounts
2. **IP Checking**: Flags accounts using same IP
3. **Channel Lock**: Requires users to stay in channels
4. **Penalty Mode**: Deducts points if referred users leave

### Best Practices
1. **Keep secrets safe**: Never commit `.env` to git
2. **Use strong passwords**: For MySQL and mini app secret
3. **Regular backups**: Backup database daily
4. **Monitor logs**: Watch for suspicious activity
5. **Update dependencies**: Keep packages up to date

### Database Backup (VPS)
```bash
# Backup
mysqldump -u botuser -p storebot > backup_$(date +%Y%m%d).sql

# Restore
mysql -u botuser -p storebot < backup_YYYYMMDD.sql
```

### SQLite Backup (Railway)
```bash
# Download from Railway volume
railway volumes download <volume-id> /data/bot.db
```

---

## Commands Reference

### Bot Commands
| Command | Description |
|---------|-------------|
| `/start` | Start bot or show main menu |

### Admin Actions
All admin actions are done through inline buttons in the bot.

---

## Support

For issues or questions:
1. Check this README thoroughly
2. Review logs for error messages
3. Open an issue on GitHub

---

## License

This project is open source. Feel free to modify and distribute.

---

**Happy bot building!** 🚀
