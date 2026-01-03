from typing import Optional, List
from ninja import Schema


class ProductImageSchema(Schema):
    """Schema for product image."""
    id: int
    image_url: str
    alt_text: str
    position: int
    is_primary: bool


class ProductImageCreateSchema(Schema):
    """Schema for creating a product image."""
    product_id: int
    image_url: str
    alt_text: Optional[str] = ''
    position: Optional[int] = 0
    is_primary: Optional[bool] = False


class ProductImageUpdateSchema(Schema):
    """Schema for updating a product image."""
    image_url: Optional[str] = None
    alt_text: Optional[str] = None
    position: Optional[int] = None
    is_primary: Optional[bool] = None


class ImageReorderSchema(Schema):
    """Schema for reordering images."""
    image_ids: List[int]  # Ordered list of image IDs
