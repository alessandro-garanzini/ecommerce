from typing import Optional, Tuple, List
from django.db import transaction, models
from django.db.models import Q
from django.core.paginator import Paginator
from catalog.models import Category, Product


class ProductService:
    """Service layer for product operations."""

    def list_products(self, filters: dict) -> Tuple[List[Product], dict]:
        """
        List products with filtering and pagination.
        Returns (products, pagination_info).
        """
        queryset = Product.objects.select_related('category').prefetch_related(
            'images', 'variants'
        ).filter(is_active=True)

        # Category filter (including children)
        if filters.get('category_slug'):
            try:
                category = Category.objects.get(slug=filters['category_slug'], is_active=True)
                descendant_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
                queryset = queryset.filter(category_id__in=descendant_ids)
            except Category.DoesNotExist:
                queryset = queryset.none()

        # Price range filter
        if filters.get('min_price') is not None:
            queryset = queryset.filter(
                Q(base_price__gte=filters['min_price']) |
                Q(variants__price__gte=filters['min_price'], variants__is_active=True)
            ).distinct()

        if filters.get('max_price') is not None:
            queryset = queryset.filter(
                Q(base_price__lte=filters['max_price']) |
                Q(variants__price__lte=filters['max_price'], variants__is_active=True)
            ).distinct()

        # Featured filter
        if filters.get('is_featured') is not None:
            queryset = queryset.filter(is_featured=filters['is_featured'])

        # In stock filter
        if filters.get('in_stock_only'):
            queryset = queryset.filter(
                variants__is_active=True,
                variants__stock_quantity__gt=0
            ).distinct()

        # Attribute filter
        if filters.get('attribute_values'):
            for attr_value_id in filters['attribute_values']:
                queryset = queryset.filter(
                    variants__attribute_values__attribute_value_id=attr_value_id,
                    variants__is_active=True
                ).distinct()

        # Search
        if filters.get('search'):
            search_query = filters['search']
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(variants__sku__icontains=search_query)
            ).distinct()

        # Sorting
        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')
        order_prefix = '-' if sort_order == 'desc' else ''

        sort_mapping = {
            'created_at': 'created_at',
            'price': 'base_price',
            'name': 'name',
        }
        order_field = sort_mapping.get(sort_by, 'created_at')
        queryset = queryset.order_by(f'{order_prefix}{order_field}')

        # Pagination
        page = filters.get('page', 1)
        page_size = min(filters.get('page_size', 20), 100)  # Max 100 per page

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        pagination = {
            'page': page,
            'page_size': page_size,
            'total_items': paginator.count,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_prev': page_obj.has_previous(),
        }

        return list(page_obj), pagination

    def get_product_by_slug(self, slug: str) -> Optional[Product]:
        """Get product detail by slug."""
        try:
            return Product.objects.select_related('category').prefetch_related(
                'images',
                'variants__attribute_values__attribute_value__attribute'
            ).get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return None

    def create_product(self, data: dict) -> Tuple[Optional[Product], Optional[str]]:
        """Create a new product."""
        try:
            category = Category.objects.get(pk=data['category_id'], is_active=True)
        except Category.DoesNotExist:
            return None, 'Category not found.'

        try:
            with transaction.atomic():
                product = Product.objects.create(
                    name=data['name'],
                    slug=data.get('slug'),
                    description=data.get('description', ''),
                    category=category,
                    base_price=data['base_price'],
                    is_active=data.get('is_active', True),
                    is_featured=data.get('is_featured', False),
                    meta_title=data.get('meta_title', ''),
                    meta_description=data.get('meta_description', ''),
                )
                return product, None
        except Exception as e:
            return None, str(e)

    def update_product(self, product_id: int, data: dict) -> Tuple[Optional[Product], Optional[str]]:
        """Update an existing product."""
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return None, 'Product not found.'

        try:
            with transaction.atomic():
                for field, value in data.items():
                    if value is not None:
                        if field == 'category_id':
                            try:
                                category = Category.objects.get(pk=value, is_active=True)
                                product.category = category
                            except Category.DoesNotExist:
                                return None, 'Category not found.'
                        else:
                            setattr(product, field, value)

                product.save()
                return product, None
        except Exception as e:
            return None, str(e)

    def delete_product(self, product_id: int, soft: bool = True) -> Tuple[bool, Optional[str]]:
        """Delete a product (soft delete by default)."""
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return False, 'Product not found.'

        try:
            with transaction.atomic():
                if soft:
                    product.soft_delete()
                    # Soft delete variants and images
                    from django.utils import timezone
                    product.variants.update(deleted_at=timezone.now())
                    product.images.update(deleted_at=timezone.now())
                else:
                    product.delete()
                return True, None
        except Exception as e:
            return False, str(e)

    def bulk_update_products(self, product_ids: List[int], updates: dict) -> dict:
        """Bulk update products."""
        success_count = 0
        failed_ids = []

        with transaction.atomic():
            for product_id in product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    for field, value in updates.items():
                        if value is not None:
                            if field == 'category_id':
                                try:
                                    category = Category.objects.get(pk=value)
                                    product.category = category
                                except Category.DoesNotExist:
                                    failed_ids.append(product_id)
                                    continue
                            else:
                                setattr(product, field, value)
                    product.save()
                    success_count += 1
                except Product.DoesNotExist:
                    failed_ids.append(product_id)

        return {
            'success_count': success_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'message': f'Updated {success_count} products.'
        }
