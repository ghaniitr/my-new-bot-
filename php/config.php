<?php
/**
 * PHP Configuration
 * Load environment variables for VPS deployment
 */

// Load .env file if exists
$env_file = __DIR__ . '/../.env';
if (file_exists($env_file)) {
    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos($line, '=') !== false && strpos($line, '#') !== 0) {
            list($key, $value) = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);
            if (!empty($key)) {
                putenv("$key=$value");
                $_ENV[$key] = $value;
            }
        }
    }
}

// Database configuration
$db_config = [
    'host' => getenv('MYSQL_HOST') ?: 'localhost',
    'port' => getenv('MYSQL_PORT') ?: '3306',
    'user' => getenv('MYSQL_USER') ?: 'botuser',
    'password' => getenv('MYSQL_PASSWORD') ?: '',
    'database' => getenv('MYSQL_DATABASE') ?: 'storebot'
];
