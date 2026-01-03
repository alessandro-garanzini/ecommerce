from typing import List, Optional
from ninja import Router
from accounts.auth import jwt_auth, staff_jwt_auth, admin_jwt_auth

from .models import (
    Category, Product, ProductVariant, ProductAttribute,
    ProductAttributeValue, ProductImage
)
from .schemas import (
    # Category
    CategoryCreateSchema, CategoryUpdateSchema, CategoryListSchema,
    CategoryTreeSchema, CategoryDetailSchema,
    # Product
    ProductCreateSchema, ProductUpdateSchema, ProductListSchema,
    ProductDetailSchema, ProductBulkUpdateSchema, PaginatedProductsSchema,
    # Variant
    ProductVariantCreateSchema, ProductVariantUpdateSchema,
    ProductVariantListSchema, StockUpdateSchema, BulkStockUpdateSchema,
    # Image
    ProductImageSchema, ProductImageCreateSchema,
    ProductImageUpdateSchema, ImageReorderSchema,
    # Attribute
    ProductAttributeSchema, ProductAttributeCreateSchema,
    ProductAttributeValueSchema, ProductAttributeValueCreateSchema,
    ProductAttributeWithValuesSchema,
    # Common
    MessageSchema, BulkOperationResultSchema,
)
from .services import CategoryService, ProductService, VariantService


router = Router(tags=['Catalog'])

# Service instances
category_service = CategoryService()
product_service = ProductService()
variant_service = VariantService()


# ============ PUBLIC ENDPOINTS (No Auth) ============

# --- Categories ---

@router.get('/categories', response=List[CategoryTreeSchema], auth=None)
def list_categories(request):
    """
    Get category tree structure.
    Returns nested categories for navigation.
    """
    return category_service.get_category_tree(include_inactive=False)


@router.get('/categories/{slug}', response={200: CategoryDetailSchema, 404: MessageSchema}, auth=None)
def get_category(request, slug: str):
    """
    Get category detail by slug.
    Includes ancestors for breadcrumb navigation.
    """
    category = category_service.get_category_by_slug(slug)
    if not category:
        return 404, {'message': 'Category not found.'}

    ancestors = list(category.get_ancestors())
    return 200, {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'image_url': category.image_url,
        'is_active': category.is_active,
        'parent_id': category.parent_id,
        'level': category.level,
        'product_count': category.product_count,
        'full_path': category.full_path,
        'ancestors': [
            {
                'id': a.id,
                'name': a.name,
                'slug': a.slug,
                'description': a.description,
                'image_url': a.image_url,
                'is_active': a.is_active,
                'parent_id': a.parent_id,
                'level': a.level,
                'product_count': 0,
            }
            for a in ancestors
        ]
    }


# --- Products ---

@router.get('/products', response=PaginatedProductsSchema, auth=None)
def list_products(
    request,
    category_slug: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    in_stock_only: Optional[bool] = False,
    attribute_values: Optional[str] = None,  # Comma-separated IDs
    search: Optional[str] = None,
    sort_by: Optional[str] = 'created_at',
    sort_order: Optional[str] = 'desc',
    page: int = 1,
    page_size: int = 20,
):
    """
    List products with filtering and pagination.
    Supports filtering by category, price, attributes, and search.
    """
    # Parse attribute_values from comma-separated string
    attr_values = None
    if attribute_values:
        try:
            attr_values = [int(x.strip()) for x in attribute_values.split(',')]
        except ValueError:
            pass

    filters = {
        'category_slug': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'is_featured': is_featured,
        'in_stock_only': in_stock_only,
        'attribute_values': attr_values,
        'search': search,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'page': page,
        'page_size': page_size,
    }

    products, pagination = product_service.list_products(filters)

    items = []
    for p in products:
        primary_img = p.primary_image
        items.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'base_price': p.base_price,
            'min_price': p.min_price,
            'max_price': p.max_price,
            'is_active': p.is_active,
            'is_featured': p.is_featured,
            'is_in_stock': p.is_in_stock,
            'total_stock': p.total_stock,
            'category_id': p.category_id,
            'category_name': p.category.name,
            'primary_image_url': primary_img.image_url if primary_img else None,
            'created_at': p.created_at,
        })

    return {
        'items': items,
        'page': pagination['page'],
        'page_size': pagination['page_size'],
        'total_items': pagination['total_items'],
        'total_pages': pagination['total_pages'],
        'has_next': pagination['has_next'],
        'has_prev': pagination['has_prev'],
    }


@router.get('/products/{slug}', response={200: ProductDetailSchema, 404: MessageSchema}, auth=None)
def get_product(request, slug: str):
    """
    Get product detail by slug.
    Includes variants, images, and category info.
    """
    product = product_service.get_product_by_slug(slug)
    if not product:
        return 404, {'message': 'Product not found.'}

    # Build variant list with attributes
    variants = []
    for v in product.variants.filter(is_active=True):
        attrs = []
        for vav in v.attribute_values.all():
            av = vav.attribute_value
            attrs.append({
                'id': av.id,
                'attribute_id': av.attribute_id,
                'attribute_name': av.attribute.name,
                'value': av.value,
            })
        variants.append({
            'id': v.id,
            'sku': v.sku,
            'name': v.name,
            'price': v.price,
            'effective_price': v.effective_price,
            'stock_quantity': v.stock_quantity,
            'low_stock_threshold': v.low_stock_threshold,
            'is_active': v.is_active,
            'is_in_stock': v.is_in_stock,
            'is_low_stock': v.is_low_stock,
            'weight': v.weight,
            'attributes': attrs,
        })

    # Build image list
    images = [
        {
            'id': img.id,
            'image_url': img.image_url,
            'alt_text': img.alt_text,
            'position': img.position,
            'is_primary': img.is_primary,
        }
        for img in product.images.all()
    ]

    return 200, {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'base_price': product.base_price,
        'min_price': product.min_price,
        'max_price': product.max_price,
        'is_active': product.is_active,
        'is_featured': product.is_featured,
        'is_in_stock': product.is_in_stock,
        'total_stock': product.total_stock,
        'meta_title': product.meta_title,
        'meta_description': product.meta_description,
        'category': {
            'id': product.category.id,
            'name': product.category.name,
            'slug': product.category.slug,
            'description': product.category.description,
            'image_url': product.category.image_url,
            'is_active': product.category.is_active,
            'parent_id': product.category.parent_id,
            'level': product.category.level,
            'product_count': 0,
        },
        'variants': variants,
        'images': images,
        'created_at': product.created_at,
        'updated_at': product.updated_at,
    }


# --- Attributes (public for filtering) ---

@router.get('/attributes', response=List[ProductAttributeWithValuesSchema], auth=None)
def list_attributes(request):
    """
    List all product attributes with their values.
    Used for building filter UI.
    """
    attributes = ProductAttribute.objects.prefetch_related('values').all()
    return [
        {
            'id': attr.id,
            'name': attr.name,
            'values': [
                {
                    'id': v.id,
                    'attribute_id': attr.id,
                    'value': v.value,
                }
                for v in attr.values.all()
            ]
        }
        for attr in attributes
    ]


# ============ ADMIN ENDPOINTS (Staff/Admin Auth) ============

# --- Category Admin ---

@router.post('/admin/categories', response={201: CategoryListSchema, 400: MessageSchema}, auth=staff_jwt_auth)
def create_category(request, payload: CategoryCreateSchema):
    """Create a new category (staff only)."""
    category, error = category_service.create_category(payload.dict())
    if error:
        return 400, {'message': error}

    return 201, {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'image_url': category.image_url,
        'is_active': category.is_active,
        'parent_id': category.parent_id,
        'level': category.level,
        'product_count': 0,
    }


@router.put('/admin/categories/{category_id}', response={200: CategoryListSchema, 400: MessageSchema, 404: MessageSchema}, auth=staff_jwt_auth)
def update_category(request, category_id: int, payload: CategoryUpdateSchema):
    """Update a category (staff only)."""
    category, error = category_service.update_category(category_id, payload.dict(exclude_unset=True))
    if error:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    return 200, {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'image_url': category.image_url,
        'is_active': category.is_active,
        'parent_id': category.parent_id,
        'level': category.level,
        'product_count': category.product_count,
    }


@router.delete('/admin/categories/{category_id}', response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema}, auth=admin_jwt_auth)
def delete_category(request, category_id: int):
    """Delete a category (admin only)."""
    success, error = category_service.delete_category(category_id)
    if not success:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    return 200, {'message': 'Category deleted successfully.'}


# --- Product Admin ---

@router.post('/admin/products', response={201: ProductListSchema, 400: MessageSchema}, auth=staff_jwt_auth)
def create_product(request, payload: ProductCreateSchema):
    """Create a new product (staff only)."""
    product, error = product_service.create_product(payload.dict())
    if error:
        return 400, {'message': error}

    return 201, {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'base_price': product.base_price,
        'min_price': product.min_price,
        'max_price': product.max_price,
        'is_active': product.is_active,
        'is_featured': product.is_featured,
        'is_in_stock': product.is_in_stock,
        'total_stock': product.total_stock,
        'category_id': product.category_id,
        'category_name': product.category.name,
        'primary_image_url': None,
        'created_at': product.created_at,
    }


@router.post('/admin/products/bulk-update', response=BulkOperationResultSchema, auth=staff_jwt_auth)
def bulk_update_products(request, payload: ProductBulkUpdateSchema):
    """Bulk update products (staff only)."""
    updates = {}
    if payload.is_active is not None:
        updates['is_active'] = payload.is_active
    if payload.is_featured is not None:
        updates['is_featured'] = payload.is_featured
    if payload.category_id is not None:
        updates['category_id'] = payload.category_id

    result = product_service.bulk_update_products(payload.product_ids, updates)
    return result


@router.put('/admin/products/{product_id}', response={200: ProductListSchema, 400: MessageSchema, 404: MessageSchema}, auth=staff_jwt_auth)
def update_product(request, product_id: int, payload: ProductUpdateSchema):
    """Update a product (staff only)."""
    product, error = product_service.update_product(product_id, payload.dict(exclude_unset=True))
    if error:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    primary_img = product.primary_image
    return 200, {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'base_price': product.base_price,
        'min_price': product.min_price,
        'max_price': product.max_price,
        'is_active': product.is_active,
        'is_featured': product.is_featured,
        'is_in_stock': product.is_in_stock,
        'total_stock': product.total_stock,
        'category_id': product.category_id,
        'category_name': product.category.name,
        'primary_image_url': primary_img.image_url if primary_img else None,
        'created_at': product.created_at,
    }


@router.delete('/admin/products/{product_id}', response={200: MessageSchema, 404: MessageSchema}, auth=admin_jwt_auth)
def delete_product(request, product_id: int):
    """Delete a product (admin only)."""
    success, error = product_service.delete_product(product_id)
    if not success:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    return 200, {'message': 'Product deleted successfully.'}


# --- Variant Admin ---

@router.post('/admin/variants', response={201: ProductVariantListSchema, 400: MessageSchema}, auth=staff_jwt_auth)
def create_variant(request, payload: ProductVariantCreateSchema):
    """Create a new product variant (staff only)."""
    variant, error = variant_service.create_variant(payload.dict())
    if error:
        return 400, {'message': error}

    attrs = []
    for vav in variant.attribute_values.select_related('attribute_value__attribute').all():
        av = vav.attribute_value
        attrs.append({
            'id': av.id,
            'attribute_id': av.attribute_id,
            'attribute_name': av.attribute.name,
            'value': av.value,
        })

    return 201, {
        'id': variant.id,
        'sku': variant.sku,
        'name': variant.name,
        'price': variant.price,
        'effective_price': variant.effective_price,
        'stock_quantity': variant.stock_quantity,
        'low_stock_threshold': variant.low_stock_threshold,
        'is_active': variant.is_active,
        'is_in_stock': variant.is_in_stock,
        'is_low_stock': variant.is_low_stock,
        'weight': variant.weight,
        'attributes': attrs,
    }


@router.put('/admin/variants/{variant_id}', response={200: ProductVariantListSchema, 400: MessageSchema, 404: MessageSchema}, auth=staff_jwt_auth)
def update_variant(request, variant_id: int, payload: ProductVariantUpdateSchema):
    """Update a variant (staff only)."""
    variant, error = variant_service.update_variant(variant_id, payload.dict(exclude_unset=True))
    if error:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    attrs = []
    for vav in variant.attribute_values.select_related('attribute_value__attribute').all():
        av = vav.attribute_value
        attrs.append({
            'id': av.id,
            'attribute_id': av.attribute_id,
            'attribute_name': av.attribute.name,
            'value': av.value,
        })

    return 200, {
        'id': variant.id,
        'sku': variant.sku,
        'name': variant.name,
        'price': variant.price,
        'effective_price': variant.effective_price,
        'stock_quantity': variant.stock_quantity,
        'low_stock_threshold': variant.low_stock_threshold,
        'is_active': variant.is_active,
        'is_in_stock': variant.is_in_stock,
        'is_low_stock': variant.is_low_stock,
        'weight': variant.weight,
        'attributes': attrs,
    }


@router.delete('/admin/variants/{variant_id}', response={200: MessageSchema, 404: MessageSchema}, auth=admin_jwt_auth)
def delete_variant(request, variant_id: int):
    """Delete a variant (admin only)."""
    success, error = variant_service.delete_variant(variant_id)
    if not success:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    return 200, {'message': 'Variant deleted successfully.'}


# --- Stock Management ---

@router.put('/admin/variants/{variant_id}/stock', response={200: ProductVariantListSchema, 400: MessageSchema, 404: MessageSchema}, auth=staff_jwt_auth)
def update_stock(request, variant_id: int, payload: StockUpdateSchema):
    """Update variant stock (staff only)."""
    variant, error = variant_service.update_stock(variant_id, payload.quantity, payload.operation)
    if error:
        if 'not found' in error.lower():
            return 404, {'message': error}
        return 400, {'message': error}

    return 200, {
        'id': variant.id,
        'sku': variant.sku,
        'name': variant.name,
        'price': variant.price,
        'effective_price': variant.effective_price,
        'stock_quantity': variant.stock_quantity,
        'low_stock_threshold': variant.low_stock_threshold,
        'is_active': variant.is_active,
        'is_in_stock': variant.is_in_stock,
        'is_low_stock': variant.is_low_stock,
        'weight': variant.weight,
        'attributes': [],
    }


@router.post('/admin/stock/bulk-update', response=BulkOperationResultSchema, auth=staff_jwt_auth)
def bulk_update_stock(request, payload: BulkStockUpdateSchema):
    """Bulk update stock for multiple variants (staff only)."""
    result = variant_service.bulk_update_stock([u.dict() for u in payload.updates])
    return result


@router.get('/admin/stock/low', response=List[ProductVariantListSchema], auth=staff_jwt_auth)
def get_low_stock_variants(request):
    """Get all variants with low stock (staff only)."""
    variants = variant_service.get_low_stock_variants()
    return [
        {
            'id': v.id,
            'sku': v.sku,
            'name': v.name,
            'price': v.price,
            'effective_price': v.effective_price,
            'stock_quantity': v.stock_quantity,
            'low_stock_threshold': v.low_stock_threshold,
            'is_active': v.is_active,
            'is_in_stock': v.is_in_stock,
            'is_low_stock': v.is_low_stock,
            'weight': v.weight,
            'attributes': [],
        }
        for v in variants
    ]


# --- Image Admin ---

@router.post('/admin/images', response={201: ProductImageSchema, 400: MessageSchema}, auth=staff_jwt_auth)
def create_image(request, payload: ProductImageCreateSchema):
    """Add an image to a product (staff only)."""
    try:
        product = Product.objects.get(pk=payload.product_id)
    except Product.DoesNotExist:
        return 400, {'message': 'Product not found.'}

    image = ProductImage.objects.create(
        product=product,
        image_url=payload.image_url,
        alt_text=payload.alt_text or '',
        position=payload.position or 0,
        is_primary=payload.is_primary or False,
    )

    return 201, {
        'id': image.id,
        'image_url': image.image_url,
        'alt_text': image.alt_text,
        'position': image.position,
        'is_primary': image.is_primary,
    }


@router.post('/admin/images/reorder', response={200: MessageSchema, 400: MessageSchema}, auth=staff_jwt_auth)
def reorder_images(request, payload: ImageReorderSchema):
    """Reorder images for a product (staff only)."""
    for position, image_id in enumerate(payload.image_ids):
        ProductImage.objects.filter(pk=image_id).update(position=position)

    return 200, {'message': 'Images reordered successfully.'}


@router.put('/admin/images/{image_id}', response={200: ProductImageSchema, 400: MessageSchema, 404: MessageSchema}, auth=staff_jwt_auth)
def update_image(request, image_id: int, payload: ProductImageUpdateSchema):
    """Update an image (staff only)."""
    try:
        image = ProductImage.objects.get(pk=image_id)
    except ProductImage.DoesNotExist:
        return 404, {'message': 'Image not found.'}

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(image, field, value)

    image.save()

    return 200, {
        'id': image.id,
        'image_url': image.image_url,
        'alt_text': image.alt_text,
        'position': image.position,
        'is_primary': image.is_primary,
    }


@router.delete('/admin/images/{image_id}', response={200: MessageSchema, 404: MessageSchema}, auth=staff_jwt_auth)
def delete_image(request, image_id: int):
    """Delete an image (staff only)."""
    try:
        image = ProductImage.objects.get(pk=image_id)
    except ProductImage.DoesNotExist:
        return 404, {'message': 'Image not found.'}

    image.soft_delete()
    return 200, {'message': 'Image deleted successfully.'}


# --- Attribute Admin ---

@router.post('/admin/attributes', response={201: ProductAttributeSchema, 400: MessageSchema}, auth=admin_jwt_auth)
def create_attribute(request, payload: ProductAttributeCreateSchema):
    """Create a new product attribute (admin only)."""
    if ProductAttribute.objects.filter(name=payload.name).exists():
        return 400, {'message': 'Attribute with this name already exists.'}

    attr = ProductAttribute.objects.create(name=payload.name)
    return 201, {'id': attr.id, 'name': attr.name}


@router.post('/admin/attributes/values', response={201: ProductAttributeValueSchema, 400: MessageSchema}, auth=admin_jwt_auth)
def create_attribute_value(request, payload: ProductAttributeValueCreateSchema):
    """Create a new attribute value (admin only)."""
    try:
        attr = ProductAttribute.objects.get(pk=payload.attribute_id)
    except ProductAttribute.DoesNotExist:
        return 400, {'message': 'Attribute not found.'}

    if ProductAttributeValue.objects.filter(attribute=attr, value=payload.value).exists():
        return 400, {'message': 'Value already exists for this attribute.'}

    value = ProductAttributeValue.objects.create(attribute=attr, value=payload.value)
    return 201, {'id': value.id, 'attribute_id': attr.id, 'value': value.value}
