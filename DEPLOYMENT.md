# Ada AI Coding Environment - Deployment Guide

## Quick Deployment Checklist

### 1. Prerequisites
- [ ] GitHub account
- [ ] Render.com account (free)
- [ ] Firebase project setup (ada-ai-aranag)
- [ ] Google AI API key
- [ ] UptimeRobot account (optional, for keeping backend alive)

### 2. Backend Deployment on Render.com

1. **Login to Render.com**
   - Visit https://render.com
   - Sign in with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect repository: `notamitgamer/ada-web`
   - Select branch: `main`

3. **Configure Service**
   ```
   Name: ada-web-backend
   Region: Oregon (or closest to you)
   Branch: main
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn backend:app --workers 2 --threads 2 --timeout 120
   Instance Type: Free
   ```

4. **Set Environment Variables**
   - Click "Environment" tab
   - Add the following variables:

   ```
   GEMINI_API_KEY=AIzaSyDWUl8ouV5PBn7o9a3mcC-OIyOTuC0aLLo
   
   FIREBASE_CREDENTIALS={"type":"service_account","project_id":"ada-ai-aranag",...}
   (Paste the entire Firebase service account JSON as one line)
   
   FLASK_DEBUG=False
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Note your backend URL: `https://ada-web.onrender.com`

### 3. Firebase Configuration

#### Get Service Account Key
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: `ada-ai-aranag`
3. Click ⚙️ Settings → Service Accounts
4. Click "Generate New Private Key"
5. Download JSON file
6. Copy entire JSON content to `FIREBASE_CREDENTIALS` env var

#### Firebase Settings
- **Authentication**: Enable Google and Email/Password providers
- **Firestore**: Create database in production mode
- **Rules**: Set up security rules (see below)

#### Firestore Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      match /chats/{chatId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

### 4. Frontend Deployment (GitHub Pages)

1. **Prepare for Deployment**
   - Frontend is already in repository (index.html, docs.html)
   - No build step required

2. **Deploy to GitHub Pages**
   - Go to repository Settings → Pages
   - Source: Deploy from branch `main`
   - Folder: `/ (root)`
   - Click Save

3. **Alternative: Use Custom Domain**
   - Add CNAME file with: `ada.amit.is-a.dev`
   - Configure DNS to point to GitHub Pages

4. **Verify Frontend**
   - Visit: `https://notamitgamer.github.io/ada-web/`
   - Or custom domain: `https://ada.amit.is-a.dev/`

### 5. UptimeRobot Setup (Keep Backend Alive)

1. **Create Account**
   - Visit https://uptimerobot.com
   - Sign up for free

2. **Add Monitor**
   ```
   Monitor Type: HTTP(s)
   Friendly Name: Ada Backend Health
   URL: https://ada-web.onrender.com/health
   Monitoring Interval: 5 minutes
   ```

3. **Configure Alerts** (Optional)
   - Email notifications when backend is down
   - SMS alerts (paid plan)

### 6. Update Frontend API URL

If your backend URL is different from `https://ada-web.onrender.com`:

1. Edit `index.html`
2. Find line ~386:
   ```javascript
   const API_URL = 'https://ada-web.onrender.com/api/chat';
   ```
3. Change to your actual Render URL
4. Commit and push changes

### 7. Testing Deployment

#### Test Backend
```bash
# Health check
curl https://ada-web.onrender.com/health

# Expected response:
{"status":"healthy","timestamp":"2024-01-17T..."}

# Service info
curl https://ada-web.onrender.com/

# Expected response:
{"status":"online","service":"Ada AI Coding Backend",...}
```

#### Test Frontend
1. Open `https://ada.amit.is-a.dev/`
2. Sign in with Google or Email
3. Ask a coding question
4. Verify response streams correctly
5. Check code appears in editor
6. Test "Run/Compile" button

### 8. Common Issues & Solutions

#### Backend returns 401 Unauthorized
- **Cause**: Firebase credentials not set correctly
- **Fix**: Check `FIREBASE_CREDENTIALS` env var in Render
- **Verify**: Ensure JSON is valid and from correct project

#### Backend is slow (30-60 seconds)
- **Cause**: Render free tier spins down after 15 minutes
- **Fix**: Set up UptimeRobot to ping every 5 minutes
- **Note**: First request after spindown will be slow

#### Frontend can't connect to backend
- **Cause**: CORS error or wrong API URL
- **Fix**: Check browser console for errors
- **Verify**: Backend URL in index.html matches Render URL
- **CORS**: Backend already configured for `ada.amit.is-a.dev`

#### Firestore permission denied
- **Cause**: Security rules too restrictive
- **Fix**: Update Firestore rules (see Firebase Configuration above)
- **Test**: Try reading/writing with authenticated user

### 9. Monitoring & Maintenance

#### Check Backend Logs
- Render Dashboard → Your Service → Logs
- Look for errors, token verification messages
- Monitor Gemini API usage

#### Monitor Uptime
- UptimeRobot Dashboard
- Check response times
- Review downtime reports

#### Update Dependencies
```bash
# Periodically update packages
pip install --upgrade google-generativeai
pip install --upgrade firebase-admin
pip install --upgrade Flask

# Update requirements.txt
pip freeze > requirements.txt
```

### 10. Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Render.com | Free | $0/month |
| Firebase Auth | Spark (Free) | $0/month |
| Firebase Firestore | Spark (Free) | $0/month (up to 1GB) |
| Google AI (Gemini) | Free tier | $0/month (60 requests/min) |
| UptimeRobot | Free | $0/month (50 monitors) |
| GitHub Pages | Free | $0/month |
| **Total** | | **$0/month** |

**Upgrade Considerations:**
- Render Starter ($7/mo): No spin-down, better performance
- Firebase Blaze: Pay-as-you-go for heavy usage
- Gemini API: Paid tier for higher rate limits

### 11. Security Checklist

- [x] HTTPS enabled (automatic on Render & GitHub Pages)
- [x] Firebase ID token verification on backend
- [x] CORS configured to specific domains
- [x] Environment variables secure (not in code)
- [x] API keys not exposed to frontend
- [x] Firestore security rules enforced
- [x] Debug mode disabled in production

### 12. Production URLs

```
Frontend: https://ada.amit.is-a.dev/
Documentation: https://ada.amit.is-a.dev/docs.html
Backend API: https://ada-web.onrender.com/api/chat
Health Check: https://ada-web.onrender.com/health
GitHub Repo: https://github.com/notamitgamer/ada-web
```

### 13. Support & Resources

- **Documentation**: Open `docs.html` in browser
- **README**: Full setup guide in repository
- **Issues**: GitHub Issues for bug reports
- **Firebase**: https://console.firebase.google.com/
- **Render**: https://dashboard.render.com/

---

## Quick Commands Reference

```bash
# Local development
python backend.py

# Test backend
python test_backend.py

# Deploy to Render (automatic on git push to main)
git push origin main

# Check deployment status
curl https://ada-web.onrender.com/health
```

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Status**: Production Ready ✅
