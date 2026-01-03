from typing import Optional, Tuple, List
from django.db import transaction
from catalog.models import Category


class CategoryService:
    """Service layer for category operations."""

    def get_category_tree(self, include_inactive: bool = False) -> List[dict]:
        """
        Get full category tree structure.
        Returns nested dict suitable for CategoryTreeSchema.
        """
        queryset = Category.objects.all() if include_inactive else Category.objects.filter(is_active=True)
        root_categories = queryset.filter(parent__isnull=True).order_by('name')

        def build_tree(category):
            children = queryset.filter(parent=category).order_by('name')
            return {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'image_url': category.image_url,
                'is_active': category.is_active,
                'level': category.level,
                'product_count': category.product_count,
                'children': [build_tree(child) for child in children]
            }

        return [build_tree(cat) for cat in root_categories]

    def create_category(self, data: dict) -> Tuple[Optional[Category], Optional[str]]:
        """Create a new category."""
        try:
            with transaction.atomic():
                parent = None
                if data.get('parent_id'):
                    try:
                        parent = Category.objects.get(pk=data['parent_id'])
                    except Category.DoesNotExist:
                        return None, 'Parent category not found.'

                category = Category.objects.create(
                    name=data['name'],
                    slug=data.get('slug'),  # Will auto-generate if None
                    description=data.get('description', ''),
                    image_url=data.get('image_url'),
                    is_active=data.get('is_active', True),
                    parent=parent
                )
                return category, None
        except Exception as e:
            return None, str(e)

    def update_category(self, category_id: int, data: dict) -> Tuple[Optional[Category], Optional[str]]:
        """Update an existing category."""
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return None, 'Category not found.'

        try:
            with transaction.atomic():
                for field, value in data.items():
                    if value is not None:
                        if field == 'parent_id':
                            if value:
                                try:
                                    parent = Category.objects.get(pk=value)
                                    # Prevent circular reference
                                    if parent.pk == category.pk or parent in category.get_descendants():
                                        return None, 'Cannot set category as its own parent or descendant.'
                                    category.parent = parent
                                except Category.DoesNotExist:
                                    return None, 'Parent category not found.'
                            else:
                                category.parent = None
                        else:
                            setattr(category, field, value)

                category.save()
                return category, None
        except Exception as e:
            return None, str(e)

    def delete_category(self, category_id: int, soft: bool = True) -> Tuple[bool, Optional[str]]:
        """Delete a category (soft delete by default)."""
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return False, 'Category not found.'

        # Check for products
        if category.products.filter(deleted_at__isnull=True).exists():
            return False, 'Cannot delete category with products. Move or delete products first.'

        try:
            if soft:
                category.soft_delete()
                # Soft delete children as well
                for child in category.get_descendants():
                    child.soft_delete()
            else:
                category.delete()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug."""
        try:
            return Category.objects.get(slug=slug, is_active=True)
        except Category.DoesNotExist:
            return None
