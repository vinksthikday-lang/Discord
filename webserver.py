from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

HCAPTCHA_SITE_KEY = os.getenv('HCAPTCHA_SITE_KEY', 'f7e046de-b060-4aa8-9176-a826bdea13be')
HCAPTCHA_SECRET_KEY = os.getenv('HCAPTCHA_SECRET_KEY', 'ES_3b42d6a2578947ad9595c16fdac78c5d')

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

@app.route('/')
def index():
    return "KoalaHub Verification Server"

@app.route('/verify/<user_id>')
def verify_page(user_id):
    return render_template_string(VERIFY_TEMPLATE, site_key=HCAPTCHA_SITE_KEY, user_id=user_id)

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    token = data.get('token')
    user_id = data.get('user_id')

    resp = requests.post('https://hcaptcha.com/siteverify', data={
        'secret': HCAPTCHA_SECRET_KEY,
        'response': token
    })

    result = resp.json()
    if result.get('success'):
        print(f"✅ User {user_id} verified successfully.")
        return jsonify({"success": True})
    else:
        print(f"❌ Verification failed for user {user_id}: {result}")
        return jsonify({"success": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)