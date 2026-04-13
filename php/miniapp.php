<?php
/**
 * Mini App for VPS deployment
 * Anti-farming verification web app
 */

// Load environment config
require_once __DIR__ . '/config.php';

?>
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
                
                const response = await fetch('verify.php', {
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
