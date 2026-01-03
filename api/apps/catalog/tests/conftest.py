import pytest
from decimal import Decimal
from model_bakery import baker
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from ninja_jwt.tokens import RefreshToken

from catalog.models import (
    Category, Product, ProductVariant, ProductAttribute,
    ProductAttributeValue, VariantAttributeValue, ProductImage
)

User = get_user_model()


# ============ User Fixtures ============

@pytest.fixture
def customer_group(db):
    """Create Customer group."""
    group, _ = Group.objects.get_or_create(name='Customer')
    return group


@pytest.fixture
def staff_group(db):
    """Create Staff group."""
    group, _ = Group.objects.get_or_create(name='Staff')
    return group


@pytest.fixture
def admin_group(db):
    """Create Admin group."""
    group, _ = Group.objects.get_or_create(name='Admin')
    return group


@pytest.fixture
def customer_user(db, customer_group):
    """Create a customer user for testing."""
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
    """Create a staff user for testing."""
    user = baker.make(
        User,
        email='staff@example.com',
        first_name='Staff',
        last_name='User',
        is_active=True,
        is_staff=True
    )
    user.set_password('testpass123')
    user.save()
    user.groups.add(staff_group)
    return user


@pytest.fixture
def admin_user(db, admin_group):
    """Create an admin user for testing."""
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
def staff_auth_headers(staff_user):
    """Get auth headers for staff user."""
    refresh = RefreshToken.for_user(staff_user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}


@pytest.fixture
def admin_auth_headers(admin_user):
    """Get auth headers for admin user."""
    refresh = RefreshToken.for_user(admin_user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}


@pytest.fixture
def customer_auth_headers(customer_user):
    """Get auth headers for customer user."""
    refresh = RefreshToken.for_user(customer_user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}


# ============ Attribute Fixtures ============

@pytest.fixture
def size_attribute(db):
    """Create Size attribute with values."""
    attr = baker.make(ProductAttribute, name='Size')
    baker.make(ProductAttributeValue, attribute=attr, value='Small')
    baker.make(ProductAttributeValue, attribute=attr, value='Medium')
    baker.make(ProductAttributeValue, attribute=attr, value='Large')
    return attr


@pytest.fixture
def color_attribute(db):
    """Create Color attribute with values."""
    attr = baker.make(ProductAttribute, name='Color')
    baker.make(ProductAttributeValue, attribute=attr, value='Red')
    baker.make(ProductAttributeValue, attribute=attr, value='Blue')
    baker.make(ProductAttributeValue, attribute=attr, value='Green')
    return attr


# ============ Category Fixtures ============

@pytest.fixture
def root_category(db):
    """Create a root category using objects.create for proper MPTT."""
    return Category.objects.create(
        name='Electronics',
        slug='electronics',
        parent=None,
        is_active=True
    )


@pytest.fixture
def child_category(db, root_category):
    """Create a child category using objects.create for proper MPTT."""
    return Category.objects.create(
        name='Phones',
        slug='phones',
        parent=root_category,
        is_active=True
    )


@pytest.fixture
def grandchild_category(db, child_category):
    """Create a grandchild category using objects.create for proper MPTT."""
    return Category.objects.create(
        name='Smartphones',
        slug='smartphones',
        parent=child_category,
        is_active=True
    )


@pytest.fixture
def inactive_category(db):
    """Create an inactive category."""
    return Category.objects.create(
        name='Discontinued',
        slug='discontinued',
        parent=None,
        is_active=False
    )


# ============ Product Fixtures ============

@pytest.fixture
def product(db, child_category):
    """Create a simple product."""
    return baker.make(
        Product,
        name='Test Phone',
        slug='test-phone',
        category=child_category,
        base_price=Decimal('999.99'),
        is_active=True,
        is_featured=False,
    )


@pytest.fixture
def featured_product(db, child_category):
    """Create a featured product."""
    return baker.make(
        Product,
        name='Featured Phone',
        slug='featured-phone',
        category=child_category,
        base_price=Decimal('1299.99'),
        is_active=True,
        is_featured=True,
    )


@pytest.fixture
def inactive_product(db, child_category):
    """Create an inactive product."""
    return baker.make(
        Product,
        name='Old Phone',
        slug='old-phone',
        category=child_category,
        base_price=Decimal('499.99'),
        is_active=False,
        is_featured=False,
    )


# ============ Variant Fixtures ============

@pytest.fixture
def variant(db, product):
    """Create a simple variant."""
    return baker.make(
        ProductVariant,
        product=product,
        sku='TEST-001',
        name='Default',
        price=None,  # Uses base price
        stock_quantity=10,
        low_stock_threshold=5,
        is_active=True,
    )


@pytest.fixture
def product_with_variants(db, product, size_attribute):
    """Create a product with multiple variants."""
    small = ProductAttributeValue.objects.get(attribute=size_attribute, value='Small')
    medium = ProductAttributeValue.objects.get(attribute=size_attribute, value='Medium')
    large = ProductAttributeValue.objects.get(attribute=size_attribute, value='Large')

    v1 = baker.make(
        ProductVariant,
        product=product,
        sku='TEST-SM',
        name='Small',
        price=Decimal('899.99'),
        stock_quantity=10,
        is_active=True,
    )
    VariantAttributeValue.objects.create(variant=v1, attribute_value=small)

    v2 = baker.make(
        ProductVariant,
        product=product,
        sku='TEST-MD',
        name='Medium',
        price=None,  # Uses base price
        stock_quantity=5,
        is_active=True,
    )
    VariantAttributeValue.objects.create(variant=v2, attribute_value=medium)

    v3 = baker.make(
        ProductVariant,
        product=product,
        sku='TEST-LG',
        name='Large',
        price=Decimal('1099.99'),
        stock_quantity=0,  # Out of stock
        is_active=True,
    )
    VariantAttributeValue.objects.create(variant=v3, attribute_value=large)

    return product


@pytest.fixture
def low_stock_variant(db, product):
    """Create a variant with low stock."""
    return baker.make(
        ProductVariant,
        product=product,
        sku='LOW-STOCK-001',
        name='Low Stock Item',
        price=Decimal('799.99'),
        stock_quantity=3,
        low_stock_threshold=5,
        is_active=True,
    )


# ============ Image Fixtures ============

@pytest.fixture
def product_with_images(db, product):
    """Create a product with multiple images."""
    baker.make(
        ProductImage,
        product=product,
        image_url='https://example.com/image1.jpg',
        alt_text='Front view',
        position=0,
        is_primary=True
    )
    baker.make(
        ProductImage,
        product=product,
        image_url='https://example.com/image2.jpg',
        alt_text='Side view',
        position=1,
        is_primary=False
    )
    baker.make(
        ProductImage,
        product=product,
        image_url='https://example.com/image3.jpg',
        alt_text='Back view',
        position=2,
        is_primary=False
    )
    return product


# ============ API Client Fixture ============

@pytest.fixture
def api_client():
    """Create a Django test client."""
    from django.test import Client
    return Client()
