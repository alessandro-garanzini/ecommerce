# Authentication System Documentation

## Overview

Email-based JWT authentication system for the ecommerce backend API using **django-ninja-jwt**, with support for both admin and customer users.

## Architecture

### Key Components

- **Custom User Model** ([accounts/models.py](api/accounts/models.py))
  - Email-based authentication (no username field)
  - Django Groups for role management (Customer, Staff, Admin)
  - Password reset token management

- **JWT Authentication** ([accounts/auth.py](api/accounts/auth.py))
  - **django-ninja-jwt** integration (native to Django Ninja)
  - Access tokens: 15 minutes lifetime
  - Refresh tokens: 7 days lifetime
  - Four auth classes: `JWTAuth`, `AdminJWTAuth`, `StaffJWTAuth`, `CustomerJWTAuth`

- **Service Layer** ([accounts/services/auth_service.py](api/accounts/services/auth_service.py))
  - User registration
  - Password reset flow
  - Rate limiting (Redis-backed)

- **API Endpoints** ([accounts/api.py](api/accounts/api.py))
  - Django Ninja routers with typed schemas
  - Comprehensive error handling

## API Endpoints

Base URL: `http://localhost:8000/api/auth/`

### Public Endpoints (No Authentication)

#### 1. Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "is_customer": true
}
```

**Response (201 Created):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

#### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Rate Limiting:** 10 failed attempts per 30 minutes per email

#### 3. Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 4. Request Password Reset
```http
POST /api/auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Rate Limiting:** 10 requests per hour per email

#### 5. Confirm Password Reset
```http
POST /api/auth/password-reset/confirm
Content-Type: application/json

{
  "token": "reset_token_from_email",
  "new_password": "newsecurepass456"
}
```

### Protected Endpoints (Requires JWT)

#### 6. Get Current User
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_staff": false,
  "is_customer": true,
  "is_active": true,
  "date_joined": "2025-12-21T19:59:25Z"
}
```

#### 7. Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

### Admin-Only Endpoints

#### 8. List All Users (Admin)
```http
GET /api/auth/admin/users
Authorization: Bearer <admin_access_token>
```

**Requires:** `is_staff=True`

### Customer-Only Endpoints

#### 9. Get Customer Profile
```http
GET /api/auth/customer/profile
Authorization: Bearer <customer_access_token>
```

**Requires:** `is_customer=True`

## Usage in Next.js Frontend

### Installation
```bash
npm install axios
```

### API Client Setup
```typescript
// lib/api.ts
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {
            refresh: refreshToken,
          });
          
          localStorage.setItem('access_token', data.access);
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return api.request(error.config);
        } catch (refreshError) {
          // Redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

### Authentication Hook
```typescript
// hooks/useAuth.ts
import { useState } from 'react';
import { api } from '@/lib/api';

export const useAuth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const register = async (email: string, password: string, firstName: string, lastName: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post('/auth/register', {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        is_customer: true,
      });
      
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      return data;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post('/auth/login', { email, password });
      
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      return data;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  };

  return { register, login, logout, loading, error };
};
```

## Configuration

### Environment Variables

```bash
# Backend (.env)
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Database
POSTGRES_DB=ecommerce
POSTGRES_USER=ecommerce_user
POSTGRES_PASSWORD=ecommerce_pass_dev_123
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@ecommerce.local

# Frontend URL (for password reset links)
FRONTEND_URL=http://localhost:3000
```

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000` (public frontend)
- `http://localhost:3001` (admin frontend)

Update `CORS_ALLOWED_ORIGINS` in [settings.py](api/core/settings.py) for production domains.

## Rate Limiting

All rate limits are Redis-backed and configured generously:

| Action | Limit | Window |
|--------|-------|--------|
| Login attempts | 10 | 30 minutes |
| Password reset requests | 10 | 1 hour |

Failed attempts are automatically cleared on successful authentication.

## Security Features

1. **Email-Only Authentication**
   - No username field to reduce attack surface
   - Email validated and normalized

2. **JWT Tokens**
   - Short-lived access tokens (15 min)
   - Longer refresh tokens (7 days)
   - Tokens signed with Django SECRET_KEY

3. **Password Security**
   - Minimum 8 characters (enforced in backend)
   - Django's built-in password validators
   - Secure password hashing (PBKDF2)

4. **Rate Limiting**
   - Protects against brute force attacks
   - Graceful degradation if Redis unavailable

5. **CORS Protection**
   - Whitelisted origins only
   - Credentials support enabled

6. **Password Reset**
   - Secure token generation (32-byte URL-safe)
   - 1-hour expiration
   - Email enumeration protection

## Testing the API

### Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Get current user (replace TOKEN)
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

### Interactive API Documentation

Django Ninja provides automatic API documentation:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI Schema:** http://localhost:8000/api/openapi.json

## OAuth Integration (Future)

The authentication system is structured to support OAuth providers in the future:

### Recommended Library
- **django-allauth** or **social-auth-app-django**

### Preparation
- Service layer already separated ([auth_service.py](api/accounts/services/auth_service.py))
- Placeholder for `oauth_provider.py` service
- User model supports both email/password and OAuth flows
- JWT tokens work regardless of authentication method

### Implementation Steps (Future)
1. Install `django-allauth`
2. Configure OAuth providers (Google, GitHub, etc.)
3. Create OAuth endpoints in [accounts/api.py](api/accounts/api.py)
4. Return JWT tokens after OAuth callback
5. Update Next.js frontend with OAuth buttons

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(254) UNIQUE NOT NULL,
  password VARCHAR(128) NOT NULL,
  first_name VARCHAR(150),
  last_name VARCHAR(150),
  is_staff BOOLEAN DEFAULT FALSE,
  is_customer BOOLEAN DEFAULT TRUE,
  is_active BOOLEAN DEFAULT TRUE,
  is_superuser BOOLEAN DEFAULT FALSE,
  date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX users_email_idx ON users(email);
CREATE INDEX users_is_active_idx ON users(is_active);
```

### Password Reset Tokens Table
```sql
CREATE TABLE password_reset_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(64) UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  used BOOLEAN DEFAULT FALSE
);

CREATE INDEX password_reset_tokens_token_idx ON password_reset_tokens(token, used);
```

## Admin Interface

Access the Django admin at: http://localhost:8000/admin/

Default superuser:
- Email: `admin@example.com`
- Password: (set via `createsuperuser` command)

The admin interface allows you to:
- Manage users
- View password reset tokens
- Audit user actions (via django-auditlog)

## Troubleshooting

### Issue: CORS errors in browser
**Solution:** Ensure frontend URL is in `CORS_ALLOWED_ORIGINS` in [settings.py](api/core/settings.py)

### Issue: JWT token expired
**Solution:** Use the refresh token endpoint to get a new access token

### Issue: Password reset email not sent
**Solution:** Check email configuration in environment variables. In development, emails are printed to console.

### Issue: Rate limit hit
**Solution:** Wait for the time window to expire, or clear Redis: `docker compose exec redis redis-cli FLUSHALL`

## Development Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f api

# Create superuser
docker compose exec api python manage.py createsuperuser

# Access Django shell
docker compose exec api python manage.py shell

# Run migrations
docker compose exec api python manage.py migrate

# Create new migrations
docker compose exec api python manage.py makemigrations

# Access Redis CLI
docker compose exec redis redis-cli

# Reset database (WARNING: deletes all data)
docker compose down -v && docker compose up -d --build
```

## Next Steps

1. **Email Provider Setup**
   - Configure SendGrid, AWS SES, or Mailgun for production
   - Update EMAIL_* settings in production environment

2. **Frontend Integration**
   - Implement login/register pages in Next.js
   - Add protected routes with JWT verification
   - Create password reset flow UI

3. **Additional Features**
   - Email verification on registration
   - Two-factor authentication (2FA)
   - OAuth providers (Google, GitHub, etc.)
   - Token blacklisting for logout
   - User profile management endpoints

4. **Production Deployment**
   - Use environment variables for all secrets
   - Enable HTTPS only
   - Configure proper CORS origins
   - Set up email provider
   - Configure Redis persistence
   - Add monitoring and logging
