from typing import Optional, List
from ninja import Schema
from decimal import Decimal


class AttributeValueSchema(Schema):
    """Schema for attribute value in variant context."""
    id: int
    attribute_id: int
    attribute_name: str
    value: str


class ProductVariantBaseSchema(Schema):
    """Base variant schema."""
    name: str
    sku: str
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = 0
    low_stock_threshold: Optional[int] = 5
    weight: Optional[Decimal] = None
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    is_active: Optional[bool] = True


class ProductVariantCreateSchema(ProductVariantBaseSchema):
    """Schema for creating a variant."""
    product_id: int
    attribute_value_ids: Optional[List[int]] = []


class ProductVariantUpdateSchema(Schema):
    """Schema for updating a variant (partial)."""
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    weight: Optional[Decimal] = None
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    is_active: Optional[bool] = None
    attribute_value_ids: Optional[List[int]] = None


class ProductVariantListSchema(Schema):
    """Schema for variant list items."""
    id: int
    sku: str
    name: str
    price: Optional[Decimal]
    effective_price: Decimal
    stock_quantity: int
    low_stock_threshold: int
    is_active: bool
    is_in_stock: bool
    is_low_stock: bool
    weight: Optional[Decimal]
    attributes: List[AttributeValueSchema]


class StockUpdateSchema(Schema):
    """Schema for stock updates."""
    quantity: int
    operation: str = 'set'  # set, add, reduce


class BulkStockUpdateSchema(Schema):
    """Schema for bulk stock updates."""
    updates: List['StockUpdateItemSchema']


class StockUpdateItemSchema(Schema):
    """Schema for individual stock update in bulk operations."""
    variant_id: int
    quantity: int
    operation: str = 'set'  # set, add, reduce
