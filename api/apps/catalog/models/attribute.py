from django.db import models
from core.models import BaseModel
from auditlog.registry import auditlog


class ProductAttribute(BaseModel):
    """
    Defines an attribute type (e.g., Size, Color, Material).
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'catalog_product_attributes'
        verbose_name = 'Product Attribute'
        verbose_name_plural = 'Product Attributes'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductAttributeValue(BaseModel):
    """
    Specific attribute value (e.g., Red, Large, Cotton).
    """
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values'
    )
    value = models.CharField(max_length=100)

    class Meta:
        db_table = 'catalog_product_attribute_values'
        verbose_name = 'Attribute Value'
        verbose_name_plural = 'Attribute Values'
        ordering = ['attribute', 'value']
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class VariantAttributeValue(BaseModel):
    """
    Links variants to their attribute values.
    M2M through table for variant attribute combinations.
    """
    variant = models.ForeignKey(
        'catalog.ProductVariant',
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )
    attribute_value = models.ForeignKey(
        ProductAttributeValue,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    class Meta:
        db_table = 'catalog_variant_attribute_values'
        verbose_name = 'Variant Attribute Value'
        verbose_name_plural = 'Variant Attribute Values'
        unique_together = ['variant', 'attribute_value']

    def __str__(self):
        return f"{self.variant.sku} - {self.attribute_value}"


auditlog.register(ProductAttribute)
auditlog.register(ProductAttributeValue)
auditlog.register(VariantAttributeValue)
