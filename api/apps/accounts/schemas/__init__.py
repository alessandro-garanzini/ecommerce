"""
Accounts app schemas.

This package contains all Pydantic/Ninja schemas used for API validation and serialization.
Schemas are organized by category for better maintainability.
"""

from .auth import (
    RegisterSchema,
    LoginSchema,
    TokenResponseSchema,
    RefreshTokenSchema
)
from .user import UserSchema
from .password_reset import (
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema
)
from .common import MessageSchema

__all__ = [
    # Authentication
    'RegisterSchema',
    'LoginSchema',
    'TokenResponseSchema',
    'RefreshTokenSchema',
    
    # User
    'UserSchema',
    
    # Password Reset
    'PasswordResetRequestSchema',
    'PasswordResetConfirmSchema',
    
    # Common
    'MessageSchema',
]
