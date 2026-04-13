"""
Mini App Server for Railway deployment.
Lightweight aiohttp server that serves the mini app and handles verification.
"""

import hmac
import hashlib
import urllib.parse
from datetime import datetime

from aiohttp import web

from database import db
from config import config


# HTML template for the mini app
MINIAPP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        .logo {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #fff;
        }
        p {
            color: #aaa;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #0088cc;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .btn {
            background: #0088cc;
            color: #fff;
            border: none;
            padding: 15px 40px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            display: none;
        }
        .btn:hover {
            background: #006699;
        }
        .btn.show {
            display: inline-block;
        }
        .success {
            color: #4CAF50;
            display: none;
        }
        .warning {
            color: #ff9800;
            display: none;
        }
        .status-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔒</div>
        
        <div id="loading">
            <h1>Verifying...</h1>
            <p>Please wait while we verify your identity</p>
            <div class="spinner"></div>
        </div>
        
        <div id="success" class="hidden">
            <div class="status-icon">✅</div>
            <h1>Verification Successful!</h1>
            <p>You can now return to the bot and continue.</p>
            <button class="btn show" onclick="closeApp()">Close</button>
        </div>
        
        <div id="warning" class="hidden">
            <div class="status-icon">⚠️</div>
            <h1>Verification Issue</h1>
            <p>We detected a potential issue with your verification. You can still use the bot, but some features may be limited.</p>
            <button class="btn show" onclick="closeApp()">Close</button>
        </div>
        
        <div id="error" class="hidden">
            <div class="status-icon">❌</div>
            <h1>Verification Failed</h1>
            <p>Please try again or contact support if the issue persists.</p>
            <button class="btn show" onclick="retry()">Try Again</button>
        </div>
    </div>

    <script>
        const Telegram = window.Telegram.WebApp;
        Telegram.ready();
        Telegram.expand();
        
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id');
        const lang = urlParams.get('lang') || 'en';
        
        // Collect browser data
        function collectData() {
            // Canvas fingerprint
            let canvasFp = '';
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillRect(125, 1, 62, 20);
                ctx.fillStyle = '#069';
                ctx.fillText('Bot fingerprint 🔒', 2, 15);
                ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                ctx.fillText('Bot fingerprint 🔒', 4, 17);
                canvasFp = canvas.toDataURL();
            } catch(e) {
                canvasFp = 'error';
            }
            
            // WebGL renderer
            let webglRenderer = 'unavailable';
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl) {
                    const ext = gl.getExtension('WEBGL_debug_renderer_info');
                    if (ext) {
                        webglRenderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
                    }
                }
            } catch(e) {
                webglRenderer = 'error';
            }
            
            return {
                telegram_user_id: userId,
                init_data: Telegram.initData,
                user_agent: navigator.userAgent,
                screen: screen.width + 'x' + screen.height,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                canvas_fp: canvasFp,
                webgl_renderer: webglRenderer,
                language: navigator.language,
                platform: navigator.platform
            };
        }
        
        async function verify() {
            try {
                const data = collectData();
                
                const response = await fetch('/api/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                document.getElementById('loading').classList.add('hidden');
                
                if (result.status === 'ok') {
                    document.getElementById('success').classList.remove('hidden');
                } else if (result.status === 'flagged') {
                    document.getElementById('warning').classList.remove('hidden');
                } else {
                    document.getElementById('error').classList.remove('hidden');
                }
            } catch(e) {
                console.error('Verification error:', e);
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('error').classList.remove('hidden');
            }
        }
        
        function closeApp() {
            Telegram.close();
        }
        
        function retry() {
            location.reload();
        }
        
        // Start verification on load
        verify();
    </script>
</body>
</html>
"""


def validate_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """
    Validate Telegram WebApp initData.
    Uses HMAC-SHA256 to verify the data comes from Telegram.
    """
    try:
        # Parse the init data
        parsed = urllib.parse.parse_qs(init_data)
        
        # Get the hash
        received_hash = parsed.get('hash', [''])[0]
        if not received_hash:
            return False
        
        # Build the data check string
        data_check_arr = []
        for key, values in parsed.items():
            if key != 'hash':
                data_check_arr.append(f"{key}={values[0]}")
        
        data_check_arr.sort()
        data_check_string = '\n'.join(data_check_arr)
        
        # Calculate secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == received_hash
        
    except Exception as e:
        print(f"Init data validation error: {e}")
        return False


def create_fingerprint_hash(data: dict) -> str:
    """Create fingerprint hash from collected data."""
    components = [
        data.get('user_agent', ''),
        data.get('screen', ''),
        data.get('timezone', ''),
        data.get('canvas_fp', ''),
        data.get('webgl_renderer', ''),
        data.get('platform', '')
    ]
    combined = '|'.join(components)
    return hashlib.sha256(combined.encode()).hexdigest()


async def handle_index(request):
    """Serve the mini app HTML."""
    return web.Response(
        text=MINIAPP_HTML,
        content_type='text/html'
    )


async def handle_verify(request):
    """Handle verification request from mini app."""
    try:
        data = await request.json()
        
        # Validate Telegram init data
        init_data = data.get('init_data', '')
        if not validate_telegram_init_data(init_data, config.BOT_TOKEN):
            return web.json_response(
                {"status": "error", "message": "Invalid init data"},
                status=403
            )
        
        # Get user ID from init data
        parsed = urllib.parse.parse_qs(init_data)
        user_json = parsed.get('user', ['{}'])[0]
        import json
        user_data = json.loads(user_json)
        telegram_id = user_data.get('id')
        
        if not telegram_id:
            return web.json_response(
                {"status": "error", "message": "User ID not found"},
                status=400
            )
        
        # Get IP address
        ip_address = request.headers.get('X-Forwarded-For', request.remote)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # Create fingerprint
        fingerprint = create_fingerprint_hash(data)
        
        # Check for duplicates
        is_duplicate = False
        
        # Check if fingerprint exists for different user
        fingerprint_exists = await db.check_duplicate_fingerprint(telegram_id, fingerprint)
        if fingerprint_exists:
            is_duplicate = True
        
        # Check if IP is suspicious (3+ different users)
        ip_suspicious = await db.check_suspicious_ip(telegram_id, ip_address, threshold=3)
        if ip_suspicious:
            is_duplicate = True
        
        # Store session
        await db.create_miniapp_session(
            telegram_id=telegram_id,
            ip_address=ip_address,
            fingerprint=fingerprint,
            is_duplicate=is_duplicate
        )
        
        # Update user
        await db.update_miniapp_verified(
            telegram_id=telegram_id,
            verified=True,
            flagged=is_duplicate,
            ip=ip_address,
            fingerprint=fingerprint
        )
        
        return web.json_response({
            "status": "flagged" if is_duplicate else "ok",
            "duplicate": is_duplicate
        })
        
    except Exception as e:
        print(f"Verification error: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )


async def handle_health(request):
    """Health check endpoint for Railway."""
    return web.Response(text="ok")


async def start_miniapp_server():
    """Start the mini app server."""
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/miniapp', handle_index)
    app.router.add_post('/api/verify', handle_verify)
    app.router.add_post('/miniapp/api/verify', handle_verify)
    app.router.add_get('/health', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', config.MINIAPP_PORT)
    await site.start()
    
    print(f"Mini app server started on port {config.MINIAPP_PORT}")
    
    return runner
