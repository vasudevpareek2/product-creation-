# Render Deployment Guide

This project has been configured for deployment on Render with two separate services:
- **Backend**: FastAPI Python service
- **Frontend**: Next.js React service

## 📋 Prerequisites

1. **GitHub Account** - Create a new repository
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Environment Variables** - Have your Thrillophilia API credentials ready

## 🚀 Deployment Steps

### 1. Create GitHub Repository

1. Go to [github.com](https://github.com) and create a new repository
2. Name it something like `product-creation-webapp`
3. Don't initialize with README (we already have one)
4. Push your code:

```bash
cd "C:\Users\vasud\OneDrive\Desktop\bday 1\product-creation-webapp"
git remote add origin https://github.com/YOUR_USERNAME/product-creation-webapp.git
git branch -M main
git push -u origin main
```

### 2. Deploy Backend on Render

1. Go to [render.com](https://render.com) and log in
2. Click **"New +"** → **"Web Service"**
3. **Connect GitHub Repository** - Select your repo
4. **Configure Backend Service:**
   - **Name**: `product-creation-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3.9
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_backend.py`
   - **Instance Type**: Free

5. **Add Environment Variables:**
   ```
   THRILLOPHILIA_ADMIN_URL=https://admin.thrillophilia.com
   GROQ_API_KEY=your_groq_api_key_here
   (Add other variables from backend/.env.example)
   ```

6. **Click "Create Web Service"**

### 3. Deploy Frontend on Render

1. Click **"New +"** → **"Web Service"**
2. **Connect the same GitHub Repository**
3. **Configure Frontend Service:**
   - **Name**: `product-creation-frontend`
   - **Root Directory**: `frontend-new`
   - **Runtime**: Node 18
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Instance Type**: Free

4. **Add Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://product-creation-backend.onrender.com
   NODE_VERSION=18
   PORT=3000
   ```

5. **Click "Create Web Service"**

## 🔧 Post-Deployment Configuration

### 1. Update Frontend API URL

After the backend is deployed, you'll get a URL like:
`https://product-creation-backend-xyz.onrender.com`

Update the frontend service's `NEXT_PUBLIC_API_URL` environment variable to match this URL.

### 2. Test the Deployment

1. **Backend**: Visit `https://product-creation-backend.onrender.com/docs` to see the API documentation
2. **Frontend**: Visit `https://product-creation-frontend.onrender.com` to see the web interface

## 📁 Project Structure

```
product-creation-webapp/
├── backend/                 # FastAPI backend
│   ├── render.yaml         # Render configuration
│   ├── requirements.txt     # Python dependencies
│   ├── routes/             # API endpoints
│   ├── models/             # Data models
│   └── services/           # Business logic
├── frontend-new/           # Next.js frontend
│   ├── render.yaml         # Render configuration
│   ├── src/                # React components
│   └── package.json        # Node dependencies
└── render.yaml             # Root Render configuration
```

## 🔐 Security Notes

- **Never commit sensitive data** to git (use environment variables)
- **Environment variables** are set in Render's dashboard
- **API keys** should be stored securely in Render's environment variables
- **`.env` files** are included in `.gitignore` for security

## 🐛 Troubleshooting

### Backend fails to start:
- Check the logs in Render dashboard
- Verify all environment variables are set correctly
- Ensure Python version is 3.9

### Frontend can't connect to backend:
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in backend
- Ensure both services are in the same Render account

### Build fails:
- Check requirements.txt has all dependencies
- Verify Node version is compatible
- Check build logs for specific errors

## 📊 Resource Limits (Free Tier)

- **Backend**: 512MB RAM, 0.1 CPU
- **Frontend**: 512MB RAM, 0.1 CPU
- **Sleeps after 15 minutes** of inactivity
- **Monthly free hours**: 750 hours per service

## 🔄 Automatic Deployments

Both services will automatically redeploy when you push to GitHub:
- Push to `main` branch → Automatic deployment
- Push to other branches → Manual deployment available

## 🎯 What's Deployed

✅ **Backend Features:**
- Thrillophilia API integration
- Excel file processing
- Product/variant creation
- AI enrichment (Groq API)
- Batch processing workflow

✅ **Frontend Features:**
- Modern React UI
- Batch management dashboard
- File upload interface
- Real-time progress tracking
- AI assistant integration

## 📝 Notes

- Both services run on the free tier
- Separate services allow independent scaling
- Backend uses FastAPI with Uvicorn server
- Frontend uses Next.js with server-side rendering
- Services communicate via HTTP requests