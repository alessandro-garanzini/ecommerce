import pytest
from decimal import Decimal

from catalog.models import Category, Product, ProductVariant
from catalog.services import CategoryService, ProductService, VariantService


@pytest.mark.django_db
class TestCategoryService:
    """Tests for CategoryService."""

    def setup_method(self):
        self.service = CategoryService()

    def test_create_category(self):
        """Test creating a category."""
        category, error = self.service.create_category({
            'name': 'Electronics',
            'description': 'Electronic devices'
        })
        assert error is None
        assert category is not None
        assert category.name == 'Electronics'
        assert category.slug == 'electronics'

    def test_create_category_with_parent(self, root_category):
        """Test creating a child category."""
        category, error = self.service.create_category({
            'name': 'Phones',
            'parent_id': root_category.id
        })
        assert error is None
        assert category.parent == root_category

    def test_create_category_invalid_parent(self):
        """Test creating category with invalid parent."""
        category, error = self.service.create_category({
            'name': 'Test',
            'parent_id': 99999
        })
        assert category is None
        assert 'not found' in error.lower()

    def test_update_category(self, root_category):
        """Test updating a category."""
        category, error = self.service.update_category(
            root_category.id,
            {'name': 'Updated Name', 'description': 'New description'}
        )
        assert error is None
        assert category.name == 'Updated Name'
        assert category.description == 'New description'

    def test_update_category_not_found(self):
        """Test updating non-existent category."""
        category, error = self.service.update_category(99999, {'name': 'Test'})
        assert category is None
        assert 'not found' in error.lower()

    def test_update_category_circular_parent(self, root_category, child_category):
        """Test preventing circular parent reference."""
        category, error = self.service.update_category(
            root_category.id,
            {'parent_id': child_category.id}
        )
        assert category is None
        assert 'circular' in error.lower() or 'descendant' in error.lower()

    def test_delete_category(self, root_category):
        """Test soft deleting a category."""
        success, error = self.service.delete_category(root_category.id)
        assert success is True
        assert error is None
        # Note: MPTT uses its own TreeManager, so we check deleted_at directly
        assert Category.objects.filter(pk=root_category.id, deleted_at__isnull=True).count() == 0
        assert Category.all_objects.filter(pk=root_category.id).count() == 1

    def test_delete_category_with_products(self, child_category, product):
        """Test cannot delete category with products."""
        success, error = self.service.delete_category(child_category.id)
        assert success is False
        assert 'products' in error.lower()

    def test_get_category_by_slug(self, root_category):
        """Test getting category by slug."""
        category = self.service.get_category_by_slug('electronics')
        assert category is not None
        assert category.id == root_category.id

    def test_get_category_by_slug_inactive(self, inactive_category):
        """Test inactive category not returned."""
        category = self.service.get_category_by_slug('discontinued')
        assert category is None

    def test_get_category_tree(self, root_category, child_category, grandchild_category):
        """Test getting category tree."""
        tree = self.service.get_category_tree()
        assert len(tree) == 1
        assert tree[0]['name'] == 'Electronics'
        assert len(tree[0]['children']) == 1
        assert tree[0]['children'][0]['name'] == 'Phones'


@pytest.mark.django_db
class TestProductService:
    """Tests for ProductService."""

    def setup_method(self):
        self.service = ProductService()

    def test_create_product(self, child_category):
        """Test creating a product."""
        product, error = self.service.create_product({
            'name': 'New Phone',
            'category_id': child_category.id,
            'base_price': Decimal('499.99'),
            'description': 'A great phone'
        })
        assert error is None
        assert product is not None
        assert product.name == 'New Phone'
        assert product.base_price == Decimal('499.99')

    def test_create_product_invalid_category(self):
        """Test creating product with invalid category."""
        product, error = self.service.create_product({
            'name': 'Test',
            'category_id': 99999,
            'base_price': Decimal('100.00')
        })
        assert product is None
        assert 'not found' in error.lower()

    def test_update_product(self, product):
        """Test updating a product."""
        updated, error = self.service.update_product(
            product.id,
            {'name': 'Updated Phone', 'is_featured': True}
        )
        assert error is None
        assert updated.name == 'Updated Phone'
        assert updated.is_featured is True

    def test_update_product_not_found(self):
        """Test updating non-existent product."""
        product, error = self.service.update_product(99999, {'name': 'Test'})
        assert product is None
        assert 'not found' in error.lower()

    def test_delete_product(self, product):
        """Test soft deleting a product."""
        success, error = self.service.delete_product(product.id)
        assert success is True
        assert Product.objects.filter(pk=product.id).count() == 0

    def test_get_product_by_slug(self, product):
        """Test getting product by slug."""
        found = self.service.get_product_by_slug('test-phone')
        assert found is not None
        assert found.id == product.id

    def test_get_product_by_slug_inactive(self, inactive_product):
        """Test inactive product not returned."""
        found = self.service.get_product_by_slug('old-phone')
        assert found is None

    def test_list_products_basic(self, product, featured_product):
        """Test basic product listing."""
        products, pagination = self.service.list_products({})
        assert len(products) == 2
        assert pagination['total_items'] == 2

    def test_list_products_filter_category(self, product, root_category, child_category):
        """Test filtering by category."""
        products, _ = self.service.list_products({'category_slug': 'phones'})
        assert len(products) == 1
        assert products[0].id == product.id

    def test_list_products_filter_featured(self, product, featured_product):
        """Test filtering by featured."""
        products, _ = self.service.list_products({'is_featured': True})
        assert len(products) == 1
        assert products[0].is_featured is True

    def test_list_products_filter_price_range(self, product, featured_product):
        """Test filtering by price range."""
        products, _ = self.service.list_products({
            'min_price': Decimal('1000'),
            'max_price': Decimal('1500')
        })
        assert len(products) == 1
        assert products[0].name == 'Featured Phone'

    def test_list_products_search(self, product, featured_product):
        """Test search functionality."""
        products, _ = self.service.list_products({'search': 'Featured'})
        assert len(products) == 1

    def test_list_products_pagination(self, child_category):
        """Test pagination."""
        for i in range(15):
            Product.objects.create(
                name=f'Product {i}',
                category=child_category,
                base_price=Decimal('100.00')
            )

        products, pagination = self.service.list_products({
            'page': 1,
            'page_size': 10
        })
        assert len(products) == 10
        assert pagination['total_items'] == 15
        assert pagination['total_pages'] == 2
        assert pagination['has_next'] is True

    def test_bulk_update_products(self, product, featured_product):
        """Test bulk updating products."""
        result = self.service.bulk_update_products(
            [product.id, featured_product.id],
            {'is_featured': False}
        )
        assert result['success_count'] == 2
        assert result['failed_count'] == 0


@pytest.mark.django_db
class TestVariantService:
    """Tests for VariantService."""

    def setup_method(self):
        self.service = VariantService()

    def test_create_variant(self, product):
        """Test creating a variant."""
        variant, error = self.service.create_variant({
            'product_id': product.id,
            'sku': 'NEW-001',
            'name': 'New Variant',
            'price': Decimal('899.99'),
            'stock_quantity': 10
        })
        assert error is None
        assert variant is not None
        assert variant.sku == 'NEW-001'

    def test_create_variant_duplicate_sku(self, variant):
        """Test duplicate SKU fails."""
        new_variant, error = self.service.create_variant({
            'product_id': variant.product.id,
            'sku': variant.sku,
            'name': 'Another'
        })
        assert new_variant is None
        assert 'sku' in error.lower()

    def test_create_variant_with_attributes(self, product, size_attribute):
        """Test creating variant with attribute values."""
        from catalog.models import ProductAttributeValue
        small = ProductAttributeValue.objects.get(attribute=size_attribute, value='Small')

        variant, error = self.service.create_variant({
            'product_id': product.id,
            'sku': 'ATTR-001',
            'name': 'Small Variant',
            'attribute_value_ids': [small.id]
        })
        assert error is None
        assert variant.attribute_values.count() == 1

    def test_update_variant(self, variant):
        """Test updating a variant."""
        updated, error = self.service.update_variant(
            variant.id,
            {'name': 'Updated Variant', 'price': Decimal('799.99')}
        )
        assert error is None
        assert updated.name == 'Updated Variant'
        assert updated.price == Decimal('799.99')

    def test_update_variant_duplicate_sku(self, product):
        """Test updating with duplicate SKU fails."""
        from model_bakery import baker
        v1 = baker.make(ProductVariant, product=product, sku='SKU-1')
        v2 = baker.make(ProductVariant, product=product, sku='SKU-2')

        updated, error = self.service.update_variant(v2.id, {'sku': 'SKU-1'})
        assert updated is None
        assert 'sku' in error.lower()

    def test_delete_variant(self, variant):
        """Test soft deleting a variant."""
        success, error = self.service.delete_variant(variant.id)
        assert success is True
        assert ProductVariant.objects.filter(pk=variant.id).count() == 0

    def test_update_stock_set(self, variant):
        """Test setting stock."""
        updated, error = self.service.update_stock(variant.id, 50, 'set')
        assert error is None
        assert updated.stock_quantity == 50

    def test_update_stock_add(self, variant):
        """Test adding stock."""
        initial = variant.stock_quantity
        updated, error = self.service.update_stock(variant.id, 10, 'add')
        assert error is None
        assert updated.stock_quantity == initial + 10

    def test_update_stock_reduce(self, variant):
        """Test reducing stock."""
        initial = variant.stock_quantity
        updated, error = self.service.update_stock(variant.id, 3, 'reduce')
        assert error is None
        assert updated.stock_quantity == initial - 3

    def test_update_stock_reduce_insufficient(self, variant):
        """Test reducing stock fails with insufficient stock."""
        updated, error = self.service.update_stock(variant.id, 100, 'reduce')
        assert updated is None
        assert 'insufficient' in error.lower()

    def test_update_stock_negative(self, variant):
        """Test setting negative stock fails."""
        updated, error = self.service.update_stock(variant.id, -10, 'set')
        assert updated is None
        assert 'negative' in error.lower()

    def test_bulk_update_stock(self, product):
        """Test bulk stock updates."""
        from model_bakery import baker
        v1 = baker.make(ProductVariant, product=product, sku='BULK-1', stock_quantity=10)
        v2 = baker.make(ProductVariant, product=product, sku='BULK-2', stock_quantity=10)

        result = self.service.bulk_update_stock([
            {'variant_id': v1.id, 'quantity': 20, 'operation': 'set'},
            {'variant_id': v2.id, 'quantity': 5, 'operation': 'add'}
        ])
        assert result['success_count'] == 2

    def test_get_low_stock_variants(self, low_stock_variant, variant):
        """Test getting low stock variants."""
        variants = self.service.get_low_stock_variants()
        skus = [v.sku for v in variants]
        assert 'LOW-STOCK-001' in skus
        # Regular variant (stock=10, threshold=5) should not be in low stock
        assert 'TEST-001' not in skus
