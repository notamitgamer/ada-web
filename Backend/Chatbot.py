import json, requests, datetime, re, wikipedia
from groq import Groq
import os

# ─── Configuration ─────────────────────────────────────────────────────────────
USERNAME = "Amit Dutta"
ASSISTANT_NAME = "Ada"
GROQ_API = os.getenv("Groq")
SERPER_KEY = os.getenv("Serper")
YOUTUBE_KEY = os.getenv("Youtube")

client = Groq(api_key=GROQ_API)
SystemChatBot = [{"role": "system", "content": f"You are {ASSISTANT_NAME}, a powerful AI created by {USERNAME}. Answer accurately, clearly, and in English only."}]

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
    except:
        return "Google search failed."

def search_youtube(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_KEY}&type=video&maxResults=1"
        res = requests.get(url).json()
        vid = res["items"][0]
        title = vid["snippet"]["title"]
        link = f"https://youtube.com/watch?v={vid['id']['videoId']}"
        return f"📺 {title}\n🔗 {link}"
    except:
        return "YouTube search failed."

def ChatBot(Query, sender_number=None):
    try:
        messages = json.load(open("Data/ChatLog.json"))
    except:
        messages = []

    guest_names = load_guest_names()
    is_owner = sender_number == "7278779512@c.us"
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

    # 🔎 Google / YouTube Logic
    if lowered.startswith("search ") or "search" in lowered:
        return search_google(Query.replace("search", "").strip())
    elif "youtube" in lowered:
        return search_youtube(Query.replace("youtube", "").strip())

    # 🤖 LLM fallback
    messages.append({"role": "user", "content": Query})
    full_messages = SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages

    completion = client.chat.completions.create(
        model="llama3-70b-8192", messages=full_messages,
        max_tokens=1024, temperature=0.7
    )

    answer = completion.choices[0].message.content.strip()
    if is_owner:
        answer += "\n" + " " * 72 + "- Ada AI"
    messages.append({"role": "assistant", "content": answer})
    json.dump(messages, open("Data/ChatLog.json", "w"), indent=4)
    return answer
