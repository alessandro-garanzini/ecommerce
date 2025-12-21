from django.db import models
from django.utils import timezone


class BaseModelManager(models.Manager):
    """Manager that excludes soft-deleted objects by default"""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class BaseModelAllManager(models.Manager):
    """Manager that includes soft-deleted objects"""

    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    """
    Abstract base model with timestamp tracking and soft delete functionality.

    All models inheriting from this will have:
    - created_at: Auto-set on creation
    - updated_at: Auto-updated on save
    - deleted_at: Timestamp for soft deletes

    Managers:
    - objects: Default manager (excludes soft-deleted)
    - all_objects: Includes soft-deleted objects
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Default manager excludes soft-deleted objects
    objects = BaseModelManager()
    # Manager that includes soft-deleted objects
    all_objects = BaseModelAllManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Soft delete the object by setting deleted_at timestamp"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """Restore a soft-deleted object"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        """Check if the object is soft-deleted"""
        return self.deleted_at is not None
