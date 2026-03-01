from flask import Flask, jsonify, request, send_file, render_template, url_for
from flask_cors import CORS  # Install with: pip install flask-cors
from captcha.image import ImageCaptcha
import random
import string
import base64
import io
import os

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

CURRENT_CAPTCHA = ""

# Ensure static directory exists
os.makedirs('static', exist_ok=True)  # Changed from templates to static

def generate_text():
    # Generate 5 random uppercase letters/numbers
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@app.route("/", methods=["GET"])
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route("/captcha", methods=["GET"])
def captcha():
    global CURRENT_CAPTCHA

    CURRENT_CAPTCHA = generate_text()
    print(f"Generated CAPTCHA: {CURRENT_CAPTCHA}")  # For debugging

    # Create captcha image
    image = ImageCaptcha(width=280, height=90)
    data = image.generate(CURRENT_CAPTCHA)
    
    # Save captcha image to static folder instead of templates
    captcha_path = os.path.join('static', 'captcha.png')  # Changed to static
    image.write(CURRENT_CAPTCHA, captcha_path)
    print(f"Captcha image saved to: {captcha_path}")
    
    # Convert to base64 for sending via JSON
    buffered = io.BytesIO()
    buffered.write(data.read())
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        "message": "Captcha generated",
        "debug_text": CURRENT_CAPTCHA,  # Remove this in production!
        "image": img_str,
        "saved_path": url_for('static', filename='captcha.png')  # Updated to use url_for
    })

@app.route("/verify", methods=["POST", "OPTIONS"])
def verify():
    if request.method == "OPTIONS":
        # Preflight request
        return jsonify({}), 200
        
    user_input = request.json.get("captcha")
    print(f"Verifying: {user_input} vs {CURRENT_CAPTCHA}")  # For debugging

    if user_input and user_input.upper() == CURRENT_CAPTCHA.upper():  # Case-insensitive comparison
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed"})

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"status": "Server is running!"})

@app.route("/captcha-image", methods=["GET"])
def serve_captcha_image():
    """Serve the saved captcha image from static folder"""
    captcha_path = os.path.join('static', 'captcha.png')  # Changed to static
    if os.path.exists(captcha_path):
        return send_file(captcha_path, mimetype='image/png')
    else:
        return jsonify({"error": "Captcha image not found"}), 404
    
if __name__ == "__main__":
    print("Starting Flask server...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)