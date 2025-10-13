import os
from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

HCAPTCHA_SITE_KEY = os.getenv('HCAPTCHA_SITE_KEY', '24446f26-30f4-43e4-8756-185c5426fcba')
HCAPTCHA_SECRET_KEY = os.getenv('HCAPTCHA_SECRET_KEY', 'ES_3b42d6a2578947ad95c16fdac78c5d')
WEBHOOK_URL = os.getenv('DISCORD_BOT_WEBHOOK_URL', '')

@app.route('/health')
def health():
    return "OK", 200

@app.route('/verify/<user_id>')
def verify_page(user_id):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>KoalaHub Verification</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
        <style>
            body {{ 
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                            url('https://cdn.corenexis.com/files/b/7465723168.png') center/cover no-repeat fixed;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                color: white;
            }}
            .container {{ 
                background: rgba(30, 30, 40, 0.85);
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                text-align: center;
                max-width: 500px;
                width: 90%;
                backdrop-filter: blur(10px);
            }}
            h2 {{ 
                color: #4ade80; 
                margin-top: 0;
                font-size: 28px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            p {{ 
                color: #e2e8f0; 
                margin-bottom: 25px;
                font-size: 16px;
            }}
            button {{ 
                margin-top: 20px; 
                padding: 12px 24px; 
                background: #5865F2; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 16px;
                transition: background 0.3s;
            }}
            button:hover:not(:disabled) {{ 
                background: #4752c4; 
            }}
            button:disabled {{ 
                background: #64748b; 
                cursor: not-allowed; 
            }}
            .logo {{ 
                font-size: 48px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🐨</div>
            <h2>KoalaHub Security Check</h2>
            <p>Please verify you're human to protect our service.</p>
            <div class="h-captcha" data-sitekey="{HCAPTCHA_SITE_KEY}" data-callback="onVerify"></div>
            <button id="submit" disabled>Submit Verification</button>
        </div>

        <script>
            function onVerify(token) {{
                console.log("hCaptcha solved!");
                document.getElementById('submit').disabled = false;
                setTimeout(() => {{
                    submitVerification(token);
                }}, 1000);
            }}
            
            function submitVerification(token) {{
                fetch('/verify', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ 
                        token: token, 
                        user_id: "{user_id}" 
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert("✅ Verified! Return to Discord.");
                        window.close();
                    }} else {{
                        alert("❌ Verification failed. Try again.");
                    }}
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    alert("⚠️ Network error. Try again.");
                }});
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        if not data:  # ✅ FIXED: was "if not"
            return jsonify({"success": False}), 400

        token = data.get('token')
        user_id = data.get('user_id')

        if not token or not user_id:
            return jsonify({"success": False}), 400

        resp = requests.post('https://hcaptcha.com/siteverify', data={
            'secret': HCAPTCHA_SECRET_KEY,
            'response': token
        }, timeout=10)

        result = resp.json()
        if result.get('success'):
            print(f"✅ User {user_id} verified successfully.")
            
            if WEBHOOK_URL:
                try:
                    webhook_data = {"type": "verification", "user_id": str(user_id)}
                    requests.post(WEBHOOK_URL, json=webhook_data, timeout=5)
                    print(f"📤 Webhook sent for user {user_id}")
                except Exception as e:
                    print(f"⚠️ Webhook failed: {e}")
            
            return jsonify({"success": True})
        else:
            print(f"❌ Verification failed for user {user_id}: {result}")
            return jsonify({"success": False}), 403

    except Exception as e:
        print(f"⚠️ Verification error: {e}")
        return jsonify({"success": False}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)