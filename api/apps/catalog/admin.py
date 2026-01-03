from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import (
    Category, Product, ProductVariant, ProductAttribute,
    ProductAttributeValue, VariantAttributeValue, ProductImage
)


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'level']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['tree_id', 'lft']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    ordering = ['position']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['sku', 'name', 'price', 'stock_quantity', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'base_price', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    ordering = ['-created_at']


class VariantAttributeValueInline(admin.TabularInline):
    model = VariantAttributeValue
    extra = 1


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'product', 'price', 'stock_quantity', 'is_active']
    list_filter = ['is_active', 'product__category']
    search_fields = ['sku', 'name', 'product__name']
    inlines = [VariantAttributeValueInline]
    ordering = ['product', 'name']


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'created_at']
    list_filter = ['attribute']
    search_fields = ['value', 'attribute__name']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'position', 'is_primary', 'alt_text']
    list_filter = ['is_primary', 'product']
    ordering = ['product', 'position']
