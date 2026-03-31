# NexaAI — Setup Instructions

## ✅ Changes Completed

### 1. **Admin Access Control**
- ✅ Admin analytics section now HIDDEN for non-admin users
- ✅ Only shows "Admin" nav section for admin users
- ✅ Sidebar shows user role (Admin/Student)
- ✅ Protected route: Clicking admin without permission shows error

### 2. **QR Code Payment Integration**
- ✅ UPI payment section with QR code display
- ✅ Copy UPI ID button (arynmishra2007@okhdfcbank)
- ✅ Direct UPI app payment link
- ✅ Fallback UI if QR image not found
- ✅ Manual UPI ID entry option

---

## 🚀 Quick Start Guide

### Step 1: Install MySQL
Ensure MySQL server is running on `127.0.0.1:3306`

### Step 2: Create Database
```sql
CREATE DATABASE IF NOT EXISTS projectnexai_ai;
```

### Step 3: Add QR Code Image
Run the batch file to copy your QR code:
```cmd
copy-qr.bat
```

This copies the image to: `payment-qr.png`

### Step 4: Install Dependencies
```cmd
pip install flask flask-cors werkzeug PyPDF2 python-docx mysql-connector-python
```

### Step 5: Run Application
```cmd
python app.py
```

Then open: **http://localhost:5000**

---

## 🔑 Test Accounts

### Admin Login
```
Email: admin@nexaai.com
Password: admin123
```
*Note: Admin will see "Analytics" in sidebar*

### New Student Account
Click "Create an account" to register a new student

---

## 💳 Payment Flow

1. **Student clicks "Pricing Plans"** → See subscription options
2. **Select a plan** → Opens payment modal
3. **Choose payment method:**
   - **UPI**: Shows your QR code + copy button
   - **Card**: Credit/Debit card form
   - **Net Banking**: Bank selection dropdown
4. **UPI QR Code:**
   - Shows `arynmishra2007@okhdfcbank`
   - Click copy button to copy UPI ID
   - Scan QR or use UPI app link

---

## 📁 File Structure

```
project nexa/
├── app.py                    (Flask backend - MySQL)
├── index.html                (Main frontend)
├── script.js                 (Frontend logic - with admin control)
├── style.css                 (Styling - QR styles added)
├── payment-qr.png            (QR code image - run copy-qr.bat)
├── copy-qr.bat               (Helper to copy QR image)
├── start.bat                 (Quick start)
├── requirements.txt          (Python dependencies)
└── utils/
    ├── resume_parser.py
    ├── skill_analyzer.py
    └── ai_service.py
```

---

## ⚙️ Configuration

### MySQL Connection (app.py)
```python
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Aryan@2007',
    'database': 'projectnexai_ai',
}
```

### UPI Payment Details
- **UPI ID**: `arynmishra2007@okhdfcbank`
- **Name**: Aryan Mishra
- **QR Code**: `payment-qr.png` (from your image)

---

## 🔐 Admin Features

Admin users (role='admin') can:
- ✅ Access Analytics dashboard
- ✅ View all user statistics
- ✅ Monitor skill gaps
- ✅ Track revenue & subscriptions
- ✅ See recent registrations

Students cannot access admin features.

---

## ✨ Features

### User Features:
- ✅ Resume upload & parsing
- ✅ Skill gap analysis
- ✅ Diagnostic tests
- ✅ Learning paths
- ✅ Mock interviews
- ✅ ATS suggestions
- ✅ Payment plans

### Admin Features:
- ✅ User analytics
- ✅ Skill gap tracking
- ✅ Revenue monitoring
- ✅ Role-based readiness
- ✅ Interview statistics

---

## 🐛 Troubleshooting

**Q: Admin section not showing?**
A: Log in with admin@nexaai.com / admin123

**Q: QR code not displaying?**
A: Run `copy-qr.bat` to copy the image file

**Q: Payment modal won't open?**
A: Make sure you're logged in and select a plan

**Q: Database connection error?**
A: Ensure MySQL is running and database exists

---

## 📧 Support

For issues, check:
1. MySQL is running
2. Database `projectnexai_ai` exists
3. `payment-qr.png` is in project folder
4. Python dependencies installed

Good to go! 🎉
