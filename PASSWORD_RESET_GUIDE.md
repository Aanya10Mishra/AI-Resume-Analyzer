# Password Reset Feature - Complete Guide

## ✅ Features Implemented

### 1. **User Signup** 
- Email validation
- Strong password requirement (8+ chars, uppercase, lowercase, number)
- Role selection (student/employee/hr)
- Account creation with secure hashing

### 2. **User Login**
- Email/password authentication
- Last login timestamp tracking
- Secure password verification

### 3. **Forgot Password** 
- Generate secure reset token
- Token expiry (1 hour)
- Email ready (configure SMTP for production)

### 4. **Password Reset**
- Use reset token to set new password
- Strong password validation
- Token expiry checking

### 5. **Change Password**
- For logged-in users
- Requires current password verification
- Strong password validation

### 6. **User Profile Management**
- Get user details
- Update profile (name, experience level, company, etc.)

---

## 📡 API Endpoints

### **Authentication Endpoints** (Base: `/api/auth`)

#### 1️⃣ **Signup**
```
POST /api/auth/signup
Content-Type: application/json

Body:
{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe",
    "role": "student"  // or "employee", "hr"
}

Response (201):
{
    "message": "Signup successful",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "student",
        "created_at": "2024-01-15T10:30:00"
    },
    "status": "success"
}
```

#### 2️⃣ **Login**
```
POST /api/auth/login
Content-Type: application/json

Body:
{
    "email": "user@example.com",
    "password": "SecurePass123"
}

Response (200):
{
    "message": "Login successful",
    "user": { ... },
    "status": "success"
}
```

#### 3️⃣ **Forgot Password** (Request Reset)
```
POST /api/auth/forgot-password
Content-Type: application/json

Body:
{
    "email": "user@example.com"
}

Response (200):
{
    "message": "Password reset token sent",
    "reset_token": "NvbfqCvqLi2d...",  // Use this token
    "token_expiry": "2024-01-15T11:30:00",
    "status": "success"
}

⚠️  In Production: Send token via EMAIL, not in response
```

#### 4️⃣ **Reset Password**
```
POST /api/auth/reset-password
Content-Type: application/json

Body:
{
    "reset_token": "NvbfqCvqLi2d...",
    "new_password": "NewSecurePass456"
}

Response (200):
{
    "message": "Password reset successfully",
    "status": "success"
}
```

#### 5️⃣ **Change Password** (Logged-in Users)
```
POST /api/auth/change-password/<user_id>
Content-Type: application/json

Body:
{
    "current_password": "OldPass123",
    "new_password": "NewSecurePass456"
}

Response (200):
{
    "message": "Password changed successfully",
    "status": "success"
}
```

#### 6️⃣ **Get User Profile**
```
GET /api/auth/user/<user_id>

Response (200):
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "student",
    "experience_level": "fresher",
    "created_at": "2024-01-15T10:30:00",
    "last_login": "2024-01-15T10:45:00"
}
```

#### 7️⃣ **Update User Profile**
```
PUT /api/auth/user/<user_id>
Content-Type: application/json

Body:
{
    "full_name": "John Smith",
    "experience_level": "junior",
    "company_name": "Tech Corp",
    "department": "Engineering"
}

Response (200):
{
    "message": "Profile updated successfully",
    "user": { ... },
    "status": "success"
}
```

---

## 🎯 Frontend Integration

### 1. **Add Script to index.html**
```html
<!-- In <head> section -->
<script src="password-reset.js"></script>
```

### 2. **Add Forgot Password Link to Login Form**
```html
<button type="button" onclick="showForgotPasswordModal()" 
        class="text-blue-600 hover:underline text-sm">
    Forgot Password?
</button>
```

### 3. **Add Change Password Button to Dashboard/Profile**
```html
<button onclick="showChangePasswordModal()" 
        class="bg-green-600 text-white px-4 py-2 rounded">
    Change Password
</button>
```

---

## 🛡️ Security Features

✅ **Password Hashing** - Uses werkzeug PBKDF2 hashing
✅ **Strong Password Requirements** - 8+ chars, uppercase, lowercase, numbers
✅ **Token Expiration** - Reset tokens valid for 1 hour
✅ **Secure Token Generation** - Uses secrets library (cryptographically secure)
✅ **Email Validation** - RFC 5322 compliant
✅ **Password Verification** - Constant-time comparison
✅ **Account Lockout Ready** - Framework for failed attempt tracking

---

## 📧 Production Setup (Email Integration)

### **Install Flask-Mail**
```bash
pip install Flask-Mail
```

### **Update config.py**
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
MAIL_DEFAULT_SENDER = 'noreply@resumeanalyzer.com'
```

### **Update auth_routes.py - forgot_password()** 
Replace lines around 182-185 with:
```python
from flask_mail import Mail, Message

mail = Mail()

# In forgot_password():
try:
    # ... existing code ...
    
    # Send email
    msg = Message(
        subject='Password Reset Request',
        recipients=[user.email],
        body=f"""
        Click the link to reset your password:
        https://your-domain.com/reset?token={reset_token}
        
        This link expires in 1 hour.
        """
    )
    mail.send(msg)
    
    # Remove from response for security
    return jsonify({
        'message': 'Password reset instructions sent to email',
        'status': 'success'
    }), 200
```

---

## 🧪 Testing the Feature

### **Test with cURL**

1. **Signup**
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User",
    "role": "student"
  }'
```

2. **Forgot Password**
```bash
curl -X POST http://localhost:5000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

3. **Reset Password** (use token from step 2)
```bash
curl -X POST http://localhost:5000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "reset_token": "YOUR_TOKEN_HERE",
    "new_password": "NewTestPass456"
  }'
```

4. **Login with new password**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "NewTestPass456"
  }'
```

---

## 🚀 Deployment Checklist

- [ ] Add `Flask-Mail` to `requirements.txt`
- [ ] Update `config.py` with email settings
- [ ] Implement email sending in `auth_routes.py`
- [ ] Update `app.py` to initialize Mail
- [ ] Add `password-reset.js` to frontend
- [ ] Update login form with "Forgot Password" link
- [ ] Add "Change Password" button to user profile
- [ ] Update `index.html` to include `password-reset.js`
- [ ] Test all endpoints locally
- [ ] Deploy to production (Render/Railway)
- [ ] Set environment variables for email credentials

---

## 📊 Database Schema

**Users Table** (already exists):
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    experience_level VARCHAR(50),
    company_name VARCHAR(200),
    department VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

**Reset Tokens** (in-memory for now, use database in production):
```python
password_reset_tokens = {
    'token_string': {
        'user_id': 1,
        'email': 'user@example.com',
        'expiry': datetime(2024, 1, 15, 11, 30, 0)
    }
}
```

---

## 🐛 Troubleshooting

### **"Invalid email or password" on login**
- Check if user exists: `SELECT * FROM users WHERE email = 'email@example.com';`
- Verify password hash matches

### **Reset token expires too quickly**
- Increase expiry time in `forgot_password()`: `timedelta(hours=2)`

### **Token not working**
- Ensure token hasn't expired (1 hour default)
- Check token is copied correctly (no extra spaces)

### **Password validation fails**
- Password must have: 8+ chars, uppercase, lowercase, number
- Example: `SecurePass123` ✅

---

## 📝 API Response Codes

| Status | Code | Meaning |
|--------|------|---------|
| Success | 200 | Request completed successfully |
| Created | 201 | New resource created (signup) |
| Bad Request | 400 | Invalid input |
| Unauthorized | 401 | Invalid credentials or token |
| Conflict | 409 | Email already exists |
| Not Found | 404 | User not found |
| Server Error | 500 | Internal error |

---

## 🎓 Next Steps

1. ✅ Copy `auth_routes.py` to `backend/routes/`
2. ✅ Update `app.py` to import and register auth_bp
3. ✅ Copy `password-reset.js` to `front/`
4. ✅ Add script link to `index.html`
5. ✅ Update login form with "Forgot Password" button
6. ✅ Test locally
7. ✅ Deploy to Render/Railway
8. ✅ Set up email in production

---

**Questions? Check the API endpoints above or test with cURL!**
