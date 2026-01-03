from typing import Optional, List
from ninja import Schema
from decimal import Decimal
from datetime import datetime
from .category import CategoryListSchema
from .variant import ProductVariantListSchema
from .image import ProductImageSchema


class ProductBaseSchema(Schema):
    """Base product schema."""
    name: str
    description: Optional[str] = ''
    category_id: int
    base_price: Decimal
    is_active: Optional[bool] = True
    is_featured: Optional[bool] = False
    meta_title: Optional[str] = ''
    meta_description: Optional[str] = ''


class ProductCreateSchema(ProductBaseSchema):
    """Schema for creating a product."""
    slug: Optional[str] = None  # Auto-generated if not provided


class ProductUpdateSchema(Schema):
    """Schema for updating a product (partial)."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    base_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductListSchema(Schema):
    """Schema for product list items."""
    id: int
    name: str
    slug: str
    base_price: Decimal
    min_price: Decimal
    max_price: Decimal
    is_active: bool
    is_featured: bool
    is_in_stock: bool
    total_stock: int
    category_id: int
    category_name: str
    primary_image_url: Optional[str]
    created_at: datetime


class ProductDetailSchema(Schema):
    """Detailed product schema with relations."""
    id: int
    name: str
    slug: str
    description: str
    base_price: Decimal
    min_price: Decimal
    max_price: Decimal
    is_active: bool
    is_featured: bool
    is_in_stock: bool
    total_stock: int
    meta_title: str
    meta_description: str
    category: CategoryListSchema
    variants: List[ProductVariantListSchema]
    images: List[ProductImageSchema]
    created_at: datetime
    updated_at: datetime


class ProductFilterSchema(Schema):
    """Schema for product filtering."""
    category_slug: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    is_featured: Optional[bool] = None
    in_stock_only: Optional[bool] = False
    attribute_values: Optional[List[int]] = None
    search: Optional[str] = None
    sort_by: Optional[str] = 'created_at'  # created_at, price, name
    sort_order: Optional[str] = 'desc'  # asc, desc
    page: Optional[int] = 1
    page_size: Optional[int] = 20


class ProductBulkUpdateSchema(Schema):
    """Schema for bulk product operations."""
    product_ids: List[int]
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None


class PaginatedProductsSchema(Schema):
    """Paginated products response."""
    items: List[ProductListSchema]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool
