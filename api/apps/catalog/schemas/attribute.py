from typing import List
from ninja import Schema


class ProductAttributeSchema(Schema):
    """Schema for product attribute."""
    id: int
    name: str


class ProductAttributeCreateSchema(Schema):
    """Schema for creating an attribute."""
    name: str


class ProductAttributeValueSchema(Schema):
    """Schema for attribute value."""
    id: int
    attribute_id: int
    value: str


class ProductAttributeValueCreateSchema(Schema):
    """Schema for creating an attribute value."""
    attribute_id: int
    value: str


class ProductAttributeWithValuesSchema(Schema):
    """Schema for attribute with all its values."""
    id: int
    name: str
    values: List[ProductAttributeValueSchema]
