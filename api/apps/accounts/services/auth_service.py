import secrets
import hashlib
from datetime import timedelta
from typing import Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
import redis

User = get_user_model()


class AuthService:
    """
    Service layer for authentication operations including registration,
    password reset, and rate limiting.
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
    
    # Rate Limiting
    
    def check_rate_limit(self, identifier: str, action: str, max_attempts: int, window_minutes: int) -> Tuple[bool, int]:
        """
        Check if an action is rate limited for a given identifier.
        
        Args:
            identifier: Email or IP address
            action: Action type (e.g., 'login', 'password_reset')
            max_attempts: Maximum number of attempts allowed
            window_minutes: Time window in minutes
        
        Returns:
            Tuple of (is_allowed, attempts_remaining)
        """
        key = f'rate_limit:{action}:{identifier}'
        try:
            current_count = self.redis_client.get(key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            if current_count >= max_attempts:
                return False, 0
            
            return True, max_attempts - current_count
        except Exception as e:
            # If Redis is down, allow the action (fail open for better UX)
            print(f"Rate limit check failed: {e}")
            return True, max_attempts
    
    def increment_rate_limit(self, identifier: str, action: str, window_minutes: int):
        """
        Increment the rate limit counter for an action.
        """
        key = f'rate_limit:{action}:{identifier}'
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_minutes * 60)
            pipe.execute()
        except Exception as e:
            print(f"Rate limit increment failed: {e}")
    
    def reset_rate_limit(self, identifier: str, action: str):
        """
        Reset rate limit counter (e.g., after successful login).
        """
        key = f'rate_limit:{action}:{identifier}'
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Rate limit reset failed: {e}")
    
    # User Registration
    
    def register_user(self, email: str, password: str, first_name: str = '', 
                     last_name: str = '', role: str = 'customer') -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user with a specified role.
        
        Args:
            email: User's email address
            password: User's password
            first_name: User's first name
            last_name: User's last name
            role: User role - 'customer' (default), 'staff', or 'admin'
        
        Returns:
            Tuple of (user, error_message)
        """
        email = email.lower().strip()
        role = role.lower()
        
        # Validate role
        valid_roles = ['customer', 'staff', 'admin']
        if role not in valid_roles:
            return None, f'Invalid role. Must be one of: {", ".join(valid_roles)}'
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return None, 'A user with this email already exists.'
        
        # Validate password strength (basic validation)
        if len(password) < 8:
            return None, 'Password must be at least 8 characters long.'
        
        try:
            with transaction.atomic():
                if role == 'customer':
                    user = User.objects.create_customer(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                elif role == 'staff':
                    user = User.objects.create_staff_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                elif role == 'admin':
                    # Creating admin users might require additional security checks
                    user = User.objects.create_superuser(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                
                return user, None
        except Exception as e:
            return None, f'Registration failed: {str(e)}'
    
    # Password Reset
    
    def generate_password_reset_token(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a password reset token for a user.
        
        Returns:
            Tuple of (token, error_message)
        """
        email = email.lower().strip()
        
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            return None, None
        
        # Check rate limit (generous: 10 requests per hour per email)
        is_allowed, _ = self.check_rate_limit(email, 'password_reset', 10, 60)
        if not is_allowed:
            return None, 'Too many password reset requests. Please try again later.'
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Store in Redis with 1 hour expiration
        redis_key = f'password_reset:{token}'
        try:
            self.redis_client.setex(
                redis_key,
                3600,  # 1 hour
                user.id
            )
        except Exception as e:
            print(f"Redis storage failed: {e}")
            # Fallback: store in database
            from accounts.models import PasswordResetToken
            expires_at = timezone.now() + timedelta(hours=1)
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
        
        # Increment rate limit
        self.increment_rate_limit(email, 'password_reset', 60)
        
        # Send email
        self._send_password_reset_email(user, token)
        
        return token, None
    
    def verify_password_reset_token(self, token: str) -> Optional[User]:
        """
        Verify a password reset token and return the associated user.
        """
        redis_key = f'password_reset:{token}'
        
        try:
            # Try Redis first
            user_id = self.redis_client.get(redis_key)
            if user_id:
                try:
                    return User.objects.get(id=int(user_id), is_active=True)
                except User.DoesNotExist:
                    return None
        except Exception as e:
            print(f"Redis verification failed: {e}")
        
        # Fallback: check database
        from accounts.models import PasswordResetToken
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(
                token=token,
                used=False
            )
            if reset_token.is_valid():
                return reset_token.user
        except PasswordResetToken.DoesNotExist:
            pass
        
        return None
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Reset user password using a valid token.
        
        Returns:
            Tuple of (success, error_message)
        """
        user = self.verify_password_reset_token(token)
        if not user:
            return False, 'Invalid or expired password reset token.'
        
        # Validate password strength
        if len(new_password) < 8:
            return False, 'Password must be at least 8 characters long.'
        
        try:
            with transaction.atomic():
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                # Invalidate token in Redis
                redis_key = f'password_reset:{token}'
                try:
                    self.redis_client.delete(redis_key)
                except Exception:
                    pass
                
                # Mark token as used in database (if exists)
                from accounts.models import PasswordResetToken
                PasswordResetToken.objects.filter(token=token).update(used=True)
                
                return True, None
        except Exception as e:
            return False, f'Password reset failed: {str(e)}'
    
    # Email Sending
    
    def _send_password_reset_email(self, user: User, token: str):
        """
        Send password reset email to user.
        """
        # In production, you'd construct a proper frontend URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        subject = 'Password Reset Request'
        message = f"""
        Hi {user.get_short_name()},
        
        You requested to reset your password. Click the link below to reset it:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        The Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
