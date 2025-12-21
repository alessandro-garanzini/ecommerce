"""
OAuth Provider Service - Placeholder for Future Implementation

This service will handle OAuth authentication flows for providers like:
- Google
- GitHub  
- Facebook
- Apple
- Microsoft

When implementing OAuth, use this pattern to maintain consistency
with the existing JWT authentication system.
"""

from typing import Optional, Tuple, Dict
from django.contrib.auth import get_user_model
from django.db import transaction
from ninja_jwt.tokens import RefreshToken

User = get_user_model()


class OAuthProviderService:
    """
    Service for handling OAuth authentication flows.
    
    Recommended Libraries:
    - django-allauth: https://django-allauth.readthedocs.io/
    - social-auth-app-django: https://python-social-auth.readthedocs.io/
    
    Both libraries integrate well with Django and support multiple providers.
    """
    
    def authenticate_with_google(self, code: str, redirect_uri: str) -> Tuple[Optional[User], Optional[str], Optional[Dict]]:
        """
        Authenticate user with Google OAuth.
        
        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in OAuth flow
            
        Returns:
            Tuple of (user, error_message, tokens)
            tokens = {'access': str, 'refresh': str, 'expires_in': int}
        """
        # TODO: Implement Google OAuth flow
        # 1. Exchange code for Google access token
        # 2. Get user info from Google API
        # 3. Find or create user with email
        # 4. Generate JWT tokens
        # 5. Return user and tokens
        raise NotImplementedError("OAuth not yet implemented")
    
    def authenticate_with_github(self, code: str, redirect_uri: str) -> Tuple[Optional[User], Optional[str], Optional[Dict]]:
        """
        Authenticate user with GitHub OAuth.
        """
        # TODO: Implement GitHub OAuth flow
        raise NotImplementedError("OAuth not yet implemented")
    
    def link_oauth_account(self, user: User, provider: str, provider_user_id: str, access_token: str) -> bool:
        """
        Link an OAuth account to an existing user.
        
        This allows users to login with either:
        - Email/password (existing system)
        - OAuth provider (new)
        """
        # TODO: Create a model to store OAuth connections
        # OAuthConnection model should have:
        # - user (FK to User)
        # - provider (str: 'google', 'github', etc.)
        # - provider_user_id (str: unique ID from provider)
        # - access_token (str: encrypted)
        # - refresh_token (str: encrypted, nullable)
        # - created_at, updated_at
        raise NotImplementedError("OAuth linking not yet implemented")
    
    def get_or_create_user_from_oauth(
        self, 
        email: str, 
        provider: str,
        provider_user_id: str,
        first_name: str = '',
        last_name: str = ''
    ) -> Tuple[User, bool]:
        """
        Get existing user by email or create a new one.
        
        Returns:
            Tuple of (user, created)
        """
        try:
            # Try to find existing user
            user = User.objects.get(email=email.lower().strip())
            created = False
        except User.DoesNotExist:
            # Create new user (OAuth users don't need a password)
            with transaction.atomic():
                user = User.objects.create_customer(
                    email=email.lower().strip(),
                    first_name=first_name,
                    last_name=last_name
                )
                # Set unusable password for OAuth-only accounts
                user.set_unusable_password()
                user.save()
            created = True
        
        return user, created
    
    def generate_jwt_tokens_for_user(self, user: User) -> Dict[str, any]:
        """
        Generate JWT tokens for a user (same as password auth).
        
        This ensures OAuth and password authentication return the same token format.
        """
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        return {
            'access': str(access),
            'refresh': str(refresh),
            'token_type': 'Bearer',
            'expires_in': access.lifetime.total_seconds()
        }


"""
Example API Endpoints (to add to accounts/api.py):

@router.get('/oauth/google/login', auth=None)
def google_oauth_login(request):
    \"\"\"
    Redirect to Google OAuth consent screen.
    \"\"\"
    # Build Google OAuth URL with client_id, redirect_uri, scope
    # Return redirect URL to frontend
    pass

@router.post('/oauth/google/callback', auth=None)
def google_oauth_callback(request, code: str):
    \"\"\"
    Handle Google OAuth callback.
    Returns JWT tokens.
    \"\"\"
    oauth_service = OAuthProviderService()
    user, error, tokens = oauth_service.authenticate_with_google(
        code=code,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    
    if error:
        return 400, {'message': error}
    
    return 200, tokens

@router.post('/oauth/link', auth=jwt_auth)
def link_oauth_account(request, provider: str, code: str):
    \"\"\"
    Link OAuth account to existing authenticated user.
    \"\"\"
    # Verify code with provider
    # Link to request.auth (current user)
    pass
"""
