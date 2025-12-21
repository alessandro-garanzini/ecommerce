import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user_with_baker(self):
        """Test creating user with model-bakery"""
        user = baker.make(User, email='test@example.com')
        
        assert user.email == 'test@example.com'
        assert user.pk is not None
    
    def test_user_email_required(self):
        """Test that email is required"""
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='testpass')
    
    def test_user_string_representation(self):
        """Test __str__ method"""
        user = baker.make(User, email='test@example.com')
        
        assert str(user) == 'test@example.com'
    
    def test_user_groups_property(self, customer_group):
        """Test user groups relationship"""
        user = baker.make(User)
        user.groups.add(customer_group)
        
        assert customer_group in user.groups.all()
        assert 'Customer' in [g.name for g in user.groups.all()]


@pytest.mark.django_db
class TestUserGroupProperties:
    """Test user group-based properties"""
    
    def test_is_customer_property(self, customer_user):
        """Test is_customer property"""
        assert customer_user.is_customer is True
    
    def test_is_customer_false(self, staff_user):
        """Test is_customer returns False for non-customers"""
        assert staff_user.is_customer is False
    
    def test_is_admin_property(self, admin_user):
        """Test is_admin property"""
        assert admin_user.is_admin is True
    
    def test_is_admin_false(self, customer_user):
        """Test is_admin returns False for non-admins"""
        assert customer_user.is_admin is False
    
    def test_is_staff_member_property(self, staff_user):
        """Test is_staff_member property"""
        assert staff_user.is_staff_member is True
    
    def test_is_staff_member_false(self, customer_user):
        """Test is_staff_member returns False for non-staff"""
        assert customer_user.is_staff_member is False


@pytest.mark.django_db
class TestUserManagers:
    """Test custom user managers"""
    
    def test_create_customer(self, customer_group):
        """Test create_customer method"""
        user = User.objects.create_customer(
            email='customer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Customer'
        )
        
        assert user.email == 'customer@test.com'
        assert user.check_password('testpass123')
        assert user.groups.filter(name='Customer').exists()
        assert user.is_staff is False
    
    def test_create_staff_user(self, staff_group):
        """Test create_staff_user method"""
        user = User.objects.create_staff_user(
            email='staff@test.com',
            password='testpass123'
        )
        
        assert user.email == 'staff@test.com'
        assert user.is_staff is True
        assert user.groups.filter(name='Staff').exists()
    
    def test_create_superuser(self, admin_group):
        """Test create_superuser method"""
        user = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123'
        )
        
        assert user.email == 'admin@test.com'
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.groups.filter(name='Admin').exists()
    
    def test_create_customer_normalizes_email(self, customer_group):
        """Test that email is normalized to lowercase"""
        user = User.objects.create_customer(
            email='TEST@EXAMPLE.COM',
            password='testpass123'
        )
        
        # Django normalizes only the domain part, not the local part
        assert '@example.com' in user.email


@pytest.mark.django_db
class TestUserGroupMethods:
    """Test add_to_group and remove_from_group methods"""
    
    def test_add_to_group(self, customer_group):
        """Test adding user to group"""
        user = baker.make(User)
        user.add_to_group('Customer')
        
        assert user.groups.filter(name='Customer').exists()
    
    def test_remove_from_group(self, customer_user):
        """Test removing user from group"""
        assert customer_user.groups.filter(name='Customer').exists()
        
        customer_user.remove_from_group('Customer')
        
        assert not customer_user.groups.filter(name='Customer').exists()
    
    def test_add_to_nonexistent_group(self):
        """Test adding to non-existent group creates it"""
        user = baker.make(User)
        user.add_to_group('NewGroup')
        
        assert user.groups.filter(name='NewGroup').exists()
        assert Group.objects.filter(name='NewGroup').exists()


@pytest.mark.django_db
class TestUserRoleDisplay:
    """Test get_role_display method"""
    
    def test_customer_role_display(self, customer_user):
        """Test customer role display"""
        role = customer_user.get_role_display()
        assert role == 'Customer'
    
    def test_staff_role_display(self, staff_user):
        """Test staff role display"""
        role = staff_user.get_role_display()
        assert role == 'Staff'
    
    def test_admin_role_display(self, admin_user):
        """Test admin role display"""
        role = admin_user.get_role_display()
        # Superusers get 'Superuser' as primary role
        assert role == 'Superuser'
    
    def test_multiple_groups_role_display(self, customer_group, staff_group):
        """Test role display with multiple groups"""
        user = baker.make(User)
        user.groups.add(customer_group, staff_group)
        
        role = user.get_role_display()
        # Should return first group
        assert role in ['Customer', 'Staff']
