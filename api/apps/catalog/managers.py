from django.db import models
from core.models import BaseModelManager


class CategoryManager(BaseModelManager):
    """Custom manager for Category model."""

    def active(self):
        """Get only active categories."""
        return self.get_queryset().filter(is_active=True)

    def root_categories(self):
        """Get top-level categories."""
        return self.active().filter(parent__isnull=True)

    def with_product_count(self):
        """Annotate categories with product count."""
        from django.db.models import Count, Q
        return self.get_queryset().annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True, products__deleted_at__isnull=True)
            )
        )


class ProductManager(BaseModelManager):
    """Custom manager for Product model."""

    def active(self):
        """Get only active products."""
        return self.get_queryset().filter(is_active=True)

    def featured(self):
        """Get featured products."""
        return self.active().filter(is_featured=True)

    def in_stock(self):
        """Get products with stock available."""
        return self.active().filter(
            variants__is_active=True,
            variants__stock_quantity__gt=0
        ).distinct()

    def by_category(self, category):
        """
        Get products in category and all descendants.
        Uses MPTT for efficient tree queries.
        """
        descendant_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
        return self.active().filter(category_id__in=descendant_ids)

    def with_prices(self):
        """Annotate products with min/max prices from variants."""
        from django.db.models import Min, Max
        return self.get_queryset().annotate(
            variant_min_price=Min('variants__price', filter=models.Q(variants__is_active=True)),
            variant_max_price=Max('variants__price', filter=models.Q(variants__is_active=True)),
        )

    def filter_by_price_range(self, min_price=None, max_price=None):
        """Filter products by price range."""
        qs = self.active()
        if min_price is not None:
            qs = qs.filter(
                models.Q(base_price__gte=min_price) |
                models.Q(variants__price__gte=min_price, variants__is_active=True)
            )
        if max_price is not None:
            qs = qs.filter(
                models.Q(base_price__lte=max_price) |
                models.Q(variants__price__lte=max_price, variants__is_active=True)
            )
        return qs.distinct()

    def filter_by_attributes(self, attribute_values: list):
        """
        Filter products by attribute value IDs.
        Products must have variants with ALL specified attribute values.
        """
        if not attribute_values:
            return self.get_queryset()

        qs = self.active()
        for attr_value_id in attribute_values:
            qs = qs.filter(
                variants__attribute_values__attribute_value_id=attr_value_id,
                variants__is_active=True
            )
        return qs.distinct()

    def search(self, query: str):
        """Search products by name or description."""
        return self.active().filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        )


class ProductVariantManager(BaseModelManager):
    """Custom manager for ProductVariant model."""

    def active(self):
        """Get only active variants."""
        return self.get_queryset().filter(is_active=True)

    def in_stock(self):
        """Get variants with stock."""
        return self.active().filter(stock_quantity__gt=0)

    def low_stock(self):
        """Get variants with low stock."""
        from django.db.models import F
        return self.active().filter(stock_quantity__lte=F('low_stock_threshold'))
