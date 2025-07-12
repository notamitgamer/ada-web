from flask import Flask, request, jsonify
from flask_cors import CORS # <--- ADD THIS IMPORT
from Backend.Chatbot import ChatBot
import uuid
import os

app = Flask(__name__)
CORS(app) # <--- ADD THIS LINE: Enables CORS for all routes

# --- Ensure Data directory exists (same as in Chatbot.py) ---
if not os.path.exists("Data"):
    os.makedirs("Data")

@app.route('/')
def home():
    """Basic route to confirm the server is running."""
    return "Your AI Chatbot API is running! Access the /chat endpoint via POST."

@app.route('/chat', methods=['POST'])
def chat():
    """
    API endpoint for handling chat messages.
    Expects a JSON payload with 'message' and optionally 'user_id'.
    """
    data = request.get_json()

    user_message = data.get('message')
    user_id = data.get('user_id') # Get user_id from the frontend

    if not user_message:
        return jsonify({"response": "Error: 'message' field is required.", "user_id": user_id}), 400

    if not user_id:
        user_id = str(uuid.uuid4())
        print(f"New guest session initiated: {user_id}")

    sender_for_chatbot = f"web_user_{user_id}@website.com"

    try:
        ai_response = ChatBot(user_message, sender_for_chatbot)
        return jsonify({"response": ai_response, "user_id": user_id})
    except Exception as e:
        print(f"Error processing chat request: {e}")
        # Return a more informative error for debugging if needed, but keep it generic for production
        return jsonify({"response": "I'm sorry, something went wrong on my end. Please check server logs.", "user_id": user_id}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
