import pytest
from decimal import Decimal
from model_bakery import baker
from django.utils import timezone

from catalog.models import (
    Category, Product, ProductVariant, ProductAttribute,
    ProductAttributeValue, VariantAttributeValue, ProductImage
)


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model."""

    def test_category_creation(self, root_category):
        """Test basic category creation."""
        assert root_category.name == 'Electronics'
        assert root_category.slug == 'electronics'
        assert root_category.is_active is True
        assert root_category.parent is None

    def test_category_slug_auto_generation(self, db):
        """Test that slug is auto-generated from name."""
        category = Category.objects.create(name='New Category')
        assert category.slug == 'new-category'

    def test_category_slug_uniqueness(self, db):
        """Test that duplicate slugs get a suffix."""
        cat1 = Category.objects.create(name='Test Category')
        cat2 = Category.objects.create(name='Test Category')
        assert cat1.slug == 'test-category'
        assert cat2.slug == 'test-category-1'

    def test_category_hierarchy(self, root_category, child_category, grandchild_category):
        """Test MPTT hierarchy."""
        assert child_category.parent == root_category
        assert grandchild_category.parent == child_category
        assert root_category.level == 0
        assert child_category.level == 1
        assert grandchild_category.level == 2

    def test_category_ancestors(self, grandchild_category):
        """Test getting ancestors."""
        ancestors = list(grandchild_category.get_ancestors())
        assert len(ancestors) == 2
        assert ancestors[0].name == 'Electronics'
        assert ancestors[1].name == 'Phones'

    def test_category_descendants(self, root_category, child_category, grandchild_category):
        """Test getting descendants."""
        descendants = list(root_category.get_descendants())
        assert len(descendants) == 2
        assert child_category in descendants
        assert grandchild_category in descendants

    def test_category_full_path(self, grandchild_category):
        """Test full path property."""
        assert grandchild_category.full_path == 'Electronics > Phones > Smartphones'

    def test_category_soft_delete(self, root_category):
        """Test soft delete functionality."""
        root_category.soft_delete()
        assert root_category.is_deleted is True
        assert root_category.deleted_at is not None
        # Note: MPTT uses its own TreeManager, so we check deleted_at directly
        # The BaseModel soft delete still works, we just need to filter manually
        assert Category.objects.filter(pk=root_category.pk, deleted_at__isnull=True).count() == 0
        # Should appear in all_objects
        assert Category.all_objects.filter(pk=root_category.pk).count() == 1

    def test_category_restore(self, root_category):
        """Test restore after soft delete."""
        root_category.soft_delete()
        root_category.restore()
        assert root_category.is_deleted is False
        assert root_category.deleted_at is None

    def test_category_product_count(self, child_category, product):
        """Test product count property."""
        # Refresh to get latest data
        child_category.refresh_from_db()
        assert child_category.product_count == 1


@pytest.mark.django_db
class TestProductModel:
    """Tests for the Product model."""

    def test_product_creation(self, product):
        """Test basic product creation."""
        assert product.name == 'Test Phone'
        assert product.slug == 'test-phone'
        assert product.base_price == Decimal('999.99')
        assert product.is_active is True

    def test_product_slug_auto_generation(self, child_category):
        """Test that slug is auto-generated from name."""
        product = Product.objects.create(
            name='New Product',
            category=child_category,
            base_price=Decimal('100.00')
        )
        assert product.slug == 'new-product'

    def test_product_total_stock(self, product_with_variants):
        """Test total stock across all variants."""
        # Small: 10, Medium: 5, Large: 0
        assert product_with_variants.total_stock == 15

    def test_product_is_in_stock(self, product_with_variants):
        """Test is_in_stock property."""
        assert product_with_variants.is_in_stock is True

    def test_product_not_in_stock(self, product):
        """Test product with no variants is not in stock."""
        assert product.is_in_stock is False

    def test_product_min_price(self, product_with_variants):
        """Test min_price property."""
        # Small: 899.99, Medium: 999.99 (base), Large: 1099.99
        assert product_with_variants.min_price == Decimal('899.99')

    def test_product_max_price(self, product_with_variants):
        """Test max_price property."""
        assert product_with_variants.max_price == Decimal('1099.99')

    def test_product_price_with_no_variants(self, product):
        """Test price when no variants exist."""
        assert product.min_price == Decimal('999.99')
        assert product.max_price == Decimal('999.99')

    def test_product_primary_image(self, product_with_images):
        """Test primary image property."""
        primary = product_with_images.primary_image
        assert primary is not None
        assert primary.is_primary is True
        assert primary.image_url == 'https://example.com/image1.jpg'

    def test_product_soft_delete(self, product):
        """Test soft delete functionality."""
        product.soft_delete()
        assert product.is_deleted is True
        assert Product.objects.filter(pk=product.pk).count() == 0
        assert Product.all_objects.filter(pk=product.pk).count() == 1


@pytest.mark.django_db
class TestProductVariantModel:
    """Tests for the ProductVariant model."""

    def test_variant_creation(self, variant):
        """Test basic variant creation."""
        assert variant.sku == 'TEST-001'
        assert variant.name == 'Default'
        assert variant.stock_quantity == 10
        assert variant.is_active is True

    def test_variant_effective_price_with_price(self, product):
        """Test effective price when variant has custom price."""
        variant = baker.make(
            ProductVariant,
            product=product,
            sku='PRICE-TEST',
            name='Custom Price',
            price=Decimal('799.99'),
            stock_quantity=5,
        )
        assert variant.effective_price == Decimal('799.99')

    def test_variant_effective_price_without_price(self, variant):
        """Test effective price falls back to base price."""
        assert variant.price is None
        assert variant.effective_price == Decimal('999.99')

    def test_variant_is_in_stock(self, variant):
        """Test is_in_stock property."""
        assert variant.is_in_stock is True

    def test_variant_not_in_stock(self, product):
        """Test variant with zero stock."""
        variant = baker.make(
            ProductVariant,
            product=product,
            sku='EMPTY',
            name='Empty',
            stock_quantity=0,
        )
        assert variant.is_in_stock is False

    def test_variant_is_low_stock(self, low_stock_variant):
        """Test is_low_stock property."""
        assert low_stock_variant.is_low_stock is True

    def test_variant_reduce_stock_success(self, variant):
        """Test successful stock reduction."""
        initial_stock = variant.stock_quantity
        result = variant.reduce_stock(3)
        assert result is True
        assert variant.stock_quantity == initial_stock - 3

    def test_variant_reduce_stock_insufficient(self, variant):
        """Test stock reduction with insufficient stock."""
        result = variant.reduce_stock(100)
        assert result is False
        assert variant.stock_quantity == 10  # Unchanged

    def test_variant_add_stock(self, variant):
        """Test adding stock."""
        initial_stock = variant.stock_quantity
        variant.add_stock(5)
        assert variant.stock_quantity == initial_stock + 5


@pytest.mark.django_db
class TestProductAttributeModel:
    """Tests for the ProductAttribute model."""

    def test_attribute_creation(self, size_attribute):
        """Test basic attribute creation."""
        assert size_attribute.name == 'Size'

    def test_attribute_values(self, size_attribute):
        """Test attribute has correct values."""
        values = list(size_attribute.values.values_list('value', flat=True))
        assert 'Small' in values
        assert 'Medium' in values
        assert 'Large' in values


@pytest.mark.django_db
class TestProductAttributeValueModel:
    """Tests for the ProductAttributeValue model."""

    def test_attribute_value_str(self, size_attribute):
        """Test string representation."""
        value = ProductAttributeValue.objects.get(attribute=size_attribute, value='Small')
        assert str(value) == 'Size: Small'

    def test_attribute_value_unique_together(self, size_attribute):
        """Test unique constraint on attribute + value."""
        with pytest.raises(Exception):
            ProductAttributeValue.objects.create(
                attribute=size_attribute,
                value='Small'  # Already exists
            )


@pytest.mark.django_db
class TestVariantAttributeValueModel:
    """Tests for the VariantAttributeValue model."""

    def test_variant_attribute_assignment(self, product_with_variants, size_attribute):
        """Test variant has correct attributes."""
        small_variant = ProductVariant.objects.get(sku='TEST-SM')
        attrs = list(small_variant.attribute_values.all())
        assert len(attrs) == 1
        assert attrs[0].attribute_value.value == 'Small'


@pytest.mark.django_db
class TestProductImageModel:
    """Tests for the ProductImage model."""

    def test_image_creation(self, product):
        """Test basic image creation."""
        image = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/test.jpg',
            alt_text='Test image',
            position=0
        )
        assert image.image_url == 'https://example.com/test.jpg'
        assert image.is_primary is True  # First image auto-set as primary

    def test_image_auto_primary(self, product):
        """Test first image is auto-set as primary."""
        img1 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/1.jpg',
        )
        img2 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/2.jpg',
        )
        assert img1.is_primary is True
        assert img2.is_primary is False

    def test_image_single_primary(self, product):
        """Test only one primary image per product."""
        img1 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/1.jpg',
            is_primary=True
        )
        img2 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/2.jpg',
            is_primary=True
        )
        img1.refresh_from_db()
        assert img1.is_primary is False
        assert img2.is_primary is True

    def test_image_ordering(self, product_with_images):
        """Test images are ordered by position."""
        images = list(product_with_images.images.all())
        positions = [img.position for img in images]
        assert positions == sorted(positions)
