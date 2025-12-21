from typing import Optional, Any
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja.security import HttpBearer
from ninja_jwt.tokens import AccessToken
from ninja_jwt.exceptions import TokenError, InvalidToken

User = get_user_model()


class JWTAuth(HttpBearer):
    """
    JWT Authentication for Django Ninja.
    Validates JWT tokens and attaches the user to the request.
    """
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        """
        Authenticate a request using JWT token.
        
        Args:
            request: The HTTP request
            token: The JWT token from Authorization header
        
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Validate the access token
            access_token = AccessToken(token)
            
            # Get user ID from token
            user_id = access_token.get('user_id')
            if not user_id:
                return None
            
            # Fetch user from database
            try:
                user = User.objects.get(id=user_id, is_active=True)
                return user
            except User.DoesNotExist:
                return None
                
        except (TokenError, InvalidToken) as e:
            # Token is invalid or expired
            return None
        except Exception as e:
            # Unexpected error
            print(f"JWT authentication error: {e}")
            return None


class AdminJWTAuth(JWTAuth):
    """
    JWT Authentication for admin-only endpoints.
    Requires user to be in Admin group or be a superuser.
    """
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        
        if user and user.is_admin:
            return user
        
        return None


class StaffJWTAuth(JWTAuth):
    """
    JWT Authentication for staff endpoints.
    Requires user to be in Staff group or have is_staff flag.
    """
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        
        if user and (user.is_staff_member or user.is_staff):
            return user
        
        return None


class CustomerJWTAuth(JWTAuth):
    """
    JWT Authentication for customer-only endpoints.
    Requires user to be in Customer group.
    """
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        
        if user and user.is_customer:
            return user
        
        return None


# Convenience instances for use in API endpoints
jwt_auth = JWTAuth()
admin_jwt_auth = AdminJWTAuth()
staff_jwt_auth = StaffJWTAuth()
customer_jwt_auth = CustomerJWTAuth()
