from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Inventory(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.sku} - {self.quantity}"


class Dealer(TimeStampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Order(TimeStampedModel):
    STATUS_DRAFT = 'DRAFT'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    dealer = models.ForeignKey(Dealer, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=32, unique=True, blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.dealer.name} - {self.status}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_sku = models.CharField(max_length=64)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        # preserve price at time of save
        if not self.unit_price and self.product:
            self.unit_price = self.product.price
        self.line_total = Decimal(self.quantity) * Decimal(self.unit_price)
        # ensure product info is stored
        if self.product:
            self.product_sku = self.product.sku
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number} - {self.product_sku} x {self.quantity}"


class InventoryAdjustment(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='adjustments')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    change = models.IntegerField()  # positive or negative
    note = models.TextField(blank=True)

    def __str__(self):
        return f"Adj {self.product.sku} {self.change} by {self.changed_by}"