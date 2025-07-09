# GitHub Repository Setup Guide
## Cybercon Melbourne 2025 - Code Organization for Render Deployment

### 📁 **Required Folder Structure**

Your GitHub repository should be organized like this:

```
cybercon-melbourne-2025/
├── backend/
│   ├── src/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routes/
│   │   └── utils/
│   ├── requirements.txt
│   ├── render.yaml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── lib/
│   │   └── contexts/
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── docs/
│   ├── user_manual.md
│   ├── deployment_guide.md
│   └── api_documentation.md
└── README.md
```

### 🗂️ **Where to Find Your Code**

#### **Backend Code Location**
Your backend code is currently located at:
```
/home/ubuntu/cybercon_speaker_system/
```

**What to copy to `/backend` folder:**
- Copy the entire contents of `/home/ubuntu/cybercon_speaker_system/` 
- This includes:
  - `src/` folder (with main.py, models, routes, utils)
  - `requirements.txt`
  - `render.yaml`
  - `.env.example`

#### **Frontend Code Location**
Your frontend code is currently located at:
```
/home/ubuntu/cybercon-frontend/
```

**What to copy to `/frontend` folder:**
- Copy the entire contents of `/home/ubuntu/cybercon-frontend/`
- This includes:
  - `src/` folder (with components, pages, lib, contexts)
  - `package.json`
  - `vite.config.js`
  - `.env.example`
  - `index.html`

### 📋 **Step-by-Step Setup Instructions**

#### **Step 1: Create GitHub Repository**
1. Go to https://github.com
2. Click "New repository"
3. Name it: `cybercon-melbourne-2025`
4. Make it **Private** (recommended for conference systems)
5. Initialize with README
6. Click "Create repository"

#### **Step 2: Clone Repository Locally**
```bash
git clone https://github.com/yourusername/cybercon-melbourne-2025.git
cd cybercon-melbourne-2025
```

#### **Step 3: Create Folder Structure**
```bash
mkdir backend
mkdir frontend
mkdir docs
```

#### **Step 4: Copy Backend Code**
From your development environment, copy all files from:
- **Source**: `/home/ubuntu/cybercon_speaker_system/`
- **Destination**: `backend/` folder in your repository

**Files to copy:**
```
backend/
├── src/
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── communication.py
│   │   ├── session_review.py
│   │   └── notification.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── sessions.py
│   │   ├── approver.py
│   │   ├── admin.py
│   │   ├── files.py
│   │   └── notifications.py
│   ├── utils/
│   │   └── security.py
│   └── database/
├── requirements.txt
├── render.yaml
└── .env.example
```

#### **Step 5: Copy Frontend Code**
From your development environment, copy all files from:
- **Source**: `/home/ubuntu/cybercon-frontend/`
- **Destination**: `frontend/` folder in your repository

**Files to copy:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   ├── Layout.jsx
│   │   ├── LoadingSpinner.jsx
│   │   ├── FileUpload.jsx
│   │   ├── PresentationViewer.jsx
│   │   └── NotificationCenter.jsx
│   ├── pages/
│   │   ├── auth/
│   │   ├── speaker/
│   │   ├── manager/
│   │   └── admin/
│   ├── lib/
│   │   └── api.js
│   ├── contexts/
│   │   └── AuthContext.jsx
│   ├── App.jsx
│   └── main.jsx
├── package.json
├── vite.config.js
├── .env.example
├── index.html
└── tailwind.config.js
```

#### **Step 6: Copy Documentation**
Copy all documentation files to the `docs/` folder:
- `user_manual.md`
- `deployment_guide.md`
- `api_documentation.md`
- `render_deployment_checklist.md`

#### **Step 7: Create README.md**
Create a main README.md file in the root:

```markdown
# Cybercon Melbourne 2025 Speaker Presentation Management System

## Overview
Professional speaker presentation management system for Cybercon Melbourne 2025.

## Structure
- `/backend` - Flask API backend
- `/frontend` - React frontend application
- `/docs` - Complete documentation

## Deployment
See `/docs/render_deployment_guide.md` for complete deployment instructions.

## Quick Start
1. Deploy backend to Render Web Service
2. Deploy frontend to Render Static Site
3. Configure environment variables
4. Test and launch!

## Support
- Default admin: admin@cybercon2025.com / CyberconAdmin2025!
- Documentation: See `/docs` folder
- Render support: https://render.com/support
```

#### **Step 8: Commit and Push**
```bash
git add .
git commit -m "Initial commit: Cybercon Melbourne 2025 speaker system"
git push origin main
```

### 🔧 **Render Configuration Updates**

When deploying to Render, you'll need to specify the correct paths:

#### **Backend Service Configuration**
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python src/main.py`

#### **Frontend Service Configuration**
- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `dist`

### 📱 **Alternative: Download from Sandbox**

If you're working in the Manus sandbox, you can download the files directly:

#### **Backend Files to Download**
1. Navigate to `/home/ubuntu/cybercon_speaker_system/`
2. Download the entire folder
3. Upload to your GitHub repository's `backend/` folder

#### **Frontend Files to Download**
1. Navigate to `/home/ubuntu/cybercon-frontend/`
2. Download the entire folder
3. Upload to your GitHub repository's `frontend/` folder

### ✅ **Verification Checklist**

Before proceeding with Render deployment, verify:

- [ ] GitHub repository created and configured
- [ ] Backend code in `/backend` folder
- [ ] Frontend code in `/frontend` folder
- [ ] Documentation in `/docs` folder
- [ ] README.md file created
- [ ] Repository is private (recommended)
- [ ] All files committed and pushed
- [ ] Repository accessible from Render

### 🎯 **Next Steps**

Once your GitHub repository is properly organized:

1. **Connect Render to GitHub**: Link your GitHub account to Render
2. **Deploy Backend**: Create Web Service pointing to `/backend` folder
3. **Deploy Frontend**: Create Static Site pointing to `/frontend` folder
4. **Configure Environment Variables**: Use the provided `.env.example` files
5. **Test Deployment**: Follow the deployment checklist

### 💡 **Pro Tips**

- **Keep it Private**: Conference systems should use private repositories
- **Use Branches**: Create a `development` branch for testing changes
- **Document Changes**: Use clear commit messages for tracking changes
- **Backup Regularly**: GitHub serves as your code backup
- **Test Locally**: Always test changes locally before deploying

This organization ensures that Render can easily deploy both your backend and frontend from the same repository while keeping everything organized and maintainable!

