from django.contrib.auth.models import User
from rest_framework import serializers

from apps.orders.models import Order, OrderItem, Product


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value: int) -> int:
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f'Product {value} does not exist.')
        return value


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True, min_length=1)
    promocode = serializers.CharField(required=False, allow_null=True, default=None)

    def validate_user_id(self, value: int) -> int:
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f'User {value} does not exist.')
        return value

    def validate_items(self, value: list) -> list:
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('Duplicate products in order.')
        return value


class OrderItemOutputSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.pk')
    product_name = serializers.CharField(source='product.name')

    class Meta:
        model = OrderItem
        fields = ('product_id', 'product_name', 'quantity', 'price')


class OrderOutputSerializer(serializers.ModelSerializer):
    items = OrderItemOutputSerializer(many=True)
    promocode = serializers.CharField(source='promocode.code', allow_null=True)

    class Meta:
        model = Order
        fields = ('id', 'user_id', 'promocode', 'total_price', 'discounted_price', 'created_at', 'items')