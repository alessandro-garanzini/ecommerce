from django.db import models
from django.utils.text import slugify
from core.models import BaseModel
from auditlog.registry import auditlog


class Product(BaseModel):
    """
    Main product model. Each product can have multiple variants.
    Base price can be overridden by variant-specific prices.
    """
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, help_text="Rich text product description")

    # Category relationship
    category = models.ForeignKey(
        'catalog.Category',
        on_delete=models.PROTECT,
        related_name='products'
    )

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default price, can be overridden by variants"
    )

    # Flags
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    # SEO fields
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        db_table = 'catalog_products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        """Generate unique slug from name."""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Product.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @property
    def total_stock(self) -> int:
        """Sum of stock across all active variants."""
        return self.variants.filter(is_active=True).aggregate(
            total=models.Sum('stock_quantity')
        )['total'] or 0

    @property
    def is_in_stock(self) -> bool:
        """Check if any variant has stock."""
        return self.variants.filter(is_active=True, stock_quantity__gt=0).exists()

    @property
    def min_price(self):
        """Get minimum price across variants (or base_price if no variants with price)."""
        variant_min = self.variants.filter(
            is_active=True, price__isnull=False
        ).aggregate(min_price=models.Min('price'))['min_price']

        if variant_min:
            return min(variant_min, self.base_price)
        return self.base_price

    @property
    def max_price(self):
        """Get maximum price across variants."""
        variant_max = self.variants.filter(
            is_active=True, price__isnull=False
        ).aggregate(max_price=models.Max('price'))['max_price']

        if variant_max:
            return max(variant_max, self.base_price)
        return self.base_price

    @property
    def primary_image(self):
        """Get the primary image or first image."""
        return self.images.filter(is_primary=True).first() or self.images.first()


auditlog.register(Product)
