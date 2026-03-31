# 🚀 ResumeAI - Quick Start Guide

## ⚡ Super Fast Setup (5 Minutes)

### Step 1: Install MySQL (if not installed)
1. Download MySQL: https://dev.mysql.com/downloads/installer/
2. Install MySQL Server and MySQL Workbench
3. Remember your root password: **Aryan@2007** (already configured)

### Step 2: Setup Database
1. **Open MySQL Workbench**
2. **Connect to localhost**
3. **File → Open SQL Script**
4. **Select:** `database_setup.sql`
5. **Click Execute** ⚡ (lightning bolt icon)
6. ✅ You should see "Database setup complete!"

### Step 3: Install Python Packages
**Option A: Using Batch File (Easiest)**
```bash
# Just double-click this file:
install.bat
```

**Option B: Manual Installation**
```bash
pip install flask flask-cors werkzeug PyPDF2 python-docx mysql-connector-python python-dotenv
```

### Step 4: Start the Application
**Option A: Using Batch File (Easiest)**
```bash
# Double-click this file:
QUICK_START.bat
```

**Option B: Manual Start**
```bash
python app-mysql.py
```

### Step 5: Open in Browser
```
http://localhost:5000
```

---

## 🎉 First Time Setup

### Create Your Account
1. Click **"Get Started Free"**
2. Enter your name, email, and password
3. Click **"Create Account"**

### Login as Admin (Optional)
- Email: `admin@resumeai.com`
- Password: `admin123`
- Click "Admin Login" link on login page

---

## 📂 File Structure

```
project nexa/
├── app-mysql.py           ⭐ Main Flask application (MySQL version)
├── index-enhanced.html    ⭐ Enhanced frontend with payments
├── style-enhanced.css     🎨 Beautiful CSS with animations
├── script-enhanced.js     ⚡ JavaScript with admin & payments
├── resume_parser.py       📄 Resume parsing with NLP
├── skill_analyzer.py      📊 Skill gap analysis
├── ai_service.py          🤖 AI features & learning paths
├── database_setup.sql     🗄️ MySQL database schema
├── .env                   🔐 MySQL configuration
├── requirements.txt       📦 Python dependencies
├── QUICK_START.bat        🚀 One-click startup
└── install.bat            📥 Install dependencies

uploads/                   📁 Uploaded resumes stored here
```

---

## 🎯 Features Available

### For Students (Free Account)
- ✅ Upload resume (PDF/DOC/DOCX)
- ✅ AI skill extraction
- ✅ Skill gap analysis
- ✅ View learning paths
- ✅ Basic dashboard

### With Subscription
- ⭐ **Basic (₹499/month)**
  - Resume Analysis
  - Skill Gap Report  
  - 5 Mock Interviews
  - Basic Learning Path
  
- 🔥 **Professional (₹999/3 months)** - Most Popular
  - Everything in Basic
  - Unlimited Mock Interviews
  - AI Interview Feedback
  - Personalized Learning Path
  - Priority Support
  
- 💎 **Premium (₹1999/6 months)**
  - Everything in Professional
  - One-on-One Mentorship
  - Company-Specific Preparation
  - Placement Assistance
  - Certificate

### For Admins
- 📊 Analytics Dashboard
- 👥 User Management
- 💰 Revenue Tracking
- 📈 Skill Gap Insights

---

## 🛠️ Troubleshooting

### MySQL Connection Failed
```bash
# Check if MySQL is running:
# Windows: Services → MySQL80 → Start
# Or open MySQL Workbench and connect manually
```

### Port 5000 Already in Use
Edit `app-mysql.py` line (last line):
```python
app.run(debug=True, port=5001, host='0.0.0.0')  # Changed to 5001
```

### Module Not Found Error
```bash
# Reinstall dependencies:
pip install -r requirements.txt
```

### Database Table Not Found
```bash
# Re-run the SQL script in MySQL Workbench:
# File → Open SQL Script → database_setup.sql → Execute
```

---

## 🎨 UI Features

### Landing Page
- 🌟 Beautiful gradient background
- ✨ Animated robot icon
- 📊 Platform statistics
- 🎯 Feature highlights

### Login/Signup
- 💎 Glassmorphism design
- 🎨 Gradient effects
- ⚡ Smooth animations
- 🔐 Secure password hashing

### Dashboard
- 📊 Stats cards
- 📈 Match score visualization
- 🎯 Quick analyze feature
- 💡 Interactive elements

### Pricing Page
- 💳 3 pricing tiers
- ⭐ Popular badge
- 💰 Payment methods display
- 🎨 Hover effects

### Admin Dashboard
- 📊 4 stat cards with gradients
- 👥 Recent users list
- 💰 Revenue breakdown
- 📈 Common skill gaps

---

## 🔐 Security Notes

### Change Default Admin Password
After first login as admin:
```sql
-- Run in MySQL Workbench:
UPDATE users 
SET password = 'new_hashed_password' 
WHERE email = 'admin@resumeai.com';
```

### Production Deployment
Edit `.env`:
```env
FLASK_DEBUG=False
SECRET_KEY=generate-new-random-key-here
```

---

## 📊 MySQL Workbench Queries

### View All Users
```sql
USE resumeai;
SELECT id, name, email, role, created_at FROM users;
```

### View Active Subscriptions
```sql
SELECT u.name, s.plan_type, s.amount, s.end_date 
FROM subscriptions s 
JOIN users u ON s.user_id = u.id
WHERE s.status = 'active';
```

### Total Revenue
```sql
SELECT SUM(amount) as total_revenue
FROM payments 
WHERE status = 'completed';
```

### User Activity Stats
```sql
SELECT 
    u.name,
    COUNT(DISTINCT r.id) as resumes,
    COUNT(DISTINCT sa.id) as analyses
FROM users u
LEFT JOIN resumes r ON u.id = r.user_id
LEFT JOIN skill_analysis sa ON u.id = sa.user_id
GROUP BY u.id, u.name;
```

---

## 🚀 Production Deployment

### Using Gunicorn (Linux/Mac)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app-mysql:app
```

### Using Waitress (Windows)
```bash
pip install waitress
waitress-serve --port=5000 app-mysql:app
```

### With Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📱 API Endpoints

### Authentication
- `POST /api/register` - Create account
- `POST /api/login` - Login
- `POST /api/logout` - Logout
- `GET /api/user` - Get current user

### Resume & Skills
- `POST /api/upload-resume` - Upload resume
- `POST /api/analyze-skills` - Analyze skill gap
- `GET /api/role-requirements/<role>` - Get role requirements

### Payments
- `GET /api/payment/plans` - Get pricing plans
- `POST /api/payment/create-order` - Create payment order
- `POST /api/payment/verify` - Verify payment
- `GET /api/subscription/status` - Get subscription status

### Admin
- `GET /api/admin/analytics` - Get dashboard analytics
- `GET /api/user-stats` - Get user statistics

---

## 🎯 Next Steps

1. ✅ **Create an account** and explore the platform
2. 📄 **Upload your resume** to see AI extraction
3. 🎯 **Select a target role** (AI Engineer, Data Analyst, etc.)
4. 📊 **View your skill gap** report
5. 📚 **Browse learning paths** for missing skills
6. 🎤 **Try mock interviews** with AI feedback
7. 💳 **Subscribe to a plan** for full features
8. 🔐 **Login as admin** to see analytics

---

## 💡 Tips

- 🎨 The UI is fully responsive (works on mobile)
- 🌙 Dark theme for better eye comfort
- ⚡ Fast page transitions with animations
- 💾 Auto-save session (stays logged in)
- 🔒 Secure password hashing with Werkzeug
- 🗄️ Efficient MySQL connection pooling

---

## 🆘 Need Help?

1. Check the terminal/console for error messages
2. Verify MySQL is running
3. Check `.env` file configuration
4. Review `SETUP_GUIDE.md` for detailed instructions
5. Run MySQL queries to verify database setup

---

## 🎉 You're Ready!

**Everything is configured and ready to go!**

1. Double-click `QUICK_START.bat`
2. Wait for "Server is ready!"
3. Open http://localhost:5000
4. Start building your career with AI! 🚀

---

**Made with ❤️ using Flask, MySQL, and AI**
