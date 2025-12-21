from typing import Optional
from ninja import Schema


class RegisterSchema(Schema):
    """User registration schema"""
    email: str
    password: str
    first_name: Optional[str] = ''
    last_name: Optional[str] = ''
    role: Optional[str] = 'customer'  # 'customer', 'staff', or 'admin'


class LoginSchema(Schema):
    """User login schema"""
    email: str
    password: str


class TokenResponseSchema(Schema):
    """JWT token response schema"""
    access: str
    refresh: str
    token_type: str = 'Bearer'
    expires_in: int  # seconds


class RefreshTokenSchema(Schema):
    """Token refresh request schema"""
    refresh: str
