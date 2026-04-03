from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.orders.models import Category, Product
from apps.orders.serializers import OrderCreateSerializer


class OrderCreateSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Laptop', price=Decimal('1000.00'), category=self.category
        )

    def _data(self, **kwargs):
        return {
            'user_id': self.user.pk,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
            **kwargs,
        }

    def test_valid_data(self):
        serializer = OrderCreateSerializer(data=self._data())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_with_promocode(self):
        serializer = OrderCreateSerializer(data=self._data(promocode='SAVE10'))
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_promocode_defaults_to_none(self):
        serializer = OrderCreateSerializer(data=self._data())
        serializer.is_valid()
        self.assertIsNone(serializer.validated_data['promocode'])

    def test_invalid_user_id(self):
        serializer = OrderCreateSerializer(data=self._data(user_id=99999))
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)

    def test_invalid_product_id(self):
        data = self._data()
        data['items'] = [{'product_id': 99999, 'quantity': 1}]
        serializer = OrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_quantity_must_be_positive(self):
        data = self._data()
        data['items'] = [{'product_id': self.product.pk, 'quantity': 0}]
        serializer = OrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_empty_items(self):
        serializer = OrderCreateSerializer(data=self._data(items=[]))
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)

    def test_duplicate_products(self):
        data = self._data(items=[
            {'product_id': self.product.pk, 'quantity': 1},
            {'product_id': self.product.pk, 'quantity': 2},
        ])
        serializer = OrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)

    def test_missing_user_id(self):
        data = {'items': [{'product_id': self.product.pk, 'quantity': 1}]}
        serializer = OrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)

    def test_missing_items(self):
        data = {'user_id': self.user.pk}
        serializer = OrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)