import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from instagrapi import Client

app = Flask(__name__)
CORS(app)

SESSION_FILE = "instagram_session.json"
cl = Client()

def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            print("[+] Loaded existing session")
            return True
        except:
            return False
    return False

def save_session():
    try:
        cl.dump_settings(SESSION_FILE)
        print("[+] Session saved")
        return True
    except:
        return False

if load_session():
    try:
        cl.user_id
        print("[+] Session valid, logged in as", cl.username)
    except:
        print("[!] Session invalid, will need login")
else:
    print("[!] No session file. Use /login endpoint first.")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "logged_in": cl.user_id is not None
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400
    
    try:
        cl.login(username, password)
        save_session()
        return jsonify({
            "status": "ok",
            "user_id": cl.user_id,
            "username": cl.username
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/search', methods=['GET'])
def search():
    if not cl.user_id:
        return jsonify({"error": "Not logged in. Call /login first"}), 401
    
    keyword = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not keyword:
        return jsonify({"error": "Missing search query"}), 400
    
    try:
        medias = cl.hashtag_medias_recent(keyword.replace(' ', ''), amount=limit)
        results = []
        for m in medias:
            results.append({
                "username": m.user.username,
                "full_name": m.user.full_name,
                "follower_count": m.user.follower_count,
                "is_private": m.user.is_private,
                "has_website": bool(m.user.external_url),
            })
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-dm', methods=['POST'])
def send_dm():
    if not cl.user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    username = data.get('username')
    message = data.get('message')
    
    if not username or not message:
        return jsonify({"error": "Missing username or message"}), 400
    
    try:
        user_id = cl.user_id_from_username(username)
        cl.direct_send(message, [user_id])
        return jsonify({"success": True, "message": f"DM sent to {username}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
