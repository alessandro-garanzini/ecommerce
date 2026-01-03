from django.db import models
from django.db.models import F
from core.models import BaseModel
from auditlog.registry import auditlog


class ProductVariant(BaseModel):
    """
    Product variant with unique SKU, price, and stock.
    Each variant can have multiple attribute values (e.g., Red + Large).
    """
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='variants'
    )

    # Identification
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(
        max_length=255,
        help_text="Variant name, e.g., 'Red - Large'"
    )

    # Pricing (overrides product base_price if set)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank to use product base price"
    )

    # Stock
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text="Alert threshold for low stock"
    )

    # Physical attributes (optional)
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in grams"
    )
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'catalog_product_variants'
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        ordering = ['product', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def effective_price(self):
        """Return variant price if set, otherwise product base price."""
        return self.price if self.price is not None else self.product.base_price

    @property
    def is_in_stock(self) -> bool:
        """Check if variant has stock."""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below threshold."""
        return self.stock_quantity <= self.low_stock_threshold

    def reduce_stock(self, quantity: int) -> bool:
        """
        Reduce stock by quantity. Returns False if insufficient stock.
        Uses database-level update for concurrency safety.
        """
        updated = ProductVariant.objects.filter(
            pk=self.pk,
            stock_quantity__gte=quantity
        ).update(stock_quantity=F('stock_quantity') - quantity)

        if updated:
            self.refresh_from_db()
            return True
        return False

    def add_stock(self, quantity: int):
        """Add stock quantity."""
        ProductVariant.objects.filter(pk=self.pk).update(
            stock_quantity=F('stock_quantity') + quantity
        )
        self.refresh_from_db()


auditlog.register(ProductVariant)
