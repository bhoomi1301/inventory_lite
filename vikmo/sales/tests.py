from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from . import models


class OrderFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.prod = models.Product.objects.create(name='Brake Pad', sku='BP-001', price='500.00')
        models.Inventory.objects.create(product=self.prod, quantity=100)
        self.dealer = models.Dealer.objects.create(name='ABC Motors', code='ABC')

    def test_successful_order_flow(self):
        # create draft order
        payload = {
            'dealer': self.dealer.id,
            'items': [{'product': self.prod.id, 'quantity': 10}]
        }
        resp = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        order_id = resp.data['id']
        # confirm
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 200)
        # inventory should be 90
        inv = models.Inventory.objects.get(product=self.prod)
        self.assertEqual(inv.quantity, 90)
        # deliver
        resp = self.client.post(f'/api/orders/{order_id}/deliver/')
        self.assertEqual(resp.status_code, 200)

    def test_insufficient_stock(self):
        # set stock to 5
        inv = models.Inventory.objects.get(product=self.prod)
        inv.quantity = 5
        inv.save()
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 10}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        order_id = resp.data['id']
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('items', resp.data)
        # message should be clear
        expected = f"Insufficient stock for {self.prod.name}. Available: 5, Requested: 10"
        self.assertEqual(resp.data['items'][0]['message'], expected)
        # detail may contain the same message for single-item failures
        self.assertIn('Insufficient stock', resp.data['detail'])

    def test_cannot_edit_confirmed_order(self):
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 1}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        order_id = resp.data['id']
        # confirm
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 200)
        # attempt to update
        update_payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 2}]}
        resp = self.client.put(f'/api/orders/{order_id}/', update_payload, format='json')
        self.assertEqual(resp.status_code, 400)
        # Clear and helpful message
        self.assertEqual(resp.data.get('detail'), 'Only Draft orders can be edited')

    def test_cannot_change_delivered_back_to_draft(self):
        # create order
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 1}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        order_id = resp.data['id']
        # confirm and deliver
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(f'/api/orders/{order_id}/deliver/')
        self.assertEqual(resp.status_code, 200)
        # attempt to set status back to DRAFT via update
        update_payload = {'status': 'DRAFT', 'items': [{'product': self.prod.id, 'quantity': 1}]}
        resp = self.client.put(f'/api/orders/{order_id}/', update_payload, format='json')
        self.assertEqual(resp.status_code, 400)
        # expect clear message about status changes
        self.assertEqual(resp.data.get('detail'), 'Order status cannot be changed via update; use confirm or deliver endpoints')

    def test_delete_confirmed_restores_stock(self):
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 10}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        order_id = resp.data['id']
        # confirm
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 200)
        inv = models.Inventory.objects.get(product=self.prod)
        self.assertEqual(inv.quantity, 90)
        # delete order
        resp = self.client.delete(f'/api/orders/{order_id}/')
        self.assertIn(resp.status_code, (204, 200))
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 100)

    def test_cancel_draft_order(self):
        # set stock to 20 so cancel is not related to stock
        inv = models.Inventory.objects.get(product=self.prod)
        inv.quantity = 20
        inv.save()
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 5}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        order_id = resp.data['id']
        # cancel
        resp = self.client.post(f'/api/orders/{order_id}/cancel/')
        self.assertEqual(resp.status_code, 200)
        # order status should be cancelled
        order = models.Order.objects.get(pk=order_id)
        self.assertEqual(order.status, models.Order.STATUS_CANCELLED)
        # inventory remains unchanged
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 20)

    def test_cannot_cancel_confirmed_order(self):
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 1}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        order_id = resp.data['id']
        # confirm
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 200)
        # attempt to cancel
        resp = self.client.post(f'/api/orders/{order_id}/cancel/')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data.get('detail'), 'Only Draft orders can be cancelled')

    def test_invalid_status_transition(self):
        payload = {'dealer': self.dealer.id, 'items': [{'product': self.prod.id, 'quantity': 5}]}
        resp = self.client.post('/api/orders/', payload, format='json')
        order_id = resp.data['id']
        # confirm and deliver
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(f'/api/orders/{order_id}/deliver/')
        self.assertEqual(resp.status_code, 200)
        # attempt to confirm again
        resp = self.client.post(f'/api/orders/{order_id}/confirm/')
        self.assertEqual(resp.status_code, 400)

    def test_inventory_adjust_permissions_and_audit(self):
        from django.contrib.auth.models import User
        inv = models.Inventory.objects.get(product=self.prod)
        # non-admin cannot list or adjust
        user = User.objects.create_user('user1', 'u1@example.com', 'pass')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/inventory/')
        self.assertEqual(resp.status_code, 403)
        resp = self.client.put(f'/api/inventory/{inv.id}/adjust/', {'change': -10, 'note': 'unauthorized'}, format='json')
        self.assertEqual(resp.status_code, 403)
        # admin can adjust and audit is recorded
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.client.force_authenticate(user=admin)
        resp = self.client.put(f'/api/inventory/{inv.id}/adjust/', {'change': -10, 'note': 'stock correction'}, format='json')
        self.assertEqual(resp.status_code, 200)
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 90)
        # check adjustment record
        adj = models.InventoryAdjustment.objects.filter(product=self.prod).order_by('-created_at').first()
        self.assertIsNotNone(adj)
        self.assertEqual(adj.change, -10)
        self.assertEqual(adj.changed_by.username, 'admin')
