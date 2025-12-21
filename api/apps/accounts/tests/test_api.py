import pytest
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
class TestRegisterEndpoint:
    """Test user registration endpoint"""
    
    def test_register_customer_success(self, api_client, customer_group):
        """Test successful customer registration"""
        payload = {
            'email': 'newcustomer@example.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Customer',
            'role': 'customer'
        }
        
        response = api_client.post(
            '/api/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert data['token_type'] == 'Bearer'
        assert 'expires_in' in data
        
        # Verify user was created
        user = User.objects.get(email='newcustomer@example.com')
        assert user.first_name == 'New'
        assert user.last_name == 'Customer'
        assert user.check_password('securepass123')
        assert user.groups.filter(name='Customer').exists()
    
    def test_register_staff_success(self, api_client, staff_group):
        """Test successful staff registration"""
        payload = {
            'email': 'newstaff@example.com',
            'password': 'securepass123',
            'role': 'staff'
        }
        
        response = api_client.post(
            '/api/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        user = User.objects.get(email='newstaff@example.com')
        assert user.is_staff
        assert user.groups.filter(name='Staff').exists()
    
    def test_register_duplicate_email(self, api_client, customer_user):
        """Test registration with existing email"""
        payload = {
            'email': 'customer@example.com',
            'password': 'securepass123'
        }
        
        response = api_client.post(
            '/api/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'message' in data
        assert 'already exists' in data['message'].lower()
    
    def test_register_default_role(self, api_client, customer_group):
        """Test registration defaults to customer role"""
        payload = {
            'email': 'defaultrole@example.com',
            'password': 'securepass123'
        }
        
        response = api_client.post(
            '/api/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        user = User.objects.get(email='defaultrole@example.com')
        assert user.groups.filter(name='Customer').exists()


@pytest.mark.django_db
class TestLoginEndpoint:
    """Test login endpoint"""
    
    def test_login_success(self, api_client, customer_user):
        """Test successful login"""
        payload = {
            'email': 'customer@example.com',
            'password': 'testpass123'
        }
        
        response = api_client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert data['token_type'] == 'Bearer'
    
    def test_login_wrong_password(self, api_client, customer_user):
        """Test login with wrong password"""
        payload = {
            'email': 'customer@example.com',
            'password': 'wrongpassword'
        }
        
        response = api_client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'message' in data
    
    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent email"""
        payload = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = api_client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_login_inactive_user(self, api_client, customer_user):
        """Test login with inactive user"""
        customer_user.is_active = False
        customer_user.save()
        
        payload = {
            'email': 'customer@example.com',
            'password': 'testpass123'
        }
        
        response = api_client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Django's authenticate() returns None for inactive users
        assert response.status_code == 401
        data = response.json()
        assert 'message' in data
    
    def test_login_case_insensitive_email(self, api_client, customer_user):
        """Test login with uppercase email"""
        payload = {
            'email': 'CUSTOMER@EXAMPLE.COM',
            'password': 'testpass123'
        }
        
        response = api_client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestRefreshTokenEndpoint:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, api_client, customer_tokens):
        """Test successful token refresh"""
        payload = {
            'refresh': customer_tokens['refresh']
        }
        
        response = api_client.post(
            '/api/auth/refresh',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert data['access'] != customer_tokens['access']  # New access token
    
    def test_refresh_token_invalid(self, api_client):
        """Test refresh with invalid token"""
        payload = {
            'refresh': 'invalid.token.here'
        }
        
        response = api_client.post(
            '/api/auth/refresh',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'message' in data


@pytest.mark.django_db
class TestLogoutEndpoint:
    """Test logout endpoint"""
    
    def test_logout_success(self, api_client, auth_headers_customer):
        """Test successful logout"""
        response = api_client.post(
            '/api/auth/logout',
            **auth_headers_customer
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
    
    def test_logout_without_auth(self, api_client):
        """Test logout without authentication"""
        response = api_client.post('/api/auth/logout')
        
        assert response.status_code == 401


@pytest.mark.django_db
class TestGetCurrentUserEndpoint:
    """Test /me endpoint"""
    
    def test_get_current_user_success(self, api_client, customer_user, auth_headers_customer):
        """Test getting current user info"""
        response = api_client.get(
            '/api/auth/me',
            **auth_headers_customer
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == 'customer@example.com'
        assert data['first_name'] == 'John'
        assert data['last_name'] == 'Doe'
        assert 'Customer' in data['groups']
        assert data['is_customer'] is True
    
    def test_get_current_user_without_auth(self, api_client):
        """Test /me without authentication"""
        response = api_client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_get_current_user_staff(self, api_client, staff_user, auth_headers_staff):
        """Test getting staff user info"""
        response = api_client.get(
            '/api/auth/me',
            **auth_headers_staff
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == 'staff@example.com'
        assert 'Staff' in data['groups']
        assert data['is_staff'] is True


@pytest.mark.django_db
class TestPasswordResetEndpoints:
    """Test password reset flow"""
    
    def test_password_reset_request_success(self, api_client, customer_user):
        """Test password reset request"""
        # Reset rate limit before test
        from apps.accounts.services.auth_service import AuthService
        auth_service = AuthService()
        auth_service.reset_rate_limit('customer@example.com', 'password_reset')
        
        payload = {
            'email': 'customer@example.com'
        }
        
        response = api_client.post(
            '/api/auth/password-reset/request',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
    
    def test_password_reset_request_nonexistent_email(self, api_client):
        """Test password reset with non-existent email (should still return success)"""
        payload = {
            'email': 'nonexistent@example.com'
        }
        
        response = api_client.post(
            '/api/auth/password-reset/request',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return 200 to avoid email enumeration
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    def test_list_users_admin_success(self, api_client, admin_user, auth_headers_admin, customer_user, staff_user):
        """Test admin can list all users"""
        response = api_client.get(
            '/api/auth/admin/users',
            **auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # admin, customer, staff
    
    def test_list_users_customer_forbidden(self, api_client, auth_headers_customer):
        """Test customer cannot access admin endpoint"""
        response = api_client.get(
            '/api/auth/admin/users',
            **auth_headers_customer
        )
        
        # AdminJWTAuth returns None for non-admin, which results in 401
        assert response.status_code == 401
    
    def test_list_users_staff_forbidden(self, api_client, auth_headers_staff):
        """Test staff cannot access admin endpoint"""
        response = api_client.get(
            '/api/auth/admin/users',
            **auth_headers_staff
        )
        
        # AdminJWTAuth returns None for non-admin, which results in 401
        assert response.status_code == 401


@pytest.mark.django_db
class TestCustomerEndpoints:
    """Test customer-only endpoints"""
    
    def test_customer_profile_success(self, api_client, customer_user, auth_headers_customer):
        """Test customer can access their profile"""
        response = api_client.get(
            '/api/auth/customer/profile',
            **auth_headers_customer
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == 'customer@example.com'
    
    def test_customer_profile_staff_forbidden(self, api_client, auth_headers_staff):
        """Test staff cannot access customer endpoint"""
        response = api_client.get(
            '/api/auth/customer/profile',
            **auth_headers_staff
        )
        
        # CustomerJWTAuth returns None for non-customer, which results in 401
        assert response.status_code == 401
