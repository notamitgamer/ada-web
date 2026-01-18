import os
import json
import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth, firestore

# --- INIT APP & CONFIG ---
app = Flask(__name__)
# Allow CORS for your domain and localhost for testing
CORS(app, resources={r"/api/*": {"origins": [
    "https://ada.amit.is-a.dev", 
    "https://amit.is-a.dev", 
    "http://127.0.0.1:5500", 
    "http://localhost:5000",
    "http://localhost:5500"
]}})

# 1. Firebase Admin Init (Server-Side Security)
# Ensure you have your service account json or environment variables set up in Render
# For Render/Cloud, credentials.ApplicationDefault() often works if env vars are correct.
# Otherwise, use a service account JSON file.
try:
    if not firebase_admin._apps:
        # Check for FIREBASE_CREDENTIALS environment variable (JSON string)
        firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
        
        if firebase_creds_json:
            # Parse JSON string from environment variable
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            print("✅ Using Firebase credentials from FIREBASE_CREDENTIALS environment variable")
        elif os.path.exists("firebase-adminsdk.json"):
            cred = credentials.Certificate("firebase-adminsdk.json")
            print("✅ Using Firebase credentials from firebase-adminsdk.json file")
        else:
            # Try application default credentials
            cred = credentials.ApplicationDefault()
            print("✅ Using Firebase Application Default Credentials")
        
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized successfully")
    db = firestore.client()
    print("✅ Firestore client initialized successfully")
except Exception as e:
    print(f"❌ Firebase initialization error: {type(e).__name__}: {e}")
    print("⚠️  API will run but Firestore features will not work")
    db = None

# 2. Gemini Init
GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GENAI_API_KEY:
    print("CRITICAL: GEMINI_API_KEY not found in env variables.")
else:
    genai.configure(api_key=GENAI_API_KEY)

# Generation Config
generation_config = {
    "temperature": 0.2, # Low temp for precise coding
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# System Instruction - THE STRICT CODING GATEKEEPER
SYSTEM_PROMPT = """
You are 'Ada', a highly specialized Coding Assistant created by Amit Dutta.

STRICT RULES:
1. You ONLY answer questions related to Computer Science, Programming, Code Debugging, Rewrite, or Generation.
2. If a user asks anything else (e.g., "How to cook pasta?", "Who is the president?"), politely REFUSE: "I am designed only for coding tasks."
3. FORMAT YOUR RESPONSE STRICTLY:
   - Provide a helpful text explanation in Markdown format.
   - If you generate, fix, or show code, place the FINAL COMPLETE CODE inside a special block:
     <<<CODE_START>>>
     (put the raw code here)
     <<<CODE_END>>>
   - Do NOT use standard markdown code fences (```) for the main code solution that belongs in the editor. You MAY use small inline code ticks `like this` in the explanation text.
   - If the user provides a file or code context, USE IT.
"""

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash-preview-09-2025",
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT,
)

# --- HELPER: Verify Firebase Token ---
def verify_token(auth_header):
    """
    Verifies the Firebase ID Token sent from the client.
    Returns user_uid if valid, None otherwise.
    Enhanced with better error messages and logging.
    """
    if not auth_header:
        print("❌ No Authorization header provided")
        return None
    
    if not auth_header.startswith("Bearer "):
        print("❌ Invalid Authorization header format (must start with 'Bearer ')")
        return None
    
    token = auth_header.split("Bearer ")[1]
    
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        # print(f"✅ Token verified for user: {user_id}") # verbose
        return user_id
    except auth.InvalidIdTokenError:
        print("❌ Invalid ID token - token is malformed or invalid")
        return None
    except auth.ExpiredIdTokenError:
        print("❌ Token has expired - user needs to refresh their token")
        return None
    except auth.RevokedIdTokenError:
        print("❌ Token has been revoked")
        return None
    except Exception as e:
        print(f"❌ Token verification error: {type(e).__name__}: {e}")
        return None

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Ada AI Coding Backend",
        "version": "1.0.0",
        "model": "gemini-2.5-flash-preview-09-2025"
    })

@app.route('/health')
def health():
    """Health check endpoint for UptimeRobot and monitoring services"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })

@app.route('/api/generate-title', methods=['POST'])
def generate_title():
    """Generates a short 3-5 word title for the chat history."""
    # Verify auth even for titles to prevent abuse
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({
            "error": "Unauthorized",
            "message": "Invalid or missing authentication token. Please sign in again."
        }), 401

    data = request.json
    message = data.get('message', '')
    
    try:
        title_model = genai.GenerativeModel("models/gemini-2.5-flash-preview-09-2025")
        res = title_model.generate_content(f"Summarize this coding query into a 3-5 word title: '{message}'")
        return jsonify({"title": res.text.strip()})
    except Exception as e:
        print(f"❌ Error generating title: {type(e).__name__}: {e}")
        return jsonify({"title": "New Chat"})

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get user profile from Firestore."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        user_ref = db.collection('users').document(user_uid)
        doc = user_ref.get()
        
        if doc.exists:
            return jsonify(doc.to_dict())
        else:
            # Create default profile
            default_profile = {
                "uid": user_uid,
                "displayName": "",
                "email": "",
                "photoURL": "",
                "age": "",
                "location": "",
                "bio": "",
                "totalChats": 0,
                "totalMessages": 0,
                "totalCodeSnippets": 0,
                "theme": "dark",
                "codeTheme": "dracula",
                "fontSize": 13,
                "createdAt": datetime.datetime.now(datetime.timezone.utc)
            }
            user_ref.set(default_profile)
            return jsonify(default_profile)
    except Exception as e:
        print(f"❌ Error getting profile: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to get profile"}), 500

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update user profile in Firestore."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        data = request.json
        allowed_fields = ['displayName', 'age', 'location', 'bio', 'photoURL', 'theme', 'codeTheme', 'fontSize']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        update_data['updatedAt'] = datetime.datetime.now(datetime.timezone.utc)
        
        user_ref = db.collection('users').document(user_uid)
        user_ref.update(update_data)
        
        return jsonify({"success": True, "message": "Profile updated"})
    except Exception as e:
        print(f"❌ Error updating profile: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to update profile"}), 500

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all user's chat sessions from Firestore."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        chats_ref = db.collection('users').document(user_uid).collection('chats')
        # Order by updatedAt descending (most recent first)
        docs = chats_ref.order_by('updatedAt', direction='DESCENDING').stream()
        
        chats = []
        for doc in docs:
            chat_data = doc.to_dict()
            chat_data['id'] = doc.id
            # Only send metadata, not full messages
            chats.append({
                'id': chat_data.get('id'),
                'title': chat_data.get('title', 'New Chat'),
                'createdAt': chat_data.get('createdAt'),
                'updatedAt': chat_data.get('updatedAt'),
                'isPinned': chat_data.get('isPinned', False),
                'messageCount': len(chat_data.get('messages', []))
            })
        
        return jsonify({"chats": chats})
    except Exception as e:
        print(f"❌ Error getting chats: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to get chats"}), 500

@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get specific chat session."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        chat_ref = db.collection('users').document(user_uid).collection('chats').document(chat_id)
        doc = chat_ref.get()
        
        if not doc.exists:
            return jsonify({"error": "Chat not found"}), 404
        
        chat_data = doc.to_dict()
        chat_data['id'] = doc.id
        return jsonify(chat_data)
    except Exception as e:
        print(f"❌ Error getting chat: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to get chat"}), 500

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat session."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        chat_ref = db.collection('users').document(user_uid).collection('chats').document(chat_id)
        chat_ref.delete()
        return jsonify({"success": True, "message": "Chat deleted"})
    except Exception as e:
        print(f"❌ Error deleting chat: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to delete chat"}), 500

@app.route('/api/chats/<chat_id>/rename', methods=['PUT'])
def rename_chat(chat_id):
    """Rename a chat session."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        data = request.json
        new_title = data.get('title', 'New Chat')
        
        chat_ref = db.collection('users').document(user_uid).collection('chats').document(chat_id)
        chat_ref.update({
            'title': new_title,
            'updatedAt': datetime.datetime.now(datetime.timezone.utc)
        })
        
        return jsonify({"success": True, "message": "Chat renamed"})
    except Exception as e:
        print(f"❌ Error renaming chat: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to rename chat"}), 500

@app.route('/api/chats/<chat_id>/export', methods=['GET'])
def export_chat(chat_id):
    """Export chat as JSON."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        chat_ref = db.collection('users').document(user_uid).collection('chats').document(chat_id)
        doc = chat_ref.get()
        
        if not doc.exists:
            return jsonify({"error": "Chat not found"}), 404
        
        chat_data = doc.to_dict()
        chat_data['id'] = doc.id
        
        # Convert timestamps to ISO format for JSON serialization
        if 'createdAt' in chat_data:
            chat_data['createdAt'] = chat_data['createdAt'].isoformat() if hasattr(chat_data['createdAt'], 'isoformat') else str(chat_data['createdAt'])
        if 'updatedAt' in chat_data:
            chat_data['updatedAt'] = chat_data['updatedAt'].isoformat() if hasattr(chat_data['updatedAt'], 'isoformat') else str(chat_data['updatedAt'])
        
        for msg in chat_data.get('messages', []):
            if 'timestamp' in msg:
                msg['timestamp'] = msg['timestamp'].isoformat() if hasattr(msg['timestamp'], 'isoformat') else str(msg['timestamp'])
        
        return jsonify(chat_data)
    except Exception as e:
        print(f"❌ Error exporting chat: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to export chat"}), 500

@app.route('/api/chats/<chat_id>/pin', methods=['PUT'])
def pin_chat(chat_id):
    """Toggle pin status of a chat."""
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        data = request.json
        is_pinned = data.get('isPinned', False)
        
        chat_ref = db.collection('users').document(user_uid).collection('chats').document(chat_id)
        chat_ref.update({
            'isPinned': is_pinned,
            'updatedAt': datetime.datetime.now(datetime.timezone.utc)
        })
        
        return jsonify({"success": True, "isPinned": is_pinned})
    except Exception as e:
        print(f"❌ Error pinning chat: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to pin chat"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main Chat Endpoint (Streaming).
    Headers: Authorization: Bearer <firebase_id_token>
    Body: { "message": str, "history": list, "codeContext": str, "fileContext": str, "sessionId": str }
    """
    # 1. Verify User
    user_uid = verify_token(request.headers.get('Authorization'))
    if not user_uid:
        return jsonify({
            "error": "Unauthorized",
            "message": "Invalid or missing authentication token. Please sign in again."
        }), 401

    data = request.json
    user_msg = data.get('message')
    history = data.get('history', []) 
    code_ctx = data.get('codeContext', '') 
    file_ctx = data.get('fileContext', '') 
    session_id = data.get('sessionId')

    if not user_msg:
        return jsonify({
            "error": "Bad Request",
            "message": "Message cannot be empty"
        }), 400

    # 2. Construct Prompt with Context
    context_str = ""
    if code_ctx:
        context_str += f"\n\n[CURRENT EDITOR CONTENT]:\n{code_ctx}\n"
    if file_ctx:
        # Handle both string and object formats
        if isinstance(file_ctx, dict):
            file_name = file_ctx.get('name', 'uploaded_file')
            file_content = file_ctx.get('content', '')
            context_str += f"\n\n[UPLOADED FILE: {file_name}]:\n{file_content}\n"
        else:
            context_str += f"\n\n[UPLOADED FILE CONTENT]:\n{file_ctx}\n"
    
    # Add History (Gemini format)
    chat_history = []
    for turn in history:
        # Gemini expects 'user' and 'model' roles
        chat_history.append({"role": "user", "parts": [turn.get('user', '')]})
        chat_history.append({"role": "model", "parts": [turn.get('model', '')]})
    
    try:
        chat_session = model.start_chat(history=chat_history)
    except Exception as e:
        print(f"❌ Error starting chat session: {type(e).__name__}: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to initialize chat session"
        }), 500

    # 3. Stream Response
    def generate():
        final_text_acc = ""
        
        prompt_with_ctx = user_msg + context_str
        
        try:
            response = chat_session.send_message(prompt_with_ctx, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    final_text_acc += chunk.text
            
            # 4. Save Interaction to Firestore
            # We save this asynchronously (conceptually) after streaming is done.
            if session_id and db:
                try:
                    doc_ref = db.collection('users').document(user_uid).collection('chats').document(session_id)
                    
                    msg_data = {
                        "role": "user",
                        "content": user_msg,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc)
                    }
                    
                    # We store the raw AI response. The client parses the code blocks.
                    ai_data = {
                        "role": "model",
                        "content": final_text_acc, 
                        "timestamp": datetime.datetime.now(datetime.timezone.utc)
                    }
                    
                    doc = doc_ref.get()
                    if not doc.exists:
                        # First message - generate title
                        chat_title = "New Chat"
                        try:
                            title_model = genai.GenerativeModel("models/gemini-2.5-flash-preview-09-2025")
                            title_response = title_model.generate_content(f"Summarize this coding query into a 3-5 word title: '{user_msg}'")
                            chat_title = title_response.text.strip()
                        except Exception as title_err:
                            print(f"⚠️  Title generation failed: {title_err}")
                        
                        doc_ref.set({
                            "title": chat_title,
                            "createdAt": datetime.datetime.now(datetime.timezone.utc),
                            "updatedAt": datetime.datetime.now(datetime.timezone.utc),
                            "userId": user_uid,
                            "isPinned": False,
                            "messages": [msg_data, ai_data]
                        })
                    else:
                        doc_ref.update({
                            "messages": firestore.ArrayUnion([msg_data, ai_data]),
                            "updatedAt": datetime.datetime.now(datetime.timezone.utc)
                        })
                    print(f"✅ Chat saved to Firestore for session: {session_id}")
                except Exception as db_err:
                    print(f"❌ Database Save Error: {type(db_err).__name__}: {db_err}")

        except Exception as e:
            error_msg = f"❌ Gemini API Error: {type(e).__name__}: {str(e)}"
            print(error_msg)
            yield f"\n\nError: I encountered an issue while processing your request. Please try again."

    return Response(stream_with_context(generate()), mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Use debug=False in production (Render)
    # Gunicorn will be used for production: gunicorn backend:app
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
