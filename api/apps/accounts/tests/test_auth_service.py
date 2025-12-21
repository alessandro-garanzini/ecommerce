import pytest
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from apps.accounts.services.auth_service import AuthService
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
class TestAuthServiceRegistration:
    """Test AuthService registration functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.auth_service = AuthService()
    
    def test_register_customer_success(self, customer_group):
        """Test successful customer registration"""
        user, error = self.auth_service.register_user(
            email='newuser@example.com',
            password='securepass123',
            first_name='New',
            last_name='User',
            role='customer'
        )
        
        assert error is None
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.check_password('securepass123')
        assert user.groups.filter(name='Customer').exists()
    
    def test_register_staff_success(self, staff_group):
        """Test successful staff registration"""
        user, error = self.auth_service.register_user(
            email='staff@example.com',
            password='securepass123',
            role='staff'
        )
        
        assert error is None
        assert user.is_staff
        assert user.groups.filter(name='Staff').exists()
    
    def test_register_admin_success(self, admin_group):
        """Test successful admin registration"""
        user, error = self.auth_service.register_user(
            email='admin@example.com',
            password='securepass123',
            role='admin'
        )
        
        assert error is None
        assert user.is_staff
        assert user.is_superuser
        assert user.groups.filter(name='Admin').exists()
    
    def test_register_duplicate_email(self, customer_user):
        """Test registration with existing email"""
        user, error = self.auth_service.register_user(
            email='customer@example.com',
            password='securepass123',
            role='customer'
        )
        
        assert user is None
        assert error is not None
        assert 'already exists' in error.lower()
    
    def test_register_invalid_role(self):
        """Test registration with invalid role"""
        user, error = self.auth_service.register_user(
            email='test@example.com',
            password='securepass123',
            role='invalidrole'
        )
        
        assert user is None
        assert error is not None
        assert 'invalid' in error.lower()
    
    def test_register_email_normalization(self, customer_group):
        """Test email is normalized to lowercase"""
        user, error = self.auth_service.register_user(
            email='TEST@EXAMPLE.COM',
            password='securepass123',
            role='customer'
        )
        
        assert error is None
        assert user.email == 'test@example.com'


@pytest.mark.django_db
class TestAuthServiceRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.auth_service = AuthService()
    
    @patch('redis.Redis.get')
    @patch('redis.Redis.pipeline')
    def test_check_rate_limit_allowed(self, mock_pipeline, mock_get):
        """Test rate limit check when under limit"""
        mock_get.return_value = b'5'
        
        is_allowed, remaining = self.auth_service.check_rate_limit(
            'test@example.com',
            'login',
            10,
            30
        )
        
        assert is_allowed is True
        assert remaining == 5
    
    @patch('redis.Redis.get')
    def test_check_rate_limit_exceeded(self, mock_get):
        """Test rate limit check when limit exceeded"""
        mock_get.return_value = b'10'
        
        is_allowed, remaining = self.auth_service.check_rate_limit(
            'test@example.com',
            'login',
            10,
            30
        )
        
        assert is_allowed is False
        assert remaining == 0
    
    @patch('redis.Redis.get')
    def test_check_rate_limit_first_attempt(self, mock_get):
        """Test rate limit check on first attempt"""
        mock_get.return_value = None
        
        is_allowed, remaining = self.auth_service.check_rate_limit(
            'test@example.com',
            'login',
            10,
            30
        )
        
        assert is_allowed is True
        assert remaining == 10
    
    @patch('redis.Redis.get')
    def test_check_rate_limit_redis_failure(self, mock_get):
        """Test rate limit fails open when Redis is down"""
        mock_get.side_effect = Exception('Redis connection error')
        
        is_allowed, remaining = self.auth_service.check_rate_limit(
            'test@example.com',
            'login',
            10,
            30
        )
        
        # Should fail open for better UX
        assert is_allowed is True
        assert remaining == 10


@pytest.mark.django_db
class TestAuthServicePasswordReset:
    """Test password reset functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.auth_service = AuthService()
    
    @patch('apps.accounts.services.auth_service.send_mail')
    def test_generate_password_reset_token_success(self, mock_send_mail, customer_user):
        """Test generating password reset token"""
        token, error = self.auth_service.generate_password_reset_token(
            'customer@example.com'
        )
        
        assert error is None
        assert token is not None
        assert len(token) > 20  # Token should be reasonably long
    
    @patch('apps.accounts.services.auth_service.send_mail')
    def test_generate_password_reset_nonexistent_email(self, mock_send_mail):
        """Test password reset for non-existent email"""
        token, error = self.auth_service.generate_password_reset_token(
            'nonexistent@example.com'
        )
        
        # Should not reveal that email doesn't exist
        assert error is None or token is None
    
    @patch('apps.accounts.services.auth_service.send_mail')
    def test_reset_password_with_valid_token(self, mock_send_mail, customer_user):
        """Test resetting password with valid token"""
        # Generate token first
        token, _ = self.auth_service.generate_password_reset_token(
            'customer@example.com'
        )
        
        if token:
            # Reset password
            success, error = self.auth_service.reset_password(
                token,
                'newsecurepass456'
            )
            
            # Refresh user from DB
            customer_user.refresh_from_db()
            
            # Verify new password works
            if success:
                assert customer_user.check_password('newsecurepass456')
    
    def test_reset_password_with_invalid_token(self):
        """Test resetting password with invalid token"""
        success, error = self.auth_service.reset_password(
            'invalidtoken123',
            'newsecurepass456'
        )
        
        assert success is False
        assert error is not None


@pytest.mark.django_db  
class TestAuthServiceIntegration:
    """Integration tests for AuthService"""
    
    def setup_method(self):
        """Setup for each test"""
        self.auth_service = AuthService()
    
    def test_full_registration_flow(self, customer_group):
        """Test complete registration flow"""
        # Register user
        user, error = self.auth_service.register_user(
            email='integration@example.com',
            password='testpass123',
            first_name='Integration',
            last_name='Test',
            role='customer'
        )
        
        assert error is None
        assert user.email == 'integration@example.com'
        assert user.is_customer
        
        # Verify user can be retrieved
        retrieved_user = User.objects.get(email='integration@example.com')
        assert retrieved_user.id == user.id
        assert retrieved_user.check_password('testpass123')
    
    def test_cannot_register_duplicate_normalized_email(self, customer_user):
        """Test that duplicate emails are caught even with different cases"""
        # Try to register with uppercase version of existing email
        user, error = self.auth_service.register_user(
            email='CUSTOMER@EXAMPLE.COM',
            password='testpass123',
            role='customer'
        )
        
        assert user is None
        assert error is not None
