from django.db import models
from django.utils import timezone

from .user import User

class PasswordResetToken(models.Model):
    """
    Stores password reset tokens with expiration.
    Uses Redis for temporary storage but DB as fallback.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'password reset token'
        verbose_name_plural = 'password reset tokens'
        indexes = [
            models.Index(fields=['token', 'used']),
        ]
    
    def __str__(self):
        return f'Password reset for {self.user.email}'
    
    def is_valid(self):
        """Check if token is still valid (not used and not expired)."""
        return not self.used and timezone.now() < self.expires_at
