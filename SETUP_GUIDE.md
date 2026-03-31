# ResumeAI - Career Intelligence Platform Setup Guide

## 🚀 Quick Setup with MySQL

### Step 1: Prerequisites
Make sure you have installed:
- ✅ Python 3.8+ ([Download](https://www.python.org/downloads/))
- ✅ MySQL Server 8.0+ ([Download](https://dev.mysql.com/downloads/mysql/))
- ✅ MySQL Workbench ([Download](https://dev.mysql.com/downloads/workbench/))

### Step 2: Setup MySQL Database

**Option A: Using MySQL Workbench (Recommended)**
1. Open MySQL Workbench
2. Connect to your MySQL server (default: localhost)
3. Click **File → Open SQL Script**
4. Select `database_setup.sql` from the project folder
5. Click **Execute** (⚡ lightning bolt icon)
6. Verify tables are created successfully

**Option B: Using Command Line**
```bash
# Login to MySQL
mysql -u root -p

# Run the setup script
source database_setup.sql

# Or copy-paste the SQL commands
```

### Step 3: Configure Database Connection

1. **Copy the environment template:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file with your MySQL credentials:**
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=resumeai
   
   SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=True
   ```

   ⚠️ **Important:** Replace `your_mysql_password` with your actual MySQL root password!

### Step 4: Install Python Dependencies

```bash
# Navigate to project folder
cd "c:\Users\arynm\OneDrive\Documents\Desktop\project nexa"

# Install all required packages
pip install -r requirements.txt
```

**Packages that will be installed:**
- Flask (web framework)
- Flask-CORS (cross-origin support)
- MySQL Connector (database driver)
- PyPDF2 (PDF parsing)
- python-docx (Word document parsing)
- python-dotenv (environment variables)

### Step 5: Run the Application

```bash
# Start the Flask server with MySQL
python app-mysql.py
```

You should see:
```
════════════════════════════════════════════════════════
🚀 Starting ResumeAI Server with MySQL Database
════════════════════════════════════════════════════════

✅ MySQL Connection Pool created successfully!
✅ Default admin created - Email: admin@resumeai.com, Password: admin123
✅ Database initialized successfully!

════════════════════════════════════════════════════════
✅ Server is ready!
📱 Access the application at: http://localhost:5000
🔐 Admin Login: admin@resumeai.com / admin123
════════════════════════════════════════════════════════
```

### Step 6: Access the Application

1. **Open your browser:** `http://localhost:5000`
2. **Landing Page** will show first with beautiful background
3. **Click "Get Started Free"** to create a student account
4. **Or "Sign In"** with existing credentials

**Default Admin Credentials:**
- Email: `admin@resumeai.com`
- Password: `admin123`
- ⚠️ Change this password after first login!

---

## 🎨 Features Overview

### For Students:
- ✅ **Resume Upload & Analysis** - Upload PDF/DOC resume, AI extracts skills
- ✅ **Skill Gap Report** - Compare your skills with job requirements
- ✅ **Personalized Learning Path** - Get curated courses for missing skills
- ✅ **Mock Interviews** - Practice with AI-powered interview questions
- ✅ **Multiple Pricing Plans** - Basic (₹499), Pro (₹999), Premium (₹1999)

### For Admins:
- 📊 **Analytics Dashboard** - User stats, revenue, skill gaps
- 👥 **User Management** - View all students and subscriptions
- 💰 **Revenue Tracking** - Monitor payments and active subscriptions
- 📈 **Skill Insights** - Common gaps across all students

---

## 🗄️ Database Structure

The application creates **10 tables** in MySQL:

| Table | Purpose |
|-------|---------|
| `users` | User accounts (students & admin) |
| `resumes` | Uploaded resume files and parsed data |
| `user_skills` | Skills extracted from resumes |
| `skill_analysis` | Skill gap analysis results |
| `diagnostic_tests` | Test questions for skills |
| `test_results` | Student test scores |
| `interview_sessions` | Mock interview history |
| `learning_progress` | Course completion tracking |
| `subscriptions` | Active subscription plans |
| `payments` | Payment transactions |

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'mysql'"
**Solution:**
```bash
pip install mysql-connector-python
```

### Error: "Access denied for user 'root'@'localhost'"
**Solution:**
1. Check your MySQL password in `.env` file
2. Or reset MySQL root password:
   ```bash
   mysql -u root -p
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
   FLUSH PRIVILEGES;
   ```

### Error: "Can't connect to MySQL server"
**Solution:**
1. Make sure MySQL service is running
   - **Windows:** Services → MySQL80 → Start
   - **Mac:** System Preferences → MySQL → Start
2. Check if MySQL is listening on port 3306:
   ```bash
   netstat -an | findstr 3306
   ```

### Error: "Database 'resumeai' does not exist"
**Solution:**
Run the database setup script in MySQL Workbench or:
```bash
mysql -u root -p < database_setup.sql
```

### Error: Port 5000 already in use
**Solution:**
Change the port in `app-mysql.py`:
```python
app.run(debug=True, port=5001, host='0.0.0.0')
```

---

## 📊 Verify Database in MySQL Workbench

After running the app, verify everything is working:

```sql
-- Use the database
USE resumeai;

-- Check all tables
SHOW TABLES;

-- View users (should see admin user)
SELECT * FROM users;

-- Check table structure
DESCRIBE users;
DESCRIBE resumes;
DESCRIBE subscriptions;

-- View database size
SELECT 
    table_name AS `Table`,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS `Size (MB)`
FROM information_schema.TABLES
WHERE table_schema = 'resumeai'
ORDER BY (data_length + index_length) DESC;
```

---

## 🎯 Payment Integration

The app supports multiple payment methods:
- 💳 Credit/Debit Cards
- 📱 UPI
- 🏦 Net Banking
- 💰 Razorpay (can be integrated)

**To integrate real payments:**
1. Sign up at [Razorpay](https://razorpay.com/)
2. Get API keys
3. Add to `.env`:
   ```env
   RAZORPAY_KEY_ID=your_key_id
   RAZORPAY_KEY_SECRET=your_secret
   ```
4. Update payment verification in `app-mysql.py`

---

## 📱 Screenshots

The application includes:
- 🌟 **Beautiful Landing Page** with gradient background
- 🎨 **Modern Login/Signup** with glassmorphism effects
- 💼 **Interactive Dashboard** with stats cards
- 📊 **Skill Gap Visualization** with circular progress
- 💰 **Pricing Cards** with plan comparison
- 🔐 **Admin Dashboard** with analytics

---

## 🚀 Production Deployment

For production deployment:

1. **Set environment variables:**
   ```env
   FLASK_DEBUG=False
   SECRET_KEY=generate-strong-random-key
   ```

2. **Use a production MySQL server** (not localhost)

3. **Use Gunicorn or uWSGI:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app-mysql:app
   ```

4. **Setup HTTPS** with Nginx reverse proxy

5. **Enable connection pooling** (already configured)

---

## 📞 Support

If you encounter any issues:
1. Check the terminal/console for error messages
2. Verify MySQL is running
3. Check `.env` file configuration
4. Review MySQL Workbench connection settings

---

## 🎉 You're All Set!

Your ResumeAI platform with MySQL database is now ready! 

**Next Steps:**
1. Create a student account
2. Upload a resume
3. Analyze skills
4. Try mock interviews
5. Login as admin to see analytics

**Enjoy building careers with AI! 🚀**
