import json, requests, datetime, re, wikipedia
from groq import Groq
import os
import base64 # Import base64 for image encoding
from PIL import Image # Import PIL for image processing (though not strictly needed if just passing bytes)
from io import BytesIO # For handling image bytes in memory

# ─── Configuration ─────────────────────────────────────────────────────────────
USERNAME = "Amit Dutta"
ASSISTANT_NAME = "Ada"
GROQ_API = os.getenv("Groq")
SERPER_KEY = os.getenv("Serper")
YOUTUBE_KEY = os.getenv("Youtube")
HUGGINGFACE_API_KEY = os.getenv("Image") # New: Hugging Face API Key

client = Groq(api_key=GROQ_API)
SystemChatBot = [{"role": "system", "content": f"You are {ASSISTANT_NAME}, a powerful AI created by {USERNAME}. Answer accurately, clearly, and in English only."}]

# Hugging Face API configuration for image generation
HF_IMAGE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

def RealtimeInformation():
    now = datetime.datetime.now()
    return f"Use this real-time info:\n{now.strftime('%A, %d %B %Y')} {now.strftime('%H:%M:%S')}"

def AnswerModifier(text): return '\n'.join([line for line in text.split('\n') if line.strip()])

def load_guest_names():
    try: return json.load(open("Data/GuestNames.json"))
    except: return {}

def save_guest_names(data):
    json.dump(data, open("Data/GuestNames.json", "w"), indent=4)

def extract_name(query):
    match = re.match(r"name:\s*(\w+)", query.strip(), re.IGNORECASE)
    return match.group(1).capitalize() if match else None

def search_google(query):
    try:
        headers = {"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"}
        data = {"q": query}
        r = requests.post("https://google.serper.dev/search", headers=headers, json=data).json()
        if "organic" in r and r["organic"]:
            result = r["organic"][0]
            return f"{result['title']}\n{result['snippet']}\n🔗 {result['link']}"
        return "No result found."
    except Exception as e:
        print(f"Google search failed: {e}")
        return "Google search failed."

def search_youtube(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_KEY}&type=video&maxResults=1"
        res = requests.get(url).json()
        if "items" in res and res["items"]:
            vid = res["items"][0]
            title = vid["snippet"]["title"]
            link = f"https://youtube.com/watch?v={vid['id']['videoId']}"
            return f"📺 {title}\n🔗 {link}"
        return "No YouTube video found."
    except Exception as e:
        print(f"YouTube search failed: {e}")
        return "YouTube search failed."

def generate_image_response(prompt: str):
    """
    Generates an image using Hugging Face API and returns it as a base64 string.
    """
    if not HUGGINGFACE_API_KEY:
        return "Error: Hugging Face API key is not configured for image generation."

    payload = {"inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution"}
    
    try:
        # Make a synchronous POST request to the Hugging Face API
        response = requests.post(HF_IMAGE_API_URL, headers=HF_HEADERS, json=payload)
        response.raise_for_status() # Raise an error for bad HTTP responses (4xx or 5xx)

        # The response content is the raw binary image data
        image_bytes = response.content
        
        # Encode the image bytes to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Return a special prefix to indicate to the frontend that this is an image
        return f"[IMAGE_BASE64]:{base64_image}"
    except requests.exceptions.RequestException as e:
        print(f"Error generating image from Hugging Face API: {e}")
        return f"I apologize, I could not generate the image. There was an error with the image generation service: {e}"
    except Exception as e:
        print(f"An unexpected error occurred during image generation: {e}")
        return f"An unexpected error occurred while processing your image request: {e}"

def ChatBot(Query, sender_number=None):
    try:
        messages = json.load(open("Data/ChatLog.json"))
    except FileNotFoundError:
        messages = []
    except json.JSONDecodeError:
        messages = [] # Handle corrupted JSON

    guest_names = load_guest_names()
    is_owner = sender_number == "7278779512@c.us" # This might be a placeholder, adjust if needed for web users
    lowered = Query.lower().strip()

    # 🧠 Identity
    if not is_owner and any(kw in lowered for kw in ["who am i", "amar naam", "ami ke", "আমার নাম"]):
        return "🤔 I don’t know your name yet!\nReply like this:\n`name: YourName`"

    name = extract_name(Query)
    if name and not is_owner:
        guest_names[sender_number] = name
        save_guest_names(guest_names)
        return f"✅ Got it! I’ll remember you as {name}."

    if guest_names.get(sender_number) and lowered in ["hi", "hello", "hey"]:
        return f"👋 Welcome back, {guest_names[sender_number]}!"

    # 🖼️ Image Generation Logic (NEW FEATURE)
    if lowered.startswith("image "):
        prompt = Query[len("image "):].strip()
        return generate_image_response(prompt)

    # 🔎 Google / YouTube Logic
    if lowered.startswith("search ") or "search" in lowered:
        return search_google(Query.replace("search", "").strip())
    elif "youtube" in lowered:
        return search_youtube(Query.replace("youtube", "").strip())

    # 🤖 LLM fallback
    messages.append({"role": "user", "content": Query})
    full_messages = SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192", messages=full_messages,
            max_tokens=1024, temperature=0.7
        )

        answer = completion.choices[0].message.content.strip()
        if is_owner:
            answer += "\n" + " " * 72 + "- Ada AI" # This might be specific to a different platform
        messages.append({"role": "assistant", "content": answer})
        json.dump(messages, open("Data/ChatLog.json", "w"), indent=4)
        return answer
    except Exception as e:
        print(f"Error with LLM fallback: {e}")
        return "I'm sorry, I couldn't process that request with the AI. Please try again."

