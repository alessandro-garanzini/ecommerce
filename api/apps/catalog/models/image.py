from django.db import models
from core.models import BaseModel
from auditlog.registry import auditlog


class ProductImage(BaseModel):
    """
    Product images with position ordering and primary flag.
    """
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0, db_index=True)
    is_primary = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'catalog_product_images'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['product', 'position']

    def __str__(self):
        return f"{self.product.name} - Image {self.position}"

    def save(self, *args, **kwargs):
        # Auto-set first image as primary if no primary exists
        if not self.pk:  # New image
            existing_primary = ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exists()
            if not existing_primary:
                self.is_primary = True

        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)


auditlog.register(ProductImage)
