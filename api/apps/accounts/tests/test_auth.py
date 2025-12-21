import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from ninja_jwt.tokens import RefreshToken, AccessToken
from apps.accounts.auth import JWTAuth, AdminJWTAuth, StaffJWTAuth, CustomerJWTAuth

User = get_user_model()


@pytest.mark.django_db
class TestJWTAuth:
    """Test base JWT authentication"""
    
    def test_jwt_auth_valid_token(self, customer_user):
        """Test JWT authentication with valid token"""
        auth = JWTAuth()
        refresh = RefreshToken.for_user(customer_user)
        token = str(refresh.access_token)
        
        # Simulate request with Authorization header
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        result = auth.authenticate(MockRequest(), token)
        
        assert result is not None
        assert result.id == customer_user.id
        assert result.email == customer_user.email
    
    def test_jwt_auth_invalid_token(self):
        """Test JWT authentication with invalid token"""
        auth = JWTAuth()
        
        class MockRequest:
            headers = {'Authorization': 'Bearer invalid.token.here'}
        
        result = auth.authenticate(MockRequest(), 'invalid.token.here')
        
        assert result is None


@pytest.mark.django_db
class TestAdminJWTAuth:
    """Test admin JWT authentication"""
    
    def test_admin_jwt_auth_success(self, admin_user):
        """Test admin authentication with admin user"""
        auth = AdminJWTAuth()
        refresh = RefreshToken.for_user(admin_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        result = auth.authenticate(MockRequest(), token)
        
        assert result is not None
        assert result.id == admin_user.id
        assert result.is_admin is True
    
    def test_admin_jwt_auth_customer_forbidden(self, customer_user):
        """Test admin auth rejects customer user"""
        auth = AdminJWTAuth()
        refresh = RefreshToken.for_user(customer_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        # AdminJWTAuth returns None for non-admin users
        result = auth.authenticate(MockRequest(), token)
        assert result is None


@pytest.mark.django_db
class TestStaffJWTAuth:
    """Test staff JWT authentication"""
    
    def test_staff_jwt_auth_success(self, staff_user):
        """Test staff authentication with staff user"""
        auth = StaffJWTAuth()
        refresh = RefreshToken.for_user(staff_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        result = auth.authenticate(MockRequest(), token)
        
        assert result is not None
        assert result.id == staff_user.id
        assert result.is_staff_member is True
    
    def test_staff_jwt_auth_admin_allowed(self, admin_user):
        """Test staff auth allows admin user"""
        auth = StaffJWTAuth()
        refresh = RefreshToken.for_user(admin_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        result = auth.authenticate(MockRequest(), token)
        
        assert result is not None
        assert result.id == admin_user.id
    
    def test_staff_jwt_auth_customer_forbidden(self, customer_user):
        """Test staff auth rejects customer user"""
        auth = StaffJWTAuth()
        refresh = RefreshToken.for_user(customer_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        # StaffJWTAuth returns None for non-staff users
        result = auth.authenticate(MockRequest(), token)
        assert result is None


@pytest.mark.django_db
class TestCustomerJWTAuth:
    """Test customer JWT authentication"""
    
    def test_customer_jwt_auth_success(self, customer_user):
        """Test customer authentication with customer user"""
        auth = CustomerJWTAuth()
        refresh = RefreshToken.for_user(customer_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        result = auth.authenticate(MockRequest(), token)
        
        assert result is not None
        assert result.id == customer_user.id
        assert result.is_customer is True
    
    def test_customer_jwt_auth_staff_forbidden(self, staff_user):
        """Test customer auth rejects staff user"""
        auth = CustomerJWTAuth()
        refresh = RefreshToken.for_user(staff_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        # CustomerJWTAuth returns None for non-customer users
        result = auth.authenticate(MockRequest(), token)
        assert result is None
    
    def test_customer_jwt_auth_admin_forbidden(self, admin_user):
        """Test customer auth rejects admin user"""
        auth = CustomerJWTAuth()
        refresh = RefreshToken.for_user(admin_user)
        token = str(refresh.access_token)
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        # CustomerJWTAuth returns None for non-customer users
        result = auth.authenticate(MockRequest(), token)
        assert result is None


@pytest.mark.django_db
class TestTokenGeneration:
    """Test JWT token generation"""
    
    def test_refresh_token_generation(self, customer_user):
        """Test generating refresh token"""
        refresh = RefreshToken.for_user(customer_user)
        
        assert refresh is not None
        assert str(refresh) != ''
    
    def test_access_token_generation(self, customer_user):
        """Test generating access token from refresh"""
        refresh = RefreshToken.for_user(customer_user)
        access = refresh.access_token
        
        assert access is not None
        assert str(access) != ''
        assert str(access) != str(refresh)
    
    def test_token_contains_user_info(self, customer_user):
        """Test that token contains user information"""
        refresh = RefreshToken.for_user(customer_user)
        
        # Token payload should contain user_id
        assert 'user_id' in refresh.payload or refresh.payload.get('user_id')
