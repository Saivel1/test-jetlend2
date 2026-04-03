import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.serializers import OrderCreateSerializer, OrderOutputSerializer
from apps.orders.services.order_creator import (
    OrderItemData,
    PromocodeError,
    create_order,
)

logger = logging.getLogger(__name__)


class OrderCreateView(APIView):
    """POST /orders/ — create a new order with optional promocode."""

    def post(self, request: Request) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.get(pk=data['user_id'])

        items = [OrderItemData(product_id=i['product_id'], quantity=i['quantity']) for i in data['items']]

        try:
            order = create_order(
                user=user,
                items=items,
                promocode_code=data.get('promocode'),
            )
        except PromocodeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderOutputSerializer(order).data, status=status.HTTP_201_CREATED)