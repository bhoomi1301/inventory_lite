from django.contrib import admin
from . import models


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'active')
    search_fields = ('name', 'sku')


@admin.register(models.Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity')
    search_fields = ('product__sku', 'product__name')


@admin.register(models.Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_name', 'email')
    search_fields = ('name', 'code')


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    readonly_fields = ('product_sku', 'product_name', 'unit_price', 'line_total')
    extra = 0


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'dealer', 'status', 'total_amount', 'created_at')
    readonly_fields = ('order_number', 'total_amount')
    inlines = [OrderItemInline]


@admin.register(models.InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'change', 'changed_by', 'created_at')
    readonly_fields = ('created_at',)