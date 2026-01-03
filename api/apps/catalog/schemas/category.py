from typing import Optional, List
from ninja import Schema


class CategoryBaseSchema(Schema):
    """Base category schema for creation/update."""
    name: str
    description: Optional[str] = ''
    image_url: Optional[str] = None
    is_active: Optional[bool] = True
    parent_id: Optional[int] = None


class CategoryCreateSchema(CategoryBaseSchema):
    """Schema for creating a category."""
    slug: Optional[str] = None  # Auto-generated if not provided


class CategoryUpdateSchema(Schema):
    """Schema for updating a category (partial)."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None


class CategoryListSchema(Schema):
    """Schema for category list items."""
    id: int
    name: str
    slug: str
    description: str
    image_url: Optional[str]
    is_active: bool
    parent_id: Optional[int]
    level: int
    product_count: int = 0


class CategoryTreeSchema(Schema):
    """Schema for category tree with children."""
    id: int
    name: str
    slug: str
    description: str
    image_url: Optional[str]
    is_active: bool
    level: int
    children: List['CategoryTreeSchema'] = []
    product_count: int = 0


class CategoryDetailSchema(CategoryListSchema):
    """Detailed category schema with ancestors."""
    full_path: str
    ancestors: List['CategoryListSchema'] = []


# Enable self-referencing for CategoryTreeSchema
CategoryTreeSchema.model_rebuild()
