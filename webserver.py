import os
from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

HCAPTCHA_SITE_KEY = os.getenv('HCAPTCHA_SITE_KEY', 'f7e046de-b060-4aa8-9176-a826bdea13be')
HCAPTCHA_SECRET_KEY = os.getenv('HCAPTCHA_SECRET_KEY', 'ES_3b42d6a2578947ad95c16fdac78c5d')
DISCORD_BOT_WEBHOOK_URL = os.getenv('DISCORD_BOT_WEBHOOK_URL', '')  # ← New!

@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def index():
    return "KoalaHub Verification Server is running."

@app.route('/verify/<user_id>')
def verify_page(user_id):
    VERIFY_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verify Human</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background: #f0f2f5; }
            .container { max-width: 500px; margin: 0 auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h2 { color: #5865F2; }
            button { margin-top: 20px; padding: 10px 20px; background: #5865F2; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:disabled { background: #b9bbbe; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔒 Verify You're Human</h2>
            <p>To protect this service, please complete the challenge.</p>
            <div class="h-captcha" data-sitekey="{{ site_key }}"></div>
            <button id="submit" disabled>Submit</button>
        </div>

        <script>
            document.querySelector('.h-captcha').addEventListener('verify', function(token) {
                document.getElementById('submit').disabled = false;
                document.getElementById('submit').onclick = function() {
                    fetch('/verify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: token, user_id: "{{ user_id }}" })
                    }).then(r => r.json()).then(data => {
                        if (data.success) {
                            alert("✅ Verified! Return to Discord.");
                            window.close();
                        } else {
                            alert("❌ Verification failed. Try again.");
                        }
                    });
                };
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(VERIFY_TEMPLATE, site_key=HCAPTCHA_SITE_KEY, user_id=user_id)

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False}), 400

        token = data.get('token')
        user_id = data.get('user_id')

        if not token or not user_id:
            return jsonify({"success": False}), 400

        # Validate with hCaptcha
        resp = requests.post('https://hcaptcha.com/siteverify', data={
            'secret': HCAPTCHA_SECRET_KEY,
            'response': token
        }, timeout=10)

        result = resp.json()
        if result.get('success'):
            print(f"✅ User {user_id} verified successfully.")
            
            # 🔑 SEND WEBHOOK TO DISCORD BOT
            if DISCORD_BOT_WEBHOOK_URL:
                try:
                    webhook_data = {"user_id": str(user_id), "verified": True}
                    requests.post(DISCORD_BOT_WEBHOOK_URL, json=webhook_data, timeout=5)
                    print(f"📤 Webhook sent to bot for user {user_id}")
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