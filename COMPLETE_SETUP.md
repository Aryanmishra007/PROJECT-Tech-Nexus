# 🚀 Complete NexaAI Setup Guide

## Problem: Login returns 401 Unauthorized

**Root Cause:** The admin user (arynmishra2007@gmail.com) hasn't been created in the database yet.

---

## ✅ Complete Fix - Follow These Steps

### Step 1: Stop Flask (if running)
```
Press Ctrl+C in the terminal
```

### Step 2: Drop and Recreate Database

**Option A: Using MySQL Workbench**
1. Open MySQL Workbench
2. Click on your connection
3. Run these queries in order:

```sql
DROP DATABASE IF EXISTS projectnexai_ai;
CREATE DATABASE projectnexai_ai;
```

**Option B: Using MySQL Command Line**
```bash
mysql -h 127.0.0.1 -u root -p
# Enter password: Aryan@2007

DROP DATABASE IF EXISTS projectnexai_ai;
CREATE DATABASE projectnexai_ai;
EXIT;
```

### Step 3: Verify Dependencies

Run this command:
```bash
pip install flask flask-cors werkzeug PyPDF2 python-docx mysql-connector-python
```

### Step 4: Start Flask
```bash
cd "c:\Users\arynm\OneDrive\Documents\Desktop\project nexa"
python app.py
```

### Step 5: Look for These Messages in Console

You should see:
```
NexaAI — AI-Driven Skill Gap Platform
Starting Flask Server...
============================================================
[NexaAI] MySQL Database ready
[NexaAI] Admin user created: arynmishra2007@gmail.com / Aryan!2007
Running on http://127.0.0.1:5000
```

If you see these, the admin account is created! ✅

### Step 6: Test Database Connection

Open in browser:
```
http://localhost:5000/api/test-db
```

You should see a JSON response listing all users.

### Step 7: Try Login

**Method 1: Admin Login**
- Click "Admin" tab
- Email: `arynmishra2007@gmail.com`
- Password: `Aryan!2007`
- Click "Admin Sign In"

**Method 2: Create Student Account**
- Click "Student" tab
- Click "Create new account"
- Fill in: Name, Email, Password
- Click "Sign Up"
- Then login with that account

---

## 🔍 Troubleshooting

### Error: "Invalid email or password" (after correct credentials)
**Solution:**
1. Stop Flask (Ctrl+C)
2. Delete database: `DROP DATABASE projectnexai_ai;`
3. Create fresh: `CREATE DATABASE projectnexai_ai;`
4. Start Flask again
5. Look for admin creation message in console

### Error: "Can't connect to database"
**Solution:**
1. Make sure MySQL is running
2. Check: Windows Services → MySQL80 → Start
3. Or open MySQL Workbench to verify connection

### Error: "ModuleNotFoundError: No module named 'flask'"
**Solution:**
```bash
pip install flask flask-cors werkzeug PyPDF2 python-docx mysql-connector-python
```

### Login succeeds but dashboard doesn't load
**Solution:**
1. Press F12 (open Developer Tools)
2. Go to Console tab
3. Look for red error messages
4. If you see `/api/auth-check` errors, try hard refresh: Ctrl+F5
5. Clear browser cache and try again

---

## 📋 Quick Reference

### Database Connection
```
Host: 127.0.0.1
User: root
Password: Aryan@2007
Database: projectnexai_ai
Port: 3306
```

### Default Admin Account
```
Email: arynmishra2007@gmail.com
Password: Aryan!2007
```

### Flask Server
```
URL: http://localhost:5000
Method: python app.py
Stop: Ctrl+C
```

### Test Endpoints
```
http://localhost:5000/api/test-db          → Check database users
http://localhost:5000/api/auth-check        → Check login status
```

---

## ✅ Success Indicators

After completing all steps, you should see:

1. **Flask console shows:**
   ```
   [NexaAI] Admin user created: arynmishra2007@gmail.com / Aryan!2007
   Running on http://127.0.0.1:5000
   ```

2. **Database test shows:**
   ```
   {"users": [[1, "arynmishra2007@gmail.com", "admin"]], "user_count": 1}
   ```

3. **Login works:**
   - Enter admin credentials
   - See success toast: "Welcome Admin!"
   - Redirects to analytics dashboard

4. **Admin dashboard appears:**
   - Shows total students
   - Shows total resumes
   - Shows active subscriptions
   - Shows total revenue

---

## 🎯 What to Do After Login Works

### For Admin:
1. View student analytics
2. Monitor skill gaps across batches
3. Track subscription payments
4. View student progress

### For Students:
1. Upload resume
2. View skill analysis report
3. See learning recommendations
4. Choose subscription plan
5. Make payment via UPI QR code
6. Access premium features

---

## 📞 Still Not Working?

1. Check Flask console for error messages
2. Test: `http://localhost:5000/api/test-db`
3. Open browser DevTools (F12) → Console tab
4. Try dropping and recreating database
5. Make sure MySQL is actually running

Good luck! 🚀
