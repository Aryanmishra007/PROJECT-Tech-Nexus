# Stripe Payment Gateway Setup Instructions

## ✅ What's Been Done
Stripe Test Mode integration has been added to your NexaAI project. The code is ready but requires your Stripe API keys to work.

## 📝 Files Modified
1. **index.html** - Added Stripe.js SDK
2. **app.py** - Added Stripe payment intent creation
3. **script.js** - Added Stripe card element and payment flow
4. **style.css** - Added styling for Stripe card input

## 🔑 Get Your Stripe Keys (FREE)

### Step 1: Create Stripe Account
1. Go to https://stripe.com
2. Click "Sign In" or "Start now" (it's FREE forever in test mode)
3. Create account with email

### Step 2: Get Test API Keys
1. After login, you'll see Dashboard
2. Click "Developers" in top menu
3. Click "API keys" on left sidebar
4. You'll see two keys:
   - **Publishable key** (starts with `pk_test_`)
   - **Secret key** (starts with `sk_test_`) - Click "Reveal test key"

### Step 3: Add Keys to Your Code

**In app.py (line 1038):**
```python
stripe.api_key = 'sk_test_YOUR_SECRET_KEY_HERE'  # Replace this
```

**In script.js (line 1944):**
```javascript
stripe = Stripe('pk_test_YOUR_PUBLISHABLE_KEY_HERE');  // Replace this
```

## 🧪 Testing Stripe Payment

### Test Card Numbers
Use these test cards (they won't charge real money):

✅ **Successful Payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/34)
- CVV: Any 3 digits (e.g., 123)
- Name: Any name

❌ **Card Declined:**
- Card: `4000 0000 0000 0002`

🔄 **Requires Authentication (3D Secure):**
- Card: `4000 0027 6000 3184`

[Full list of test cards](https://stripe.com/docs/testing#cards)

## 🚀 How It Works

1. User clicks "Choose Plan" on pricing page
2. Payment modal opens with Stripe card element
3. User enters test card details
4. Click "Pay Now"
5. Stripe processes payment (in test mode, no real charge)
6. On success, subscription activates in database
7. User sees success message

## 🎯 Demo Mode Fallback
If you don't add Stripe keys, the code automatically falls back to demo mode:
- Still shows payment UI
- Simulates payment without Stripe
- Good for testing other features

## 📊 View Payments in Stripe
1. Go to Stripe Dashboard
2. Click "Payments" on left sidebar
3. See all test transactions
4. Click any payment to see details

## 🔒 Security Notes
- ✅ Test keys are safe to commit to GitHub
- ✅ Never commit live/production keys (they start with `pk_live_` or `sk_live_`)
- ✅ Stripe card element is secure (PCI compliant)
- ✅ Card details never touch your server

## 📦 Install Stripe Library (Backend)
```bash
pip install stripe
```

Then restart your Flask app:
```bash
python app.py
```

## ✨ What's Next?
After adding your Stripe keys:
1. Test payment with test card
2. Check Stripe Dashboard for payment record
3. Push to GitHub (keys are test keys, safe to commit)
4. Deploy to production

## 🆘 Troubleshooting
- **"Stripe not defined" error**: Check if Stripe.js loaded (check browser console)
- **"Invalid API key" error**: Double-check you copied the correct test keys
- **Card element not showing**: Make sure payment method is set to "card"
- **Payment stuck**: Check browser console for errors

---

Made with ❤️ for NexaAI | Test Mode is FREE Forever!
