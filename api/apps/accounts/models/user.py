from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from accounts.managers import CustomUserManager


# Group name constants
class UserGroups:
    """Constants for user group names."""
    CUSTOMER = 'Customer'
    STAFF = 'Staff'
    ADMIN = 'Admin'


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email for authentication instead of username.
    Uses Django's Groups system for role management instead of boolean flags.
    
    Available Groups:
    - Customer: Regular ecommerce customers
    - Staff: Staff members with backend access
    - Admin: Full system administrators
    """
    
    email = models.EmailField(
        'email address',
        unique=True,
        db_index=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        },
    )
    first_name = models.CharField('first name', max_length=150, blank=True)
    last_name = models.CharField('last name', max_length=150, blank=True)
    
    # Django's built-in flags
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into the admin site.',
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user should be treated as active.',
    )
    
    # Timestamps
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    last_login = models.DateTimeField('last login', blank=True, null=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required by USERNAME_FIELD
    
    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email
    
    # Role checking methods using Django Groups
    
    def is_in_group(self, group_name: str) -> bool:
        """Check if user belongs to a specific group."""
        return self.groups.filter(name=group_name).exists()
    
    @property
    def is_customer(self) -> bool:
        """Check if user is a customer."""
        return self.is_in_group(UserGroups.CUSTOMER)
    
    @property
    def is_staff_member(self) -> bool:
        """Check if user is a staff member."""
        return self.is_in_group(UserGroups.STAFF) or self.is_staff
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.is_in_group(UserGroups.ADMIN) or self.is_superuser
    
    def add_to_group(self, group_name: str):
        """Add user to a group (creates group if it doesn't exist)."""
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name=group_name)
        self.groups.add(group)
    
    def remove_from_group(self, group_name: str):
        """Remove user from a group."""
        from django.contrib.auth.models import Group
        try:
            group = Group.objects.get(name=group_name)
            self.groups.remove(group)
        except Group.DoesNotExist:
            pass
    
    def get_role_display(self) -> str:
        """Get user's primary role for display."""
        if self.is_superuser:
            return 'Superuser'
        elif self.is_admin:
            return 'Admin'
        elif self.is_staff_member:
            return 'Staff'
        elif self.is_customer:
            return 'Customer'
        return 'User'
