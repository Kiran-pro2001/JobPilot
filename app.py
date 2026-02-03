from flask import Flask, request, jsonify, send_from_directory
import os
import json
import certifi

# --- FIX: SSL Certificate Path Error on Hostinger ---
# This overrides the stale 'jobpilot' path with the correct current path
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
# ----------------------------------------------------

from backend_parser import extract_text_from_pdf, analyze_resume_with_openai
from apply_bot import run_application_bot
from linkedin_bot import run_linkedin_bot
from logger import clear_logs, log

app = Flask(__name__)

@app.route("/health")
def health():
    return {
        "status": "ok",
        "env_loaded": bool(os.getenv("OPENAI_API_KEY"))
    }


# 1. Serve the Frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# 2. Handle the Upload
@app.route('/api/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save temporarily so PyPDF2 can read it
        # Hackathon: Save as 'latest_resume.pdf' so the bot can find it easily
        resume_path = "latest_resume.pdf"
        file.save(resume_path)

        try:
            # Run your existing AI logic
            text = extract_text_from_pdf(resume_path)
            
            if text:
                data = analyze_resume_with_openai(text)
                
                # Preserve existing user stats (application count & premium status)
                if os.path.exists('user_data.json'):
                    with open('user_data.json', 'r') as f:
                        old_data = json.load(f)
                        data['application_count'] = old_data.get('application_count', 0)
                        data['is_premium'] = old_data.get('is_premium', False)
                else:
                    data['application_count'] = 0
                    data['is_premium'] = False

                # Hackathon: Save the extracted data to a file for the bot
                with open('user_data.json', 'w') as f:
                    json.dump(data, f, indent=4)

                # --- DEBUG: Print what AI found to the terminal ---
                print("\n🔍 DEBUG: AI Parsed Data:", data)
                print("-" * 50)
                # --------------------------------------------------
                
                if data:
                    return jsonify(data)
                else:
                    return jsonify({"error": "AI returned no data"}), 500
            else:
                # os.remove(resume_path) # Keep file for debugging/bot
                return jsonify({"error": "Could not extract text"}), 500

        except Exception as e:
            # if os.path.exists(resume_path):
            #     os.remove(resume_path)
            return jsonify({"error": str(e)}), 500

# 3. Trigger Auto-Apply Bot
@app.route('/api/auto-apply', methods=['POST'])
def auto_apply():
    log("➡️ API Request: /api/auto-apply received")
    try:
        clear_logs()
        run_application_bot()
        return jsonify({"message": "Bot finished successfully"})
    except Exception as e:
        log(f"❌ API Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 4. LinkedIn Auto-Apply Endpoint
@app.route('/api/linkedin-apply', methods=['POST'])
def linkedin_apply():
    log("➡️ API Request: /api/linkedin-apply received")
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Credentials required"}), 400

    if os.path.exists("stop_signal.txt"):
        os.remove("stop_signal.txt")

    try:
        clear_logs()
        log("🔄 Starting LinkedIn Bot process...")
        run_linkedin_bot(email, password)
        return jsonify({"message": "LinkedIn Pilot finished batch"})
    except Exception as e:
        log(f"❌ API Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 6. Verify Payment Endpoint
@app.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    if os.path.exists('user_data.json'):
        with open('user_data.json', 'r') as f:
            data = json.load(f)
        
        data['is_premium'] = True
        
        with open('user_data.json', 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"message": "Payment verified! Premium access granted."})
    return jsonify({"error": "User data not found"}), 404

# 5. Stop Bot Endpoint
@app.route('/api/stop-bot', methods=['POST'])
def stop_bot():
    with open("stop_signal.txt", "w") as f:
        f.write("stop")
    return jsonify({"message": "Stop signal sent. Bot will halt after current action."})

# 4. Get Application History
@app.route('/api/history', methods=['GET', 'DELETE'])
def manage_history():
    if request.method == 'DELETE':
        try:
            with open('application_history.json', 'w') as f:
                json.dump([], f)
            return jsonify({"message": "History cleared"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if os.path.exists('application_history.json'):
        with open('application_history.json', 'r') as f:
            try:
                return jsonify(json.load(f))
            except:
                return jsonify([])
    return jsonify([])

# 7. Contact Form Endpoint
@app.route('/api/contact', methods=['POST'])
def contact_support():
    data = request.json
    print("\n📧 NEW SUPPORT MESSAGE:")
    print(f"From: {data.get('name')} <{data.get('email')}>")
    print(f"Message: {data.get('message')}")
    print("-" * 30)
    return jsonify({"message": "Message sent successfully! We'll get back to you shortly."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    
    # --- Startup Diagnostics ---
    print("-" * 50)
    print(f"🚀 ApplyNinja Server Running on port {port}")
    
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OPENAI_API_KEY found.")
    else:
        print("⚠️  OPENAI_API_KEY NOT found! AI features will fail.")
        
    print("-" * 50)
    # ---------------------------
    
    app.run(host='0.0.0.0', port=port, debug=False)
