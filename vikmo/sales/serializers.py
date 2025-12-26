from rest_framework import serializers
from . import models
from django.db import transaction
from django.utils import timezone


class ProductSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source='inventory.quantity', read_only=True)

    class Meta:
        model = models.Product
        fields = ['id', 'name', 'sku', 'description', 'price', 'active', 'stock', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at')


class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dealer
        fields = ['id', 'name', 'code', 'contact_name', 'email', 'phone', 'address', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at')


class OrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.OrderItem
        fields = ['id', 'product', 'product_sku', 'product_name', 'quantity', 'unit_price', 'line_total']
        read_only_fields = ('product_sku', 'product_name', 'unit_price', 'line_total')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    dealer = serializers.PrimaryKeyRelatedField(queryset=models.Dealer.objects.all())

    class Meta:
        model = models.Order
        fields = ['id', 'order_number', 'dealer', 'status', 'total_amount', 'items', 'created_at', 'updated_at']
        read_only_fields = ('order_number', 'status', 'total_amount', 'created_at', 'updated_at')

    def validate(self, data):
        # if updating, ensure order is draft
        instance = getattr(self, 'instance', None)
        if instance and instance.status != models.Order.STATUS_DRAFT:
            raise serializers.ValidationError('Only Draft orders can be edited')
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = models.Order.objects.create(**validated_data)
        # generate order_number using pk and date
        order.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{order.pk:04d}"
        order.save()
        total = 0
        for item in items_data:
            product = item.get('product')
            quantity = item.get('quantity')
            unit_price = product.price
            oi = models.OrderItem.objects.create(
                order=order,
                product=product,
                product_sku=product.sku,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                line_total=unit_price * quantity,
            )
            total += oi.line_total
        order.total_amount = total
        order.save()
        return order

    def update(self, instance, validated_data):
        if instance.status != models.Order.STATUS_DRAFT:
            raise serializers.ValidationError('Only Draft orders can be edited')
        items_data = validated_data.pop('items', None)
        # update fields (dealer can't be changed for simplicity)
        instance.save()
        if items_data is not None:
            # replace items
            instance.items.all().delete()
            total = 0
            for item in items_data:
                product = item.get('product')
                quantity = item.get('quantity')
                unit_price = product.price
                oi = models.OrderItem.objects.create(
                    order=instance,
                    product=product,
                    product_sku=product.sku,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=unit_price * quantity,
                )
                total += oi.line_total
            instance.total_amount = total
            instance.save()
        return instance


class InventoryAdjustmentSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=models.Product.objects.all(), required=False)

    class Meta:
        model = models.InventoryAdjustment
        fields = ['id', 'product', 'change', 'note', 'changed_by', 'created_at']
        read_only_fields = ('created_at', 'changed_by')

    def create(self, validated_data):
        user = self.context['request'].user
        adj = models.InventoryAdjustment.objects.create(changed_by=user, **validated_data)
        inv, _ = models.Inventory.objects.get_or_create(product=adj.product)
        inv.quantity = models.F('quantity') + adj.change
        inv.save()
        # refresh
        inv.refresh_from_db()
        return adj