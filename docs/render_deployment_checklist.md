# Cybercon Melbourne 2025 - Render Deployment Checklist

## Pre-Deployment Preparation

### ✅ **Repository Setup**
- [ ] Create GitHub repository for the project
- [ ] Upload backend code to `/backend` folder
- [ ] Upload frontend code to `/frontend` folder
- [ ] Ensure all sensitive data is removed from code
- [ ] Verify `.env.example` files are included
- [ ] Test local build process

### ✅ **Account Setup**
- [ ] Create Render account at https://render.com
- [ ] Connect GitHub account to Render
- [ ] Verify email address
- [ ] Set up billing information (if using paid plans)

### ✅ **Domain Preparation** (Optional but Recommended)
- [ ] Register domain name (e.g., speakers.cybercon2025.com.au)
- [ ] Configure DNS settings
- [ ] Prepare subdomain strategy (api.cybercon2025.com.au)

## Backend Deployment Steps

### ✅ **Database Service Creation**
1. [ ] Log into Render dashboard
2. [ ] Click "New +" → "PostgreSQL"
3. [ ] Configure database:
   - **Name**: `cybercon-2025-database`
   - **Database Name**: `cybercon_speaker_db`
   - **User**: `cybercon_user`
   - **Region**: Choose closest to your users
   - **Plan**: Starter ($7/month) or higher
4. [ ] Wait for database provisioning (5-10 minutes)
5. [ ] Copy the **Internal Database URL** for backend configuration

### ✅ **Backend Web Service Creation**
1. [ ] Click "New +" → "Web Service"
2. [ ] Connect your GitHub repository
3. [ ] Configure service:
   - **Name**: `cybercon-2025-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `cybercon_speaker_system` (if in subfolder)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/main.py`
   - **Plan**: Starter ($7/month) or higher

### ✅ **Backend Environment Variables**
Configure the following environment variables in Render dashboard:

**Required Variables:**
- [ ] `DATABASE_URL`: Use the Internal Database URL from step above
- [ ] `JWT_SECRET_KEY`: Generate a secure random key
- [ ] `SESSION_SECRET`: Generate a secure random key
- [ ] `ENCRYPTION_KEY`: Generate a secure random key
- [ ] `DEBUG`: Set to `false`
- [ ] `FLASK_ENV`: Set to `production`
- [ ] `PORT`: Set to `5000`
- [ ] `HOST`: Set to `0.0.0.0`

**Optional Variables:**
- [ ] `SENDGRID_API_KEY`: For email notifications
- [ ] `SENDGRID_FROM_EMAIL`: From email address
- [ ] `UPLOAD_FOLDER`: Set to `/tmp/uploads`
- [ ] `MAX_FILE_SIZE`: Set to `104857600` (100MB)

### ✅ **Backend Deployment Verification**
1. [ ] Wait for build to complete (10-15 minutes)
2. [ ] Check build logs for errors
3. [ ] Verify service is running
4. [ ] Test health check endpoint: `https://your-backend.onrender.com/api/health`
5. [ ] Verify database connection in logs
6. [ ] Test admin login with default credentials

## Frontend Deployment Steps

### ✅ **Frontend Static Site Creation**
1. [ ] Click "New +" → "Static Site"
2. [ ] Connect your GitHub repository
3. [ ] Configure service:
   - **Name**: `cybercon-2025-frontend`
   - **Branch**: `main`
   - **Root Directory**: `cybercon-frontend` (if in subfolder)
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

### ✅ **Frontend Environment Variables**
Configure the following environment variables:

**Required Variables:**
- [ ] `VITE_API_BASE_URL`: Set to your backend URL (e.g., `https://cybercon-2025-backend.onrender.com/api`)
- [ ] `VITE_APP_NAME`: Set to `Cybercon Melbourne 2025 Speaker Portal`
- [ ] `VITE_CONFERENCE_NAME`: Set to `Cybercon Melbourne 2025`
- [ ] `VITE_CONFERENCE_YEAR`: Set to `2025`

**Optional Variables:**
- [ ] `VITE_GOOGLE_ANALYTICS_ID`: For analytics tracking
- [ ] `VITE_MAX_FILE_SIZE`: Set to `104857600`
- [ ] `VITE_ALLOWED_FILE_TYPES`: Set to `pdf,ppt,pptx,mp4,mov`

### ✅ **Frontend Deployment Verification**
1. [ ] Wait for build to complete (5-10 minutes)
2. [ ] Check build logs for errors
3. [ ] Verify site is accessible
4. [ ] Test login functionality
5. [ ] Verify API connectivity
6. [ ] Test file upload functionality

## Custom Domain Setup (Optional)

### ✅ **Backend Domain Configuration**
1. [ ] In backend service settings, go to "Custom Domains"
2. [ ] Add domain: `api.cybercon2025.com.au`
3. [ ] Configure DNS CNAME record pointing to Render URL
4. [ ] Wait for SSL certificate provisioning

### ✅ **Frontend Domain Configuration**
1. [ ] In frontend service settings, go to "Custom Domains"
2. [ ] Add domain: `speakers.cybercon2025.com.au`
3. [ ] Configure DNS CNAME record pointing to Render URL
4. [ ] Wait for SSL certificate provisioning
5. [ ] Update `VITE_API_BASE_URL` to use custom backend domain

## Post-Deployment Configuration

### ✅ **Security Configuration**
- [ ] Verify HTTPS is working on both services
- [ ] Test CORS configuration
- [ ] Verify security headers are present
- [ ] Test authentication flows
- [ ] Verify file upload security

### ✅ **Email Configuration**
- [ ] Set up SendGrid account (or preferred email provider)
- [ ] Configure API keys in backend environment
- [ ] Test email delivery
- [ ] Configure email templates
- [ ] Verify notification system

### ✅ **Monitoring Setup**
- [ ] Enable Render monitoring
- [ ] Set up uptime monitoring
- [ ] Configure error alerting
- [ ] Set up log monitoring
- [ ] Test backup procedures

## Testing and Validation

### ✅ **Functional Testing**
- [ ] Test user registration flow
- [ ] Test login and authentication
- [ ] Test session submission
- [ ] Test file upload (various formats and sizes)
- [ ] Test manager review workflow
- [ ] Test admin functions
- [ ] Test email notifications
- [ ] Test mobile responsiveness

### ✅ **Performance Testing**
- [ ] Test page load times
- [ ] Test file upload performance
- [ ] Test concurrent user scenarios
- [ ] Verify database performance
- [ ] Test API response times

### ✅ **Security Testing**
- [ ] Test authentication security
- [ ] Verify file upload restrictions
- [ ] Test input validation
- [ ] Verify HTTPS enforcement
- [ ] Test session management

## Go-Live Preparation

### ✅ **Content Setup**
- [ ] Create initial admin accounts
- [ ] Configure session types
- [ ] Set up conference rooms
- [ ] Create FAQ content
- [ ] Prepare user documentation

### ✅ **User Communication**
- [ ] Prepare launch announcement
- [ ] Create user guides
- [ ] Set up support channels
- [ ] Plan user training sessions
- [ ] Prepare troubleshooting guides

### ✅ **Backup and Recovery**
- [ ] Verify database backups are working
- [ ] Test recovery procedures
- [ ] Document emergency procedures
- [ ] Set up monitoring alerts
- [ ] Create incident response plan

## Launch Day Checklist

### ✅ **Final Verification**
- [ ] Verify all services are running
- [ ] Test complete user workflows
- [ ] Verify email notifications
- [ ] Check monitoring systems
- [ ] Confirm support team readiness

### ✅ **Launch Activities**
- [ ] Send launch announcement
- [ ] Monitor system performance
- [ ] Respond to user questions
- [ ] Track system metrics
- [ ] Document any issues

## Post-Launch Monitoring

### ✅ **Daily Monitoring**
- [ ] Check system uptime
- [ ] Monitor error rates
- [ ] Review user feedback
- [ ] Check email delivery
- [ ] Monitor file uploads

### ✅ **Weekly Reviews**
- [ ] Review performance metrics
- [ ] Analyse user behaviour
- [ ] Check security logs
- [ ] Review backup status
- [ ] Plan optimisations

---

## Emergency Contacts and Resources

### **Render Support**
- Dashboard: https://dashboard.render.com
- Documentation: https://render.com/docs
- Support: https://render.com/support

### **System Information**
- Backend URL: `https://cybercon-2025-backend.onrender.com`
- Frontend URL: `https://cybercon-2025-frontend.onrender.com`
- Database: PostgreSQL on Render
- Admin Email: `admin@cybercon2025.com`
- Default Password: `CyberconAdmin2025!`

### **Key Configuration Files**
- Backend: `/cybercon_speaker_system/src/main.py`
- Frontend: `/cybercon-frontend/src/lib/api.js`
- Environment: `.env.example` files in both directories

---

**Deployment Estimated Timeline:**
- Database Setup: 10 minutes
- Backend Deployment: 15-20 minutes
- Frontend Deployment: 10-15 minutes
- Domain Configuration: 30-60 minutes
- Testing and Validation: 2-4 hours
- **Total: 3-5 hours**

**Monthly Costs (Estimated):**
- PostgreSQL Database: $7/month
- Backend Web Service: $7/month
- Frontend Static Site: Free
- **Total: $14/month**

This checklist ensures a smooth, professional deployment of your Cybercon Melbourne 2025 Speaker Presentation Management System on Render.

