# Ada AI Coding Environment

A specialized AI coding assistant that helps with code analysis, debugging, and generation.

## Features

- 🤖 **AI-Powered Code Assistant**: Uses Gemini 2.5 Flash Preview for intelligent code analysis
- 💬 **Real-time Chat**: Stream responses with markdown rendering
- 📝 **Code Editor**: Built-in CodeMirror editor with syntax highlighting
- 🔐 **Secure Authentication**: Firebase Auth with Google OAuth and Email/Password
- 💾 **Chat History**: Persistent storage in Firestore
- 🚀 **Code Compilation**: Direct integration with online compiler
- 📱 **Mobile Responsive**: Works seamlessly on desktop and mobile

## Tech Stack

**Frontend:**
- Vanilla JavaScript (ES6+)
- Tailwind CSS
- CodeMirror (code editor)
- LZString (compression)
- Firebase SDK (Auth & Firestore)
- Marked.js (markdown rendering)

**Backend:**
- Python 3.x
- Flask
- Google Generative AI SDK (Gemini 2.5 Flash Preview)
- Firebase Admin SDK
- Flask-CORS

**Database:**
- Firebase Firestore (NoSQL)

## Setup

### Prerequisites
- Python 3.8+
- Node.js (for frontend development)
- Firebase account
- Google AI API key

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/notamitgamer/ada-web.git
cd ada-web
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file (use `.env.example` as template):
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`:
```
GEMINI_API_KEY=your_actual_gemini_api_key
FIREBASE_CREDENTIALS={"type":"service_account",...}
PORT=5000
```

5. Run the backend:
```bash
python backend.py
```

### Frontend Setup

The frontend is a static HTML application. Simply open `index.html` in a browser or serve it using a local server:

```bash
python -m http.server 5500
```

Then visit: `http://localhost:5500`

## Firebase Configuration

### Firestore Database Schema

```
users (collection)
  ├─ {uid} (document)
      ├─ email: string
      ├─ displayName: string
      ├─ photoURL: string
      ├─ createdAt: timestamp
      └─ chats (subcollection)
          └─ {chatUUID} (document)
              ├─ title: string
              ├─ createdAt: timestamp
              ├─ updatedAt: timestamp
              └─ messages: array[
                  {
                    role: "user" | "model",
                    content: string,
                    timestamp: timestamp
                  }
                ]
```

### Firebase Service Account

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: `ada-ai-aranag`
3. Navigate to Project Settings > Service Accounts
4. Generate new private key
5. Use the downloaded JSON for `FIREBASE_CREDENTIALS` environment variable

## API Endpoints

### POST `/api/chat`
Streams AI responses for code queries.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Body:**
```json
{
  "message": "Why is this loop infinite?",
  "history": [],
  "codeContext": "while(i > 0) { ... }",
  "fileContext": "",
  "sessionId": "uuid-v4"
}
```

### POST `/api/generate-title`
Generates a short title for chat sessions.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Body:**
```json
{
  "message": "First user message"
}
```

## Deployment

### Render.com

1. Create a new Web Service
2. Connect your GitHub repository
3. Set environment variables:
   - `GEMINI_API_KEY`
   - `FIREBASE_CREDENTIALS` (full JSON string)
4. Deploy!

### Frontend (Static Hosting)

Deploy `index.html` to:
- GitHub Pages
- Netlify
- Vercel
- Any static hosting service

Update the API URL in `index.html`:
```javascript
const API_URL = 'https://your-backend.onrender.com/api/chat';
```

## Development

### Running Tests

```bash
python test_backend.py
```

### Code Style

- Python: Follow PEP 8
- JavaScript: ES6+ with consistent formatting
- Use meaningful variable names
- Comment complex logic

## Security Features

✅ Firebase ID Token verification on backend
✅ CORS protection
✅ Environment variable protection
✅ Server-side authentication validation
✅ Secure API key storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Author

**Amit Dutta**
- Website: [amit.is-a.dev](https://amit.is-a.dev)
- Project: [Ada AI](https://ada.amit.is-a.dev)

## Acknowledgments

- Google Gemini AI for powering the code assistant
- Firebase for authentication and database
- CodeMirror for the code editor
- The open-source community