-- ============================================
-- TELEGRAM STORE BOT - MySQL DATABASE SCHEMA
-- Phone verification REMOVED version
-- ============================================

-- Users table (no phone verification fields)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ar',
    points INT DEFAULT 0,
    total_earned INT DEFAULT 0,
    total_spent INT DEFAULT 0,
    referral_code VARCHAR(50) UNIQUE,
    referred_by BIGINT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_banned TINYINT DEFAULT 0,
    setup_complete TINYINT DEFAULT 0,
    miniapp_verified TINYINT DEFAULT 0,
    miniapp_flagged TINYINT DEFAULT 0,
    ip_address VARCHAR(255),
    device_fingerprint VARCHAR(255),
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_referral_code (referral_code),
    INDEX idx_referred_by (referred_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    added_by BIGINT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telegram_id (telegram_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name_ar VARCHAR(255) NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    is_active TINYINT DEFAULT 1,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_is_active (is_active),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name_ar VARCHAR(255) NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    description_ar TEXT,
    description_en TEXT,
    delivery_type TEXT NOT NULL DEFAULT 'oncesell_text',
    points_price INT NOT NULL,
    stock INT DEFAULT 0,
    is_visible TINYINT DEFAULT 1,
    file_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_category_id (category_id),
    INDEX idx_is_visible (is_visible),
    INDEX idx_delivery_type (delivery_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Product stock table (for code/account type products)
CREATE TABLE IF NOT EXISTS product_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    content TEXT NOT NULL,
    is_sold TINYINT DEFAULT 0,
    sold_to BIGINT,
    sold_at TIMESTAMP NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_is_sold (is_sold)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'points',
    amount INT NOT NULL,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'completed',
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_user_id (user_id),
    INDEX idx_order_id (order_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    channel_id VARCHAR(255) UNIQUE NOT NULL,
    channel_name VARCHAR(255),
    channel_url VARCHAR(255) NOT NULL,
    is_active TINYINT DEFAULT 1,
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Coupons table
CREATE TABLE IF NOT EXISTS coupons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    points_value INT NOT NULL,
    max_uses INT DEFAULT 1,
    used_count INT DEFAULT 0,
    expires_at TIMESTAMP NULL,
    is_active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    INDEX idx_code (code),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Coupon uses table (track which user used which coupon)
CREATE TABLE IF NOT EXISTS coupon_uses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coupon_id INT NOT NULL,
    user_id BIGINT NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_coupon_user (coupon_id, user_id),
    FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Referrals table
CREATE TABLE IF NOT EXISTS referrals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT UNIQUE NOT NULL,
    points_awarded INT DEFAULT 0,
    status ENUM('pending', 'active', 'penalized') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    FOREIGN KEY (referrer_id) REFERENCES users(telegram_id),
    INDEX idx_referrer_id (referrer_id),
    INDEX idx_referred_id (referred_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Waiting list table (notify when product restocked)
CREATE TABLE IF NOT EXISTS waiting_list (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    notified TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_product (user_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_notified (notified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    admin_reply TEXT,
    status ENUM('open', 'replied', 'closed') DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    replied_at TIMESTAMP NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Daily bonus table
CREATE TABLE IF NOT EXISTS daily_bonus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    last_claimed TIMESTAMP NULL,
    streak INT DEFAULT 0,
    INDEX idx_user_id (user_id),
    INDEX idx_last_claimed (last_claimed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Stars packages table
CREATE TABLE IF NOT EXISTS stars_packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stars_amount INT NOT NULL,
    points_amount INT NOT NULL,
    is_active TINYINT DEFAULT 1,
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Broadcasts table
CREATE TABLE IF NOT EXISTS broadcasts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT,
    photo_id VARCHAR(255),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_by BIGINT,
    total INT DEFAULT 0,
    success INT DEFAULT 0,
    failed INT DEFAULT 0,
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Mini app sessions table
CREATE TABLE IF NOT EXISTS miniapp_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    ip_address VARCHAR(255),
    fingerprint VARCHAR(255),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_duplicate TINYINT DEFAULT 0,
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_fingerprint (fingerprint),
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Star orders table
CREATE TABLE IF NOT EXISTS star_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    stars_amount INT NOT NULL,
    points_cost INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    order_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    confirmed_at TIMESTAMP NULL,
    admin_id BIGINT,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ad tasks table
CREATE TABLE IF NOT EXISTS ad_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    points_reward INT NOT NULL,
    is_once_per_user TINYINT DEFAULT 1,
    cooldown_hours INT DEFAULT 24,
    is_active TINYINT DEFAULT 1,
    total_claims INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ad claims table
CREATE TABLE IF NOT EXISTS ad_claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    ad_id INT NOT NULL,
    screenshot_file_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    reject_reason TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    reviewed_by BIGINT,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_ad_id (ad_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DEFAULT SETTINGS
-- ============================================

INSERT INTO settings (setting_key, setting_value) VALUES
('referral_points', '1'),
('daily_bonus_points', '10'),
('penalty_mode', 'false'),
('welcome_message_ar', 'مرحباً بك في المتجر! 🎉'),
('welcome_message_en', 'Welcome to the store! 🎉'),
('stars_per_point', '4'),
('stars_withdrawal_open', 'true'),
('low_stock_threshold', '5')
ON DUPLICATE KEY UPDATE setting_value = setting_value;

-- ============================================
-- DEFAULT STARS PACKAGES
-- ============================================

INSERT INTO stars_packages (stars_amount, points_amount, is_active) VALUES
(1, 100, 1),
(5, 550, 1),
(10, 1200, 1),
(25, 3250, 1),
(50, 7000, 1)
ON DUPLICATE KEY UPDATE stars_amount = stars_amount;
