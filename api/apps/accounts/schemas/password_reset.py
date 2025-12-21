from ninja import Schema


class PasswordResetRequestSchema(Schema):
    """Password reset request schema"""
    email: str


class PasswordResetConfirmSchema(Schema):
    """Password reset confirmation schema"""
    token: str
    new_password: str
