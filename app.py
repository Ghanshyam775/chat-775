import os
import json
from dotenv import load_dotenv

# Load environment variables from the .env file (if present)
load_dotenv()

from flask import (
    Flask, request, jsonify, render_template,
    redirect, url_for, send_from_directory
)
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
from werkzeug.utils import secure_filename

app = Flask(__name__)

# === Configuration for File Uploads ===
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# === Firebase Initialization ===
# Try to load the Firebase service account JSON from an environment variable.
firebase_key_json = os.environ.get("FIREBASE_KEY_JSON")

if firebase_key_json:
    try:
        firebase_creds = json.loads(firebase_key_json)
        # Ensure the private key is correctly formatted:
        if "private_key" in firebase_creds:
            firebase_creds["private_key"] = firebase_creds["private_key"].replace('\\n', '\n')
        cred = credentials.Certificate(firebase_creds)
    except json.JSONDecodeError as e:
        raise Exception("Invalid JSON in FIREBASE_KEY_JSON environment variable: " + str(e))
else:
    # Fallback: use Application Default Credentials.
    # Make sure the environment variable GOOGLE_APPLICATION_CREDENTIALS is set
    # to the path of your Firebase service account JSON file.
    try:
        cred = credentials.ApplicationDefault()
    except Exception as e:
        raise Exception("No Firebase credentials found. Set FIREBASE_KEY_JSON or GOOGLE_APPLICATION_CREDENTIALS. " + str(e))

firebase_admin.initialize_app(cred)
db = firestore.client()

# === Routes for Rendering Templates ===
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/account')
def account():
    return render_template('account.html')

# Serve uploaded files (e.g., media and profile images)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# === API Endpoints ===

# Register a new user (store extra info in Firestore)
@app.route('/api/register', methods=['POST'])
def register_api():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")
    if not email or not password or not username:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        user = auth.create_user(email=email, password=password)
        db.collection("users").document(user.uid).set({
            "username": username,
            "email": email,
            "active": False,
            "profile_image_url": ""
        })
        return jsonify({"message": "User registered", "uid": user.uid}), 200
    except Exception as e:
        return jsonify({"error": "Registration error: " + str(e)}), 400

# Get registered users (for dynamic contacts list)
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users_ref = db.collection("users")
        users_docs = users_ref.stream()
        users = []
        for doc in users_docs:
            user_data = doc.to_dict()
            user_data["uid"] = doc.id
            users.append(user_data)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Update account information (username and profile image URL)
@app.route('/api/account/update', methods=['POST'])
def account_update():
    data = request.get_json()
    uid = data.get("uid")
    username = data.get("username")
    profile_image_url = data.get("profile_image_url", "")
    if not uid or not username:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        db.collection("users").document(uid).update({
            "username": username,
            "profile_image_url": profile_image_url
        })
        return jsonify({"message": "Account updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Set active status for a user (true/false)
@app.route('/api/set_active', methods=['POST'])
def set_active():
    data = request.get_json()
    uid = data.get("uid")
    active = data.get("active", False)
    if not uid:
        return jsonify({"error": "Missing uid"}), 400
    try:
        db.collection("users").document(uid).update({
            "active": active
        })
        return jsonify({"message": "Active status updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Send a message (text and/or media)
@app.route('/api/send', methods=['POST'])
def send_message():
    data = request.get_json()
    chat_id = data.get("chatId", "default_chat")
    message = {
        "senderId": data.get("senderId"),
        "text": data.get("text", ""),
        "media_url": data.get("media_url", ""),
        "timestamp": SERVER_TIMESTAMP,
        "deleted": False,
        "reactions": {},
        "seen": False,
        "seen_time": None
    }
    try:
        db.collection("chats").document(chat_id).collection("messages").add(message)
        return jsonify({"message": "Message sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Mark a message as seen
@app.route('/api/mark_seen', methods=['POST'])
def mark_seen():
    data = request.get_json()
    chat_id = data.get("chatId", "default_chat")
    message_id = data.get("messageId")
    if not chat_id or not message_id:
        return jsonify({"error": "Missing chatId or messageId"}), 400
    try:
        db.collection("chats").document(chat_id).collection("messages").document(message_id).update({
            "seen": True,
            "seen_time": SERVER_TIMESTAMP
        })
        return jsonify({"message": "Message marked as seen"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete a single message (soft-delete)
@app.route('/api/delete', methods=['POST'])
def delete_message():
    data = request.get_json()
    chat_id = data.get("chatId", "default_chat")
    message_id = data.get("messageId")
    try:
        db.collection("chats").document(chat_id).collection("messages").document(message_id).update({"deleted": True})
        return jsonify({"message": "Message deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete entire chat (all messages)
@app.route('/api/delete_chat', methods=['POST'])
def delete_chat():
    data = request.get_json()
    chat_id = data.get("chatId")
    if not chat_id:
        return jsonify({"error": "Missing chatId"}), 400
    try:
        messages_ref = db.collection("chats").document(chat_id).collection("messages")
        for doc in messages_ref.stream():
            doc.reference.delete()
        return jsonify({"message": "Chat deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Forward a message
@app.route('/api/forward', methods=['POST'])
def forward_message():
    data = request.get_json()
    original_chat_id = data.get("originalChatId", "default_chat")
    message_id = data.get("messageId")
    target_chat_id = data.get("target_chat_id", "default_chat")
    try:
        orig_message = db.collection("chats").document(original_chat_id).collection("messages").document(message_id).get().to_dict()
        if not orig_message:
            return jsonify({"error": "Message not found"}), 404
        orig_message.pop("timestamp", None)
        orig_message["timestamp"] = SERVER_TIMESTAMP
        db.collection("chats").document(target_chat_id).collection("messages").add(orig_message)
        return jsonify({"message": "Message forwarded"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# React to a message (update the reactions map)
@app.route('/api/react', methods=['POST'])
def react_message():
    data = request.get_json()
    chat_id = data.get("chatId", "default_chat")
    message_id = data.get("messageId")
    user_id = data.get("userId")
    reaction = data.get("reaction")
    try:
        db.collection("chats").document(chat_id).collection("messages").document(message_id).update({
            f"reactions.{user_id}": reaction
        })
        return jsonify({"message": "Reaction added"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Upload media file (for profile images or chat attachments)
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_url = url_for('uploaded_file', filename=filename, _external=True)
        return jsonify({"message": "File uploaded", "file_url": file_url}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

