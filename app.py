import os
from dotenv import load_dotenv

# Load environment variables from the .env file (if you need any other env vars)
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

# === Firebase Initialization with Embedded Credentials ===
firebase_creds = {
    "type": "service_account",
    "project_id": "chat-775-3df66",
    "private_key_id": "14727a9e1fe7cbbfd39a88f4226a08d3daa38bed",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3bTlogxwz5R0b\nlFn+Ifp94ee03NclyiUs+h5tPnxriWnq80g4tx0qZFkaFOeZ7bEGk132EZYtIbxL\n/1Ts8up+BZA8/fizrc/y3kvfcFV44x7oVIbCrlT3oczoXxhObAGaOMPGbQ0IqvYC\nlVUfe8SOgEtln4ojLA/ATBMX/QYdEnMpC58gg8jA5+ihwAGK368D7BkVvn41zMYh\nESwP5vFXcyZQ5XcUbqcX8WrfMYDLB3JyG24FrAc1ra5VO2wlHG0e5jtegrpNfFvC\nSSYCTkHDij9nVfgm7vuOyxtwxHCvE/h/P4yfOMk+mEXToYcnHmMDOcc2acO5tNQX\nGnXDOkkFAgMBAAECggEAAUNCuxSf++l5Xv279YhqruArFgR+hKzqFEUFMu+pr/HV\nEAAsa0YzcLMae+1QlNoyjEmKbY28cMNuhkAT58JaWT4U5UlC+OBa8fXpeXh5Vijg\nxxesin2PFISsIki5TvI7u+yPyHdquLhjPixPVt/6v+0OgnzBLjHOSp7GHjWoi52t\nu269KixFtVmuVWgx9P3hdzcRpD+noQjcldM/9G9pKm+KhGkJ60SkY7h4BrL1G/og\n9f9fwXY50RYZOtosXqfAc2Dm0OzfC3O8Vi31meKk/pdlyooQ0EGP2DCA9rPHmtB0\nzvrneK6wpWQEzxOOh2LS1sWcOhU0287zjPsPb4iDIQKBgQDxLYleONk2/tIGivTb\nGgAor7cMSUCxX+DLglnwu38cEnZSf05pPlQ3JFU1By9Eqb///KSFq9T3d2j6X+GK\nyRh8wG/hpFpz0LBzPQHvFBsGIIuagzDeko5IT4tWWO3dwd8jdj7Q1Kfk3JbHBX7l\nd2SR0/PKS2ru6HSXforptDSk9QKBgQDCsxW6GUGqFmjnzs9LN4+7bDVSCF/8S/Mx\nXUXHSEhIu0V7zU17LIFVjMx9bqrd4Zfd0XrUlZ5ZzaL/pFweXAp/qaJncYQelbLH\nL4ZSidEjSwL3ZEX/xMYFkbSSMTvfeYNZkDYZLUy1zwuwrxkdan1y2DQdb1YOx7Zv\nInmPUMcJ0QKBgQDHXYwjbjzpAEZfkDiOcfTVrUNUja1Dsu0hbbSpkmSlsQFMet43\nk4WMO6WP+0twqB4GHzNlKEEY/AW0itPnpQpv/ae+z9zRxh5GdJUHrAgWzYp5hJ8+\nLcoeLlsRWtvup5esOc/9Uv0i69Jb3MgkKcjh32K0xBk2OsQ+gyWTwRqPjQKBgFVF\nl+t0qlSzEekMo69euz2ry8KM1nUqUm25WxlHqBjqpCjvptKekFqGmv0Inh8lcZz9\n5Rz8FmlgbdYnBw1o5FQ7WFyT0/iNOcqRHvRBVe5uKPNu4FV/ufawdPReScm7b3Kn\nfXoTY/hwoL8WQRqoDB9jX5fQrlE02Mrdv32sNDAxAoGBAOBFu/PBIwNc6CGaD0PH\neEOJGP4NEmGCw0EpWpxafq+Ujtx9BaMw+tGnG8rvFc6EY4OfxTWzFIICEP96gBMB\nhbVp6ghpW6PVZskNeQNP9GtQhWwMU9/sZvBoCerUyw38eWrbnTBnDmYg/R9CMFnY\noE8SzMciACBFWvpWUhie+jK+\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@chat-775-3df66.iam.gserviceaccount.com",
    "client_id": "113138351792368259292",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40chat-775-3df66.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

cred = credentials.Certificate(firebase_creds)
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
        return jsonify({"error": str(e)}), 400

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
    # Add seen status fields: default seen false, no seen_time
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

# Mark a message as seen (new endpoint)
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
    app.run(debug=True)
