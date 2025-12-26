from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F

from .models import Order, Inventory


@receiver(pre_delete, sender=Order)
def restore_stock_on_order_delete(sender, instance, **kwargs):
    """
    Restores stock for confirmed orders that are deleted.
    """
    if instance.status == Order.STATUS_CONFIRMED:
        with transaction.atomic():
            for item in instance.items.select_related('product').all():
                if item.product is None:
                    continue
                inv, _ = Inventory.objects.select_for_update().get_or_create(product=item.product)
                inv.quantity = F('quantity') + item.quantity
                inv.save()
