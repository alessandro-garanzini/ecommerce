import pytest
from django.contrib.auth import get_user_model
from pydantic import ValidationError
from model_bakery import baker

from apps.accounts.schemas.auth import (
    RegisterSchema,
    LoginSchema,
    TokenResponseSchema,
    RefreshTokenSchema
)
from apps.accounts.schemas.user import UserSchema
from apps.accounts.schemas.password_reset import (
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema
)
from apps.accounts.schemas.common import MessageSchema

User = get_user_model()


@pytest.mark.django_db
class TestRegisterSchema:
    """Test RegisterSchema validation"""
    
    def test_valid_registration_data(self):
        """Test schema with valid data"""
        data = {
            'email': 'test@example.com',
            'password': 'securepass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'customer'
        }
        schema = RegisterSchema(**data)
        
        assert schema.email == 'test@example.com'
        assert schema.password == 'securepass123'
        assert schema.role == 'customer'
    
    def test_default_role(self):
        """Test default role is customer"""
        data = {
            'email': 'test@example.com',
            'password': 'securepass123'
        }
        schema = RegisterSchema(**data)
        
        assert schema.role == 'customer'
        assert schema.first_name == ''
        assert schema.last_name == ''
    
    def test_missing_required_fields(self):
        """Test schema fails without required fields"""
        with pytest.raises(ValidationError):
            RegisterSchema(email='test@example.com')  # Missing password
    
    def test_all_roles(self):
        """Test all valid roles"""
        for role in ['customer', 'staff', 'admin']:
            data = {
                'email': f'{role}@example.com',
                'password': 'pass123',
                'role': role
            }
            schema = RegisterSchema(**data)
            assert schema.role == role


@pytest.mark.django_db
class TestLoginSchema:
    """Test LoginSchema validation"""
    
    def test_valid_login_data(self):
        """Test schema with valid login data"""
        data = {
            'email': 'user@example.com',
            'password': 'password123'
        }
        schema = LoginSchema(**data)
        
        assert schema.email == 'user@example.com'
        assert schema.password == 'password123'
    
    def test_missing_fields(self):
        """Test schema fails without required fields"""
        with pytest.raises(ValidationError):
            LoginSchema(email='test@example.com')  # Missing password


@pytest.mark.django_db
class TestTokenResponseSchema:
    """Test TokenResponseSchema"""
    
    def test_valid_token_response(self):
        """Test schema with valid token data"""
        data = {
            'access': 'access_token_here',
            'refresh': 'refresh_token_here',
            'expires_in': 900
        }
        schema = TokenResponseSchema(**data)
        
        assert schema.access == 'access_token_here'
        assert schema.refresh == 'refresh_token_here'
        assert schema.token_type == 'Bearer'
        assert schema.expires_in == 900
    
    def test_default_token_type(self):
        """Test default token_type is Bearer"""
        data = {
            'access': 'token1',
            'refresh': 'token2',
            'expires_in': 900
        }
        schema = TokenResponseSchema(**data)
        
        assert schema.token_type == 'Bearer'


@pytest.mark.django_db
class TestRefreshTokenSchema:
    """Test RefreshTokenSchema"""
    
    def test_valid_refresh_token(self):
        """Test schema with refresh token"""
        schema = RefreshTokenSchema(refresh='refresh_token_value')
        
        assert schema.refresh == 'refresh_token_value'
    
    def test_missing_token(self):
        """Test schema fails without token"""
        with pytest.raises(ValidationError):
            RefreshTokenSchema()


@pytest.mark.django_db
class TestMessageSchema:
    """Test MessageSchema"""
    
    def test_valid_message(self):
        """Test schema with message"""
        schema = MessageSchema(message='Success!')
        
        assert schema.message == 'Success!'


@pytest.mark.django_db
class TestPasswordResetSchemas:
    """Test password reset schemas"""
    
    def test_password_reset_request_schema(self):
        """Test password reset request schema"""
        schema = PasswordResetRequestSchema(email='user@example.com')
        
        assert schema.email == 'user@example.com'
    
    def test_password_reset_confirm_schema(self):
        """Test password reset confirm schema"""
        schema = PasswordResetConfirmSchema(
            token='reset_token_123',
            new_password='newsecurepass'
        )
        
        assert schema.token == 'reset_token_123'
        assert schema.new_password == 'newsecurepass'


@pytest.mark.django_db
class TestUserSchema:
    """Test UserSchema (ModelSchema)"""
    
    def test_user_schema_from_model(self, customer_user):
        """Test UserSchema resolves from User model"""
        schema = UserSchema.from_orm(customer_user)
        
        assert schema.id == customer_user.id
        assert schema.email == customer_user.email
        assert schema.first_name == customer_user.first_name
        assert schema.last_name == customer_user.last_name
        assert schema.is_staff == customer_user.is_staff
        assert schema.is_active == customer_user.is_active
    
    def test_user_schema_groups(self, customer_user):
        """Test groups resolver"""
        schema = UserSchema.from_orm(customer_user)
        
        assert 'Customer' in schema.groups
        assert isinstance(schema.groups, list)
    
    def test_user_schema_role(self, customer_user):
        """Test role resolver"""
        schema = UserSchema.from_orm(customer_user)
        
        assert schema.role == 'Customer'
    
    def test_user_schema_is_customer(self, customer_user):
        """Test is_customer resolver"""
        schema = UserSchema.from_orm(customer_user)
        
        assert schema.is_customer is True
    
    def test_user_schema_staff(self, staff_user):
        """Test schema with staff user"""
        schema = UserSchema.from_orm(staff_user)
        
        assert schema.is_staff is True
        assert 'Staff' in schema.groups
        assert schema.role == 'Staff'
    
    def test_user_schema_admin(self, admin_user):
        """Test schema with admin user"""
        schema = UserSchema.from_orm(admin_user)
        
        assert schema.is_staff is True
        assert 'Admin' in schema.groups
        assert schema.role == 'Superuser'  # Superuser takes precedence
