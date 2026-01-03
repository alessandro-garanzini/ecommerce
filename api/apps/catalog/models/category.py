from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from core.models import BaseModel
from auditlog.registry import auditlog


class Category(MPTTModel, BaseModel):
    """
    Product category with hierarchical structure using MPTT.
    Supports nested categories for efficient tree queries.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # MPTT tree structure
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        db_table = 'catalog_categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['tree_id', 'lft']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        """Generate unique slug from name."""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Category.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'Electronics > Phones > Smartphones')."""
        ancestors = self.get_ancestors(include_self=True)
        return ' > '.join([cat.name for cat in ancestors])

    @property
    def product_count(self) -> int:
        """Count of active products in this category (including children)."""
        from catalog.models.product import Product
        descendant_ids = self.get_descendants(include_self=True).values_list('id', flat=True)
        return Product.objects.filter(category_id__in=descendant_ids, is_active=True).count()


auditlog.register(Category)
