from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.orders.models import Category, Product, Promocode, PromocodeUsage


class OrderCreateViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Laptop', price=Decimal('1000.00'), category=self.category
        )
        self.url = reverse('order-create')

    def _payload(self, **kwargs):
        return {
            'user_id': self.user.pk,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
            **kwargs,
        }

    def test_create_order_without_promocode(self):
        response = self.client.post(self.url, self._payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_price'], '1000.00')
        self.assertEqual(response.data['discounted_price'], '1000.00')

    def test_create_order_with_valid_promocode(self):
        promo = Promocode.objects.create(
            code='SAVE10',
            discount_percent=Decimal('10'),
            expires_at=timezone.now() + timedelta(days=1),
            max_usages=5,
        )
        response = self.client.post(self.url, self._payload(promocode=promo.code), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_price'], '1000.00')
        self.assertEqual(response.data['discounted_price'], '900.00')

    def test_nonexistent_promocode(self):
        response = self.client.post(self.url, self._payload(promocode='FAKE'), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_promocode(self):
        promo = Promocode.objects.create(
            code='EXPIRED',
            discount_percent=Decimal('10'),
            expires_at=timezone.now() - timedelta(days=1),
            max_usages=5,
        )
        response = self.client.post(self.url, self._payload(promocode=promo.code), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exceeded_max_usages(self):
        other_user = User.objects.create_user(username='other', password='pass')
        promo = Promocode.objects.create(
            code='MAXED',
            discount_percent=Decimal('10'),
            expires_at=timezone.now() + timedelta(days=1),
            max_usages=1,
        )
        PromocodeUsage.objects.create(promocode=promo, user=other_user)

        response = self.client.post(self.url, self._payload(promocode=promo.code), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_promocode_already_used_by_user(self):
        promo = Promocode.objects.create(
            code='USED',
            discount_percent=Decimal('10'),
            expires_at=timezone.now() + timedelta(days=1),
            max_usages=10,
        )
        PromocodeUsage.objects.create(promocode=promo, user=self.user)

        response = self.client.post(self.url, self._payload(promocode=promo.code), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_promocode_wrong_category(self):
        other_category = Category.objects.create(name='Books')
        promo = Promocode.objects.create(
            code='BOOKS10',
            discount_percent=Decimal('10'),
            expires_at=timezone.now() + timedelta(days=1),
            max_usages=5,
            category=other_category,
        )
        response = self.client.post(self.url, self._payload(promocode=promo.code), format='json')

        # промокод применится, но скидки не будет — товар не той категории
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['discounted_price'], '1000.00')

    def test_promocode_correct_category(self):
        promo = Promocode.objects.create(
            code='ELEC10',
            discount_percent=Decimal('10'),
            expires_at=timezone.now() + timedelta(days=1),
            max_usages=5,
            category=self.category,
        )
        response = self.client.post(self.url, self._payload(promocode=promo.code), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['discounted_price'], '900.00')

    def test_promo_excluded_product(self):
        excluded = Product.objects.create(
            name='Excluded', price=Decimal('500.00'),
            category=self.category, is_promo_excluded=True,
        )
        promo = Promocode.objects.create(
            code='SAVE20',
            discount_percent=Decimal('20'),
            expires_at=timezone.now() + timedelta(days=1),
            max_usages=5,
        )
        payload = {
            'user_id': self.user.pk,
            'items': [{'product_id': excluded.pk, 'quantity': 1}],
            'promocode': promo.code,
        }
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['discounted_price'], '500.00')

    def test_invalid_user(self):
        payload = self._payload()
        payload['user_id'] = 99999
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_product(self):
        payload = {'user_id': self.user.pk, 'items': [{'product_id': 99999, 'quantity': 1}]}
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_products_in_order(self):
        payload = {
            'user_id': self.user.pk,
            'items': [
                {'product_id': self.product.pk, 'quantity': 1},
                {'product_id': self.product.pk, 'quantity': 2},
            ],
        }
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_items(self):
        payload = {'user_id': self.user.pk, 'items': []}
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)