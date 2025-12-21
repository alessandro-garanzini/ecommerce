# Authentication System - Quick Reference

## ✅ What's Implemented

### Core Features
- ✅ Email-based authentication (no username)
- ✅ JWT access tokens (15 min) + refresh tokens (7 days) using **django-ninja-jwt**
- ✅ Django Groups & Permissions for role management (Customer, Staff, Admin)
- ✅ User registration with automatic token generation
- ✅ Login with email/password
- ✅ Password reset flow (email-based)
- ✅ Rate limiting (Redis-backed, generous limits)
- ✅ CORS configured for Next.js frontends
- ✅ Role-based access control with multiple auth classes
- ✅ Interactive API documentation (Swagger UI)

### API Endpoints
All endpoints at: `http://localhost:8000/api/auth/`

**Public:**
- `POST /register` - Create new account
- `POST /login` - Authenticate and get tokens
- `POST /refresh` - Refresh access token
- `POST /password-reset/request` - Request password reset
- `POST /password-reset/confirm` - Reset password with token

**Protected (JWT required):**
- `GET /me` - Get current user info
- `POST /logout` - Logout (client-side token removal)

**Admin Only:**
- `GET /admin/users` - List all users

**Customer Only:**
- `GET /customer/profile` - Get customer profile

## 🚀 Quick Start

### 1. Start the Backend
```bash
docker compose up -d
```

### 2. Test the API
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass12345", "first_name": "John"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass12345"}'
```

### 3. View API Docs
Open: http://localhost:8000/api/docs

## 📦 File Structure

```
api/
├── accounts/
│   ├── models.py           # Custom User model
│   ├── managers.py         # User manager (create_user, create_customer)
│   ├── admin.py            # Django admin config
│   ├── auth.py             # JWT authentication classes
│   ├── api.py              # API endpoints (Django Ninja)
│   └── services/
│       └── auth_service.py # Business logic (registration, rate limiting)
├── core/
│   ├── settings.py         # JWT, CORS, email config
│   └── urls.py             # API router registration
└── requirements.txt        # Updated with JWT & CORS packages
```

## 🔐 Security Features

1. **Rate Limiting**
   - Login: 10 attempts / 30 min
   - Password reset: 10 requests / hour
   - Redis-backed, fails open if Redis unavailable

2. **JWT Tokens**
   - Access: 15 min (short-lived)
   - Refresh: 7 days
   - HS256 algorithm with Django SECRET_KEY

3. **Password Security**
   - Min 8 characters
   - Django validators (common passwords, similarity, etc.)
   - PBKDF2 hashing

4. **Email Protection**
   - No email enumeration on password reset
   - Email normalized (lowercase, trimmed)

## 🎯 Next.js Integration

### Environment Variable
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Example Usage
```typescript
// Login
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
});
const { access, refresh } = await response.json();
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);

// Authenticated request
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
  headers: { 
    'Authorization': `Bearer ${localStorage.getItem('access_token')}` 
  },
});
```

## 🛠️ Configuration

### CORS Origins
Default: `http://localhost:3000,http://localhost:3001`
Update in [core/settings.py](api/core/settings.py) line ~140

### Email Backend
Default: Console (prints to docker logs)
For production, update EMAIL_* settings in [core/settings.py](api/core/settings.py)

### Rate Limits
Modify in [accounts/services/auth_service.py](api/accounts/services/auth_service.py):
- `check_rate_limit(email, 'login', 10, 30)` - 10 attempts, 30 min window
- `check_rate_limit(email, 'password_reset', 10, 60)` - 10 requests, 60 min window

## 📝 Admin Panel

URL: http://localhost:8000/admin/
Default superuser: `admin@example.com` (password set via createsuperuser)

## 🔮 Future: OAuth Integration

The system is structured to easily add OAuth (Google, GitHub, etc.):

1. Install `django-allauth`
2. Add OAuth provider config to settings
3. Create OAuth endpoints in `accounts/api.py`
4. Return JWT tokens after OAuth callback
5. No changes needed to existing endpoints

All authentication flows (password, OAuth) return the same JWT tokens.

## 📚 Full Documentation

See [AUTH_DOCUMENTATION.md](AUTH_DOCUMENTATION.md) for:
- Detailed API specs
- Next.js integration examples (hooks, axios setup)
- Database schema
- Troubleshooting guide
- Production deployment checklist
