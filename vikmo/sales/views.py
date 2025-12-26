from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from . import models, serializers


class ProductViewSet(viewsets.ModelViewSet):
    queryset = models.Product.objects.all().select_related('inventory')
    serializer_class = serializers.ProductSerializer


class DealerViewSet(viewsets.ModelViewSet):
    queryset = models.Dealer.objects.all()
    serializer_class = serializers.DealerSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        # include orders
        orders = instance.orders.all()
        data['orders'] = [{'id': o.id, 'order_number': o.order_number, 'status': o.status, 'total_amount': o.total_amount} for o in orders]
        return Response(data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = models.Order.objects.all().prefetch_related('items')
    serializer_class = serializers.OrderSerializer

    def update(self, request, *args, **kwargs):
        # disallow changing order status via update and only allow editing Draft orders
        order = self.get_object()
        # explicit check: clients should not change status through the update endpoint
        if 'status' in request.data:
            return Response({'detail': 'Order status cannot be changed via update; use confirm or deliver endpoints'}, status=status.HTTP_400_BAD_REQUEST)
        if order.status != models.Order.STATUS_DRAFT:
            return Response({'detail': 'Only Draft orders can be edited'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != models.Order.STATUS_DRAFT:
            return Response({'detail': 'Only Draft orders can be confirmed'}, status=status.HTTP_400_BAD_REQUEST)
        # validate stock
        insufficient = []
        # Use select_for_update on involved inventory rows to avoid race
        with transaction.atomic():
            # lock inventories
            for item in order.items.select_related('product').all():
                prod = item.product
                if prod is None:
                    insufficient.append({'product': None, 'message': 'Product no longer exists'})
                    continue
                inv, _ = models.Inventory.objects.select_for_update().get_or_create(product=prod)
                if item.quantity > inv.quantity:
                    insufficient.append({
                        'product': prod.sku,
                        'product_name': prod.name,
                        'available': inv.quantity,
                        'requested': item.quantity,
                        'message': f"Insufficient stock for {prod.name}. Available: {inv.quantity}, Requested: {item.quantity}"
                    })
            if insufficient:
                # if only one failing item, return a clear detail message
                detail_msg = insufficient[0]['message'] if len(insufficient) == 1 else 'Insufficient stock for one or more items'
                return Response({'detail': detail_msg, 'items': insufficient}, status=status.HTTP_400_BAD_REQUEST)
            # deduct
            for item in order.items.select_related('product').all():
                inv = models.Inventory.objects.select_for_update().get(product=item.product)
                inv.quantity = F('quantity') - item.quantity
                inv.save()
            order.status = models.Order.STATUS_CONFIRMED
            order.confirmed_at = timezone.now()
            order.save()
        return Response({'detail': 'Order confirmed'})

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        order = self.get_object()
        if order.status != models.Order.STATUS_CONFIRMED:
            return Response({'detail': 'Only Confirmed orders can be delivered'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = models.Order.STATUS_DELIVERED
        order.delivered_at = timezone.now()
        order.save()
        return Response({'detail': 'Order marked as delivered'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != models.Order.STATUS_DRAFT:
            return Response({'detail': 'Only Draft orders can be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = models.Order.STATUS_CANCELLED
        order.canceled_at = timezone.now()
        order.save()
        return Response({'detail': 'Order cancelled'})


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Inventory.objects.all().select_related('product')
    serializer_class = serializers.InventoryAdjustmentSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        # include the Inventory `id` so frontend can call detail endpoints like /inventory/{id}/adjust/
        data = [
            {'id': inv.id, 'product_id': inv.product.id, 'sku': inv.product.sku, 'quantity': inv.quantity}
            for inv in qs
        ]
        return Response(data)

    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
    def adjust(self, request, pk=None):
        inv = self.get_object()
        serializer = serializers.InventoryAdjustmentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # ensure product matches
        serializer.save(product=inv.product)
        return Response({'detail': 'Inventory adjusted'})