import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from model_bakery import baker
from ninja_jwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    """Django test client for API calls"""
    from django.test import Client
    return Client()


@pytest.fixture
def customer_group(db):
    """Create Customer group"""
    return Group.objects.get_or_create(name='Customer')[0]


@pytest.fixture
def staff_group(db):
    """Create Staff group"""
    return Group.objects.get_or_create(name='Staff')[0]


@pytest.fixture
def admin_group(db):
    """Create Admin group"""
    return Group.objects.get_or_create(name='Admin')[0]


@pytest.fixture
def customer_user(db, customer_group):
    """Create a customer user"""
    user = baker.make(
        User,
        email='customer@example.com',
        first_name='John',
        last_name='Doe',
        is_active=True,
        is_staff=False
    )
    user.set_password('testpass123')
    user.save()
    user.groups.add(customer_group)
    return user


@pytest.fixture
def staff_user(db, staff_group):
    """Create a staff user"""
    user = baker.make(
        User,
        email='staff@example.com',
        first_name='Jane',
        last_name='Staff',
        is_active=True,
        is_staff=True
    )
    user.set_password('testpass123')
    user.save()
    user.groups.add(staff_group)
    return user


@pytest.fixture
def admin_user(db, admin_group):
    """Create an admin user"""
    user = baker.make(
        User,
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    user.set_password('testpass123')
    user.save()
    user.groups.add(admin_group)
    return user


@pytest.fixture
def customer_tokens(customer_user):
    """Generate JWT tokens for customer user"""
    refresh = RefreshToken.for_user(customer_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


@pytest.fixture
def staff_tokens(staff_user):
    """Generate JWT tokens for staff user"""
    refresh = RefreshToken.for_user(staff_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


@pytest.fixture
def admin_tokens(admin_user):
    """Generate JWT tokens for admin user"""
    refresh = RefreshToken.for_user(admin_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


@pytest.fixture
def auth_headers_customer(customer_tokens):
    """Get auth headers for customer"""
    return {'HTTP_AUTHORIZATION': f'Bearer {customer_tokens["access"]}'}


@pytest.fixture
def auth_headers_staff(staff_tokens):
    """Get auth headers for staff"""
    return {'HTTP_AUTHORIZATION': f'Bearer {staff_tokens["access"]}'}


@pytest.fixture
def auth_headers_admin(admin_tokens):
    """Get auth headers for admin"""
    return {'HTTP_AUTHORIZATION': f'Bearer {admin_tokens["access"]}'}
