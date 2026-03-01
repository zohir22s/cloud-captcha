from flask import Flask, jsonify, request, send_file, render_template, url_for
from flask_cors import CORS
from captcha.image import ImageCaptcha
import random
import string
import base64
import io
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

CURRENT_CAPTCHA = ""

# Get access token from environment variable (set in Render Dashboard)
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', 'default-insecure-token-change-me')

# Decorator to check authentication
def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "No authorization token provided"}), 401
        
        # Expected format: "Bearer <token>"
        try:
            token_type, token = auth_header.split()
            if token_type.lower() != 'bearer':
                return jsonify({"error": "Invalid token type. Use Bearer"}), 401
        except ValueError:
            return jsonify({"error": "Invalid authorization header format"}), 401
        
        if token != ACCESS_TOKEN:
            return jsonify({"error": "Invalid access token"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Ensure static directory exists
os.makedirs('static', exist_ok=True)

def generate_text():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@app.route("/", methods=["GET"])
def index():
    """Serve the main HTML page - no token required for the page itself"""
    return render_template('index.html')

@app.route("/captcha", methods=["GET"])
@require_token  # Protect this route
def captcha():
    global CURRENT_CAPTCHA
    CURRENT_CAPTCHA = generate_text()
    print(f"Generated CAPTCHA: {CURRENT_CAPTCHA}")

    image = ImageCaptcha(width=280, height=90)
    data = image.generate(CURRENT_CAPTCHA)
    
    captcha_path = os.path.join('static', 'captcha.png')
    image.write(CURRENT_CAPTCHA, captcha_path)
    
    buffered = io.BytesIO()
    buffered.write(data.read())
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        "message": "Captcha generated",
        "image": img_str,
        "saved_path": url_for('static', filename='captcha.png')
    })

@app.route("/verify", methods=["POST", "OPTIONS"])
@require_token  # Protect this route
def verify():
    if request.method == "OPTIONS":
        return jsonify({}), 200
        
    user_input = request.json.get("captcha")
    print(f"Verifying: {user_input} vs {CURRENT_CAPTCHA}")

    if user_input and user_input.upper() == CURRENT_CAPTCHA.upper():
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed"})

@app.route("/test", methods=["GET"])
@require_token  # Protect this route
def test():
    return jsonify({"status": "Server is running with authentication!"})

@app.route("/captcha-image", methods=["GET"])
@require_token  # Protect this route
def serve_captcha_image():
    captcha_path = os.path.join('static', 'captcha.png')
    if os.path.exists(captcha_path):
        return send_file(captcha_path, mimetype='image/png')
    else:
        return jsonify({"error": "Captcha image not found"}), 404

if __name__ == "__main__":
    print("Starting Flask server...")
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)