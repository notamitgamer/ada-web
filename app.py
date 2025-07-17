from flask import Flask, request, jsonify, Response # Import Response
from flask_cors import CORS
from Backend.Chatbot import ChatBot
import uuid
import os
import json # Import json for encoding error messages

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
    Now streams the AI response.
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

    def generate_response_stream():
        """Generator function to stream response chunks."""
        full_response_content = "" # To capture the full response for saving to chat log

        try:
            # Call the ChatBot function which now yields chunks
            for chunk in ChatBot(user_message, sender_for_chatbot):
                # Check if this is an image response (non-streaming text, but still yielded)
                if chunk.startswith("[IMAGE_BASE64]:"):
                    # If it's an image, we send it as a single JSON response
                    # The frontend will detect this Content-Type
                    # We need to encode the JSON string to bytes
                    yield json.dumps({"response": chunk, "user_id": user_id}).encode('utf-8')
                    return # Stop streaming and return

                # If it's not an image, it's a text chunk, so stream it
                full_response_content += chunk # Accumulate for saving
                yield chunk.encode('utf-8') # Encode chunks to bytes for streaming

            # After streaming is complete, save the full response to ChatLog.json
            # This part will only execute if the ChatBot yielded text chunks.
            # For image/search/youtube, ChatBot returns early.
            if full_response_content:
                # Load existing chat log
                try:
                    messages = json.load(open("Data/ChatLog.json"))
                except (FileNotFoundError, json.JSONDecodeError):
                    messages = []
                
                # Append the full AI response
                messages.append({"role": "assistant", "content": full_response_content})
                
                # Save updated chat log
                with open("Data/ChatLog.json", "w") as f:
                    json.dump(messages, f, indent=4)
                print("Full LLM response saved to ChatLog.json")

        except Exception as e:
            print(f"Error processing chat request during streaming: {e}")
            # Send error message as a JSON object if an error occurs during streaming setup
            # This will be the only thing sent if the error happens early.
            yield json.dumps({"response": f"Error: {str(e)}", "user_id": user_id}).encode('utf-8')

    # Return a streaming response.
    # For text streaming, 'text/plain' is appropriate.
    # For image responses, the generator will yield a JSON string, and the frontend
    # will need to parse it. Let's keep text/plain for the stream
    # and let the frontend parse the first chunk if it's JSON.
    return Response(generate_response_stream(), mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

