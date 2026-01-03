import pytest
import json
from decimal import Decimal
from django.test import Client

from catalog.models import (
    Category, Product, ProductVariant, ProductAttribute,
    ProductAttributeValue, ProductImage
)


@pytest.mark.django_db
class TestPublicCategoryEndpoints:
    """Tests for public category endpoints."""

    def test_list_categories_empty(self, api_client):
        """Test listing categories when none exist."""
        response = api_client.get('/api/catalog/categories')
        assert response.status_code == 200
        assert response.json() == []

    def test_list_categories(self, api_client, root_category, child_category):
        """Test listing categories returns tree structure."""
        response = api_client.get('/api/catalog/categories')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only root category at top level
        assert data[0]['name'] == 'Electronics'
        assert len(data[0]['children']) == 1
        assert data[0]['children'][0]['name'] == 'Phones'

    def test_list_categories_excludes_inactive(self, api_client, root_category, inactive_category):
        """Test that inactive categories are excluded."""
        response = api_client.get('/api/catalog/categories')
        assert response.status_code == 200
        data = response.json()
        names = [cat['name'] for cat in data]
        assert 'Electronics' in names
        assert 'Discontinued' not in names

    def test_get_category_by_slug(self, api_client, root_category, child_category):
        """Test getting category detail by slug."""
        response = api_client.get('/api/catalog/categories/phones')
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Phones'
        assert data['slug'] == 'phones'
        assert len(data['ancestors']) == 1
        assert data['ancestors'][0]['name'] == 'Electronics'

    def test_get_category_not_found(self, api_client):
        """Test 404 for non-existent category."""
        response = api_client.get('/api/catalog/categories/nonexistent')
        assert response.status_code == 404

    def test_get_category_full_path(self, api_client, grandchild_category):
        """Test full path in category detail."""
        response = api_client.get('/api/catalog/categories/smartphones')
        assert response.status_code == 200
        data = response.json()
        assert data['full_path'] == 'Electronics > Phones > Smartphones'


@pytest.mark.django_db
class TestPublicProductEndpoints:
    """Tests for public product endpoints."""

    def test_list_products_empty(self, api_client):
        """Test listing products when none exist."""
        response = api_client.get('/api/catalog/products')
        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total_items'] == 0

    def test_list_products(self, api_client, product, featured_product):
        """Test listing products."""
        response = api_client.get('/api/catalog/products')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 2
        assert len(data['items']) == 2

    def test_list_products_excludes_inactive(self, api_client, product, inactive_product):
        """Test that inactive products are excluded."""
        response = api_client.get('/api/catalog/products')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 1
        assert data['items'][0]['name'] == 'Test Phone'

    def test_list_products_filter_by_category(self, api_client, product, root_category, child_category):
        """Test filtering products by category slug."""
        response = api_client.get('/api/catalog/products?category_slug=phones')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 1

    def test_list_products_filter_by_parent_category(self, api_client, product, root_category, child_category):
        """Test filtering by parent category includes children."""
        response = api_client.get('/api/catalog/products?category_slug=electronics')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 1

    def test_list_products_filter_by_featured(self, api_client, product, featured_product):
        """Test filtering by featured flag."""
        response = api_client.get('/api/catalog/products?is_featured=true')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 1
        assert data['items'][0]['is_featured'] is True

    def test_list_products_filter_by_price_range(self, api_client, product, featured_product):
        """Test filtering by price range."""
        response = api_client.get('/api/catalog/products?min_price=1000&max_price=1500')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 1
        assert data['items'][0]['name'] == 'Featured Phone'

    def test_list_products_search(self, api_client, product, featured_product):
        """Test search functionality."""
        response = api_client.get('/api/catalog/products?search=Featured')
        assert response.status_code == 200
        data = response.json()
        assert data['total_items'] == 1
        assert data['items'][0]['name'] == 'Featured Phone'

    def test_list_products_pagination(self, api_client, child_category):
        """Test pagination."""
        # Create 25 products
        for i in range(25):
            Product.objects.create(
                name=f'Product {i}',
                category=child_category,
                base_price=Decimal('100.00')
            )

        response = api_client.get('/api/catalog/products?page=1&page_size=10')
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 10
        assert data['total_items'] == 25
        assert data['total_pages'] == 3
        assert data['has_next'] is True
        assert data['has_prev'] is False

    def test_list_products_sorting(self, api_client, product, featured_product):
        """Test sorting."""
        response = api_client.get('/api/catalog/products?sort_by=name&sort_order=asc')
        assert response.status_code == 200
        data = response.json()
        names = [p['name'] for p in data['items']]
        assert names == sorted(names)

    def test_get_product_by_slug(self, api_client, product_with_variants, product_with_images):
        """Test getting product detail by slug."""
        response = api_client.get('/api/catalog/products/test-phone')
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Test Phone'
        assert data['slug'] == 'test-phone'
        assert 'variants' in data
        assert 'images' in data
        assert 'category' in data

    def test_get_product_not_found(self, api_client):
        """Test 404 for non-existent product."""
        response = api_client.get('/api/catalog/products/nonexistent')
        assert response.status_code == 404


@pytest.mark.django_db
class TestPublicAttributeEndpoints:
    """Tests for public attribute endpoints."""

    def test_list_attributes(self, api_client, size_attribute, color_attribute):
        """Test listing attributes with values."""
        response = api_client.get('/api/catalog/attributes')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        attr_names = [a['name'] for a in data]
        assert 'Size' in attr_names
        assert 'Color' in attr_names


@pytest.mark.django_db
class TestAdminCategoryEndpoints:
    """Tests for admin category endpoints."""

    def test_create_category_without_auth(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.post(
            '/api/catalog/admin/categories',
            data=json.dumps({'name': 'New Category'}),
            content_type='application/json'
        )
        assert response.status_code == 401

    def test_create_category_as_customer(self, api_client, customer_auth_headers):
        """Test that customers cannot create categories."""
        response = api_client.post(
            '/api/catalog/admin/categories',
            data=json.dumps({'name': 'New Category'}),
            content_type='application/json',
            **customer_auth_headers
        )
        assert response.status_code == 401

    def test_create_category_as_staff(self, api_client, staff_auth_headers):
        """Test creating a category as staff."""
        response = api_client.post(
            '/api/catalog/admin/categories',
            data=json.dumps({'name': 'New Category', 'description': 'Test'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'New Category'
        assert data['slug'] == 'new-category'

    def test_create_child_category(self, api_client, staff_auth_headers, root_category):
        """Test creating a child category."""
        response = api_client.post(
            '/api/catalog/admin/categories',
            data=json.dumps({'name': 'Child', 'parent_id': root_category.id}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['parent_id'] == root_category.id

    def test_update_category(self, api_client, staff_auth_headers, root_category):
        """Test updating a category."""
        response = api_client.put(
            f'/api/catalog/admin/categories/{root_category.id}',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Updated Name'

    def test_delete_category_as_staff(self, api_client, staff_auth_headers, root_category):
        """Test that staff cannot delete categories (admin only)."""
        response = api_client.delete(
            f'/api/catalog/admin/categories/{root_category.id}',
            **staff_auth_headers
        )
        assert response.status_code == 401

    def test_delete_category_as_admin(self, api_client, admin_auth_headers, root_category):
        """Test deleting a category as admin."""
        response = api_client.delete(
            f'/api/catalog/admin/categories/{root_category.id}',
            **admin_auth_headers
        )
        assert response.status_code == 200

    def test_delete_category_with_products(self, api_client, admin_auth_headers, child_category, product):
        """Test cannot delete category with products."""
        response = api_client.delete(
            f'/api/catalog/admin/categories/{child_category.id}',
            **admin_auth_headers
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestAdminProductEndpoints:
    """Tests for admin product endpoints."""

    def test_create_product(self, api_client, staff_auth_headers, child_category):
        """Test creating a product."""
        response = api_client.post(
            '/api/catalog/admin/products',
            data=json.dumps({
                'name': 'New Product',
                'category_id': child_category.id,
                'base_price': '199.99'
            }),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'New Product'

    def test_update_product(self, api_client, staff_auth_headers, product):
        """Test updating a product."""
        response = api_client.put(
            f'/api/catalog/admin/products/{product.id}',
            data=json.dumps({'name': 'Updated Product', 'is_featured': True}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Updated Product'
        assert data['is_featured'] is True

    def test_delete_product(self, api_client, admin_auth_headers, product):
        """Test deleting a product."""
        response = api_client.delete(
            f'/api/catalog/admin/products/{product.id}',
            **admin_auth_headers
        )
        assert response.status_code == 200
        # Verify soft delete
        assert Product.objects.filter(pk=product.id).count() == 0
        assert Product.all_objects.filter(pk=product.id).count() == 1

    def test_bulk_update_products(self, api_client, staff_auth_headers, product, featured_product):
        """Test bulk updating products."""
        response = api_client.post(
            '/api/catalog/admin/products/bulk-update',
            data=json.dumps({
                'product_ids': [product.id, featured_product.id],
                'is_featured': False
            }),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success_count'] == 2


@pytest.mark.django_db
class TestAdminVariantEndpoints:
    """Tests for admin variant endpoints."""

    def test_create_variant(self, api_client, staff_auth_headers, product):
        """Test creating a variant."""
        response = api_client.post(
            '/api/catalog/admin/variants',
            data=json.dumps({
                'product_id': product.id,
                'sku': 'NEW-SKU-001',
                'name': 'New Variant',
                'price': '899.99',
                'stock_quantity': 10
            }),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['sku'] == 'NEW-SKU-001'
        assert data['name'] == 'New Variant'

    def test_create_variant_duplicate_sku(self, api_client, staff_auth_headers, variant):
        """Test creating variant with duplicate SKU fails."""
        response = api_client.post(
            '/api/catalog/admin/variants',
            data=json.dumps({
                'product_id': variant.product.id,
                'sku': variant.sku,  # Duplicate
                'name': 'Another Variant'
            }),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 400

    def test_update_stock(self, api_client, staff_auth_headers, variant):
        """Test updating variant stock."""
        response = api_client.put(
            f'/api/catalog/admin/variants/{variant.id}/stock',
            data=json.dumps({'quantity': 20, 'operation': 'set'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['stock_quantity'] == 20

    def test_add_stock(self, api_client, staff_auth_headers, variant):
        """Test adding stock."""
        initial_stock = variant.stock_quantity
        response = api_client.put(
            f'/api/catalog/admin/variants/{variant.id}/stock',
            data=json.dumps({'quantity': 5, 'operation': 'add'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['stock_quantity'] == initial_stock + 5

    def test_reduce_stock(self, api_client, staff_auth_headers, variant):
        """Test reducing stock."""
        initial_stock = variant.stock_quantity
        response = api_client.put(
            f'/api/catalog/admin/variants/{variant.id}/stock',
            data=json.dumps({'quantity': 3, 'operation': 'reduce'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['stock_quantity'] == initial_stock - 3

    def test_reduce_stock_insufficient(self, api_client, staff_auth_headers, variant):
        """Test reducing stock fails with insufficient stock."""
        response = api_client.put(
            f'/api/catalog/admin/variants/{variant.id}/stock',
            data=json.dumps({'quantity': 100, 'operation': 'reduce'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 400

    def test_get_low_stock_variants(self, api_client, staff_auth_headers, low_stock_variant):
        """Test getting low stock variants."""
        response = api_client.get(
            '/api/catalog/admin/stock/low',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        skus = [v['sku'] for v in data]
        assert 'LOW-STOCK-001' in skus


@pytest.mark.django_db
class TestAdminImageEndpoints:
    """Tests for admin image endpoints."""

    def test_create_image(self, api_client, staff_auth_headers, product):
        """Test creating an image."""
        response = api_client.post(
            '/api/catalog/admin/images',
            data=json.dumps({
                'product_id': product.id,
                'image_url': 'https://example.com/new.jpg',
                'alt_text': 'New image'
            }),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['image_url'] == 'https://example.com/new.jpg'
        assert data['is_primary'] is True  # First image is auto-primary

    def test_update_image(self, api_client, staff_auth_headers, product_with_images):
        """Test updating an image."""
        image = product_with_images.images.first()
        response = api_client.put(
            f'/api/catalog/admin/images/{image.id}',
            data=json.dumps({'alt_text': 'Updated alt text'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['alt_text'] == 'Updated alt text'

    def test_delete_image(self, api_client, staff_auth_headers, product_with_images):
        """Test deleting an image."""
        image = product_with_images.images.first()
        response = api_client.delete(
            f'/api/catalog/admin/images/{image.id}',
            **staff_auth_headers
        )
        assert response.status_code == 200

    def test_reorder_images(self, api_client, staff_auth_headers, product_with_images):
        """Test reordering images."""
        images = list(product_with_images.images.all())
        # Reverse order
        new_order = [img.id for img in reversed(images)]
        response = api_client.post(
            '/api/catalog/admin/images/reorder',
            data=json.dumps({'image_ids': new_order}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminAttributeEndpoints:
    """Tests for admin attribute endpoints."""

    def test_create_attribute(self, api_client, admin_auth_headers):
        """Test creating an attribute."""
        response = api_client.post(
            '/api/catalog/admin/attributes',
            data=json.dumps({'name': 'Material'}),
            content_type='application/json',
            **admin_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Material'

    def test_create_attribute_duplicate(self, api_client, admin_auth_headers, size_attribute):
        """Test creating duplicate attribute fails."""
        response = api_client.post(
            '/api/catalog/admin/attributes',
            data=json.dumps({'name': 'Size'}),  # Already exists
            content_type='application/json',
            **admin_auth_headers
        )
        assert response.status_code == 400

    def test_create_attribute_value(self, api_client, admin_auth_headers, size_attribute):
        """Test creating an attribute value."""
        response = api_client.post(
            '/api/catalog/admin/attributes/values',
            data=json.dumps({
                'attribute_id': size_attribute.id,
                'value': 'Extra Large'
            }),
            content_type='application/json',
            **admin_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data['value'] == 'Extra Large'

    def test_create_attribute_as_staff_fails(self, api_client, staff_auth_headers):
        """Test that staff cannot create attributes (admin only)."""
        response = api_client.post(
            '/api/catalog/admin/attributes',
            data=json.dumps({'name': 'Material'}),
            content_type='application/json',
            **staff_auth_headers
        )
        assert response.status_code == 401
