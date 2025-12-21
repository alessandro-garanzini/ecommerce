from datetime import datetime
from django.contrib.auth import authenticate, get_user_model
from ninja import Router
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.exceptions import TokenError

from .auth import jwt_auth, admin_jwt_auth, staff_jwt_auth, customer_jwt_auth
from .services.auth_service import AuthService
from .schemas import (
    RegisterSchema,
    LoginSchema,
    TokenResponseSchema,
    RefreshTokenSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    UserSchema,
    MessageSchema
)

User = get_user_model()
auth_service = AuthService()

# Initialize router
router = Router(tags=['Authentication'])


# Endpoints

@router.post('/register', response={201: TokenResponseSchema, 400: MessageSchema}, auth=None)
def register(request, payload: RegisterSchema):
    """
    Register a new user account.
    Returns JWT tokens upon successful registration.
    Role options: 'customer' (default), 'staff', 'admin'
    """
    user, error = auth_service.register_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role
    )
    
    if error:
        return 400, {'message': error}
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    return 201, {
        'access': str(access),
        'refresh': str(refresh),
        'token_type': 'Bearer',
        'expires_in': access.lifetime.total_seconds()
    }


@router.post('/login', response={200: TokenResponseSchema, 401: MessageSchema, 429: MessageSchema}, auth=None)
def login(request, payload: LoginSchema):
    """
    Authenticate a user and return JWT tokens.
    Email and password authentication only.
    """
    email = payload.email.lower().strip()
    
    # Check rate limit (generous: 10 login attempts per 30 minutes per email)
    is_allowed, attempts_remaining = auth_service.check_rate_limit(email, 'login', 10, 30)
    if not is_allowed:
        return 429, {'message': 'Too many login attempts. Please try again later.'}
    
    # Authenticate user
    user = authenticate(request, username=email, password=payload.password)
    
    if user is None:
        # Increment rate limit on failed attempt
        auth_service.increment_rate_limit(email, 'login', 30)
        return 401, {'message': 'Invalid email or password.'}
    
    if not user.is_active:
        return 401, {'message': 'Account is disabled.'}
    
    # Reset rate limit on successful login
    auth_service.reset_rate_limit(email, 'login')
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    # Update last login
    user.last_login = datetime.now()
    user.save(update_fields=['last_login'])
    
    return 200, {
        'access': str(access),
        'refresh': str(refresh),
        'token_type': 'Bearer',
        'expires_in': access.lifetime.total_seconds()
    }


@router.post('/refresh', response={200: TokenResponseSchema, 401: MessageSchema}, auth=None)
def refresh_token(request, payload: RefreshTokenSchema):
    """
    Refresh an access token using a refresh token.
    """
    try:
        refresh = RefreshToken(payload.refresh)
        access = refresh.access_token
        
        return 200, {
            'access': str(access),
            'refresh': str(refresh),
            'token_type': 'Bearer',
            'expires_in': access.lifetime.total_seconds()
        }
    except TokenError as e:
        return 401, {'message': 'Invalid or expired refresh token.'}


@router.post('/logout', response={200: MessageSchema}, auth=jwt_auth)
def logout(request):
    """
    Logout the current user.
    Note: With JWT, logout is primarily handled client-side by removing tokens.
    This endpoint is for consistency and can be extended with token blacklisting.
    """
    # In a production system, you might want to blacklist the token here
    # using Redis or a database table
    return 200, {'message': 'Successfully logged out.'}


@router.get('/me', response=UserSchema, auth=jwt_auth)
def get_current_user(request):
    """
    Get the current authenticated user's information.
    """
    return request.auth


@router.post('/password-reset/request', response={200: MessageSchema, 429: MessageSchema}, auth=None)
def request_password_reset(request, payload: PasswordResetRequestSchema):
    """
    Request a password reset email.
    Always returns success to avoid email enumeration.
    """
    token, error = auth_service.generate_password_reset_token(payload.email)
    
    if error and 'Too many' in error:
        return 429, {'message': error}
    
    # Always return success even if email doesn't exist (security best practice)
    return 200, {
        'message': 'If an account with that email exists, a password reset link has been sent.'
    }


@router.post('/password-reset/confirm', response={200: MessageSchema, 400: MessageSchema}, auth=None)
def confirm_password_reset(request, payload: PasswordResetConfirmSchema):
    """
    Reset password using a valid reset token.
    """
    success, error = auth_service.reset_password(payload.token, payload.new_password)
    
    if not success:
        return 400, {'message': error}
    
    return 200, {'message': 'Password has been reset successfully.'}


# Admin-specific endpoints (example)

@router.get('/admin/users', response=list[UserSchema], auth=admin_jwt_auth)
def list_users_admin(request):
    """
    List all users (admin only).
    """
    users = User.objects.all().order_by('-date_joined')[:100]
    return users


# Customer-specific endpoints (example)

@router.get('/customer/profile', response=UserSchema, auth=customer_jwt_auth)
def get_customer_profile(request):
    """
    Get customer profile (customers only).
    """
    return request.auth
