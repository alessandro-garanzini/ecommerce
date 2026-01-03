from typing import Optional, Tuple, List
from django.db import transaction
from django.db.models import F
from catalog.models import Product, ProductVariant, VariantAttributeValue, ProductAttributeValue


class VariantService:
    """Service layer for product variant operations."""

    def create_variant(self, data: dict) -> Tuple[Optional[ProductVariant], Optional[str]]:
        """Create a new product variant."""
        try:
            product = Product.objects.get(pk=data['product_id'])
        except Product.DoesNotExist:
            return None, 'Product not found.'

        # Check for duplicate SKU
        if ProductVariant.all_objects.filter(sku=data['sku']).exists():
            return None, 'SKU already exists.'

        try:
            with transaction.atomic():
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=data['sku'],
                    name=data['name'],
                    price=data.get('price'),
                    stock_quantity=data.get('stock_quantity', 0),
                    low_stock_threshold=data.get('low_stock_threshold', 5),
                    weight=data.get('weight'),
                    length=data.get('length'),
                    width=data.get('width'),
                    height=data.get('height'),
                    is_active=data.get('is_active', True),
                )

                # Add attribute values
                if data.get('attribute_value_ids'):
                    for attr_value_id in data['attribute_value_ids']:
                        try:
                            attr_value = ProductAttributeValue.objects.get(pk=attr_value_id)
                            VariantAttributeValue.objects.create(
                                variant=variant,
                                attribute_value=attr_value
                            )
                        except ProductAttributeValue.DoesNotExist:
                            pass  # Skip invalid attribute values

                return variant, None
        except Exception as e:
            return None, str(e)

    def update_variant(self, variant_id: int, data: dict) -> Tuple[Optional[ProductVariant], Optional[str]]:
        """Update an existing variant."""
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            return None, 'Variant not found.'

        # Check for duplicate SKU
        if data.get('sku') and data['sku'] != variant.sku:
            if ProductVariant.all_objects.filter(sku=data['sku']).exists():
                return None, 'SKU already exists.'

        try:
            with transaction.atomic():
                for field, value in data.items():
                    if value is not None and field != 'attribute_value_ids':
                        setattr(variant, field, value)

                variant.save()

                # Update attribute values if provided
                if 'attribute_value_ids' in data:
                    # Clear existing and add new
                    variant.attribute_values.all().delete()
                    if data['attribute_value_ids']:
                        for attr_value_id in data['attribute_value_ids']:
                            try:
                                attr_value = ProductAttributeValue.objects.get(pk=attr_value_id)
                                VariantAttributeValue.objects.create(
                                    variant=variant,
                                    attribute_value=attr_value
                                )
                            except ProductAttributeValue.DoesNotExist:
                                pass

                return variant, None
        except Exception as e:
            return None, str(e)

    def delete_variant(self, variant_id: int, soft: bool = True) -> Tuple[bool, Optional[str]]:
        """Delete a variant."""
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            return False, 'Variant not found.'

        try:
            if soft:
                variant.soft_delete()
            else:
                variant.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_stock(self, variant_id: int, quantity: int, operation: str = 'set') -> Tuple[Optional[ProductVariant], Optional[str]]:
        """
        Update variant stock.
        Operations: 'set' (replace), 'add' (increment), 'reduce' (decrement)
        """
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            return None, 'Variant not found.'

        try:
            if operation == 'set':
                if quantity < 0:
                    return None, 'Stock quantity cannot be negative.'
                variant.stock_quantity = quantity
                variant.save(update_fields=['stock_quantity'])
            elif operation == 'add':
                variant.add_stock(quantity)
            elif operation == 'reduce':
                if not variant.reduce_stock(quantity):
                    return None, 'Insufficient stock.'
            else:
                return None, 'Invalid operation. Use set, add, or reduce.'

            variant.refresh_from_db()
            return variant, None
        except Exception as e:
            return None, str(e)

    def bulk_update_stock(self, updates: List[dict]) -> dict:
        """Bulk update stock for multiple variants."""
        success_count = 0
        failed_ids = []

        with transaction.atomic():
            for update in updates:
                variant_id = update.get('variant_id')
                quantity = update.get('quantity')
                operation = update.get('operation', 'set')

                result, error = self.update_stock(variant_id, quantity, operation)
                if result:
                    success_count += 1
                else:
                    failed_ids.append(variant_id)

        return {
            'success_count': success_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'message': f'Updated {success_count} variants.'
        }

    def get_low_stock_variants(self) -> List[ProductVariant]:
        """Get all variants with low stock."""
        return ProductVariant.objects.filter(
            is_active=True,
            stock_quantity__lte=F('low_stock_threshold')
        ).select_related('product')
