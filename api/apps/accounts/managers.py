from django.contrib.auth.models import BaseUserManager, Group
from django.db import transaction


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of username.
    Uses Django Groups for role management.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        Superusers are automatically added to the Admin group.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        with transaction.atomic():
            user = self.create_user(email, password, **extra_fields)
            # Import here to avoid circular imports
            from accounts.models.user import UserGroups
            user.add_to_group(UserGroups.ADMIN)
        
        return user
    
    def create_customer(self, email, password=None, **extra_fields):
        """
        Create and save a customer user (for ecommerce frontend).
        Customers are automatically added to the Customer group.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        
        with transaction.atomic():
            user = self.create_user(email, password, **extra_fields)
            # Import here to avoid circular imports
            from accounts.models.user import UserGroups
            user.add_to_group(UserGroups.CUSTOMER)
        
        return user
    
    def create_staff_user(self, email, password=None, **extra_fields):
        """
        Create and save a staff user with backend access.
        Staff users are added to the Staff group and have is_staff=True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        
        with transaction.atomic():
            user = self.create_user(email, password, **extra_fields)
            # Import here to avoid circular imports
            from accounts.models.user import UserGroups
            user.add_to_group(UserGroups.STAFF)
        
        return user
