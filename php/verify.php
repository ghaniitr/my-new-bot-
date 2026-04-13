<?php
/**
 * Verification endpoint for PHP mini app
 */

require_once __DIR__ . '/db.php';

// Get JSON input
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Invalid input']);
    exit;
}

// Validate Telegram init data
$init_data = $data['init_data'] ?? '';
$bot_token = getenv('BOT_TOKEN') ?: '';

if (!validate_telegram_init_data($init_data, $bot_token)) {
    http_response_code(403);
    echo json_encode(['status' => 'error', 'message' => 'Invalid init data']);
    exit;
}

// Parse user from init data
parse_str($init_data, $parsed);
$user_json = $parsed['user'] ?? '{}';
$user_data = json_decode($user_json, true);
$telegram_id = $user_data['id'] ?? null;

if (!$telegram_id) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'User ID not found']);
    exit;
}

// Get IP address
$ip_address = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? 'unknown';
if (strpos($ip_address, ',') !== false) {
    $ip_address = trim(explode(',', $ip_address)[0]);
}

// Create fingerprint
$fingerprint = create_fingerprint_hash($data);

// Get database connection
$pdo = getDB();
if (!$pdo) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Database error']);
    exit;
}

// Check for duplicates
$is_duplicate = false;

// Check fingerprint for different user
$stmt = $pdo->prepare("SELECT 1 FROM miniapp_sessions WHERE fingerprint = ? AND telegram_id != ?");
$stmt->execute([$fingerprint, $telegram_id]);
if ($stmt->fetch()) {
    $is_duplicate = true;
}

// Check IP for multiple users
$stmt = $pdo->prepare("SELECT COUNT(DISTINCT telegram_id) as count FROM miniapp_sessions WHERE ip_address = ? AND telegram_id != ?");
$stmt->execute([$ip_address, $telegram_id]);
$result = $stmt->fetch();
if ($result && $result['count'] >= 3) {
    $is_duplicate = true;
}

// Store session
$stmt = $pdo->prepare("INSERT INTO miniapp_sessions (telegram_id, ip_address, fingerprint, is_duplicate) VALUES (?, ?, ?, ?)");
$stmt->execute([$telegram_id, $ip_address, $fingerprint, $is_duplicate ? 1 : 0]);

// Update user
$stmt = $pdo->prepare("UPDATE users SET miniapp_verified = 1, miniapp_flagged = ?, ip_address = ?, device_fingerprint = ? WHERE telegram_id = ?");
$stmt->execute([$is_duplicate ? 1 : 0, $ip_address, $fingerprint, $telegram_id]);

echo json_encode([
    'status' => $is_duplicate ? 'flagged' : 'ok',
    'duplicate' => $is_duplicate
]);

/**
 * Validate Telegram WebApp initData
 */
function validate_telegram_init_data($init_data, $bot_token) {
    if (empty($init_data) || empty($bot_token)) {
        return false;
    }
    
    parse_str($init_data, $data);
    
    if (!isset($data['hash'])) {
        return false;
    }
    
    $received_hash = $data['hash'];
    unset($data['hash']);
    
    // Build data check string
    $data_check_arr = [];
    foreach ($data as $key => $value) {
        $data_check_arr[] = $key . '=' . $value;
    }
    sort($data_check_arr);
    $data_check_string = implode("\n", $data_check_arr);
    
    // Calculate secret key
    $secret_key = hash_hmac('sha256', 'WebAppData', $bot_token, true);
    
    // Calculate hash
    $calculated_hash = hash_hmac('sha256', $data_check_string, $secret_key);
    
    return hash_equals($calculated_hash, $received_hash);
}

/**
 * Create fingerprint hash
 */
function create_fingerprint_hash($data) {
    $components = [
        $data['user_agent'] ?? '',
        $data['screen'] ?? '',
        $data['timezone'] ?? '',
        $data['canvas_fp'] ?? '',
        $data['webgl_renderer'] ?? '',
        $data['platform'] ?? ''
    ];
    $combined = implode('|', $components);
    return hash('sha256', $combined);
}
