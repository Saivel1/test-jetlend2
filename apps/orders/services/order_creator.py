import logging
from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderItem, Promocode, PromocodeUsage

logger = logging.getLogger(__name__)


class PromocodeError(Exception):
    """Raised when a promocode cannot be applied."""


@dataclass
class OrderItemData:
    product_id: int
    quantity: int


def create_order(
    *,
    user: User,
    items: list[OrderItemData],
    promocode_code: str | None = None,
) -> Order:
    """
    Create an order with optional promocode discount.

    Args:
        user: The user placing the order.
        items: List of products and quantities.
        promocode_code: Optional promocode code string.

    Returns:
        Created Order instance.

    Raises:
        PromocodeError: If the promocode is invalid or cannot be applied.
    """
    from apps.orders.models import Product  # avoid circular import

    product_ids = [item.product_id for item in items]
    products = {p.pk: p for p in Product.objects.select_related('category').filter(pk__in=product_ids)}

    promocode = None
    if promocode_code:
        promocode = _validate_promocode(promocode_code, user)

    total_price, discounted_price = _calculate_prices(items, products, promocode)

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            promocode=promocode,
            total_price=total_price,
            discounted_price=discounted_price,
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=products[item.product_id],
                quantity=item.quantity,
                price=products[item.product_id].price,
            )
            for item in items
        ])

        if promocode:
            PromocodeUsage.objects.create(promocode=promocode, user=user)
            logger.info('Promocode %s applied to order #%d', promocode.code, order.pk)

    logger.info('Order #%d created for user %d, total=%s discounted=%s', order.pk, user.pk, total_price, discounted_price)
    return order


def _validate_promocode(code: str, user: User) -> Promocode:
    """Fetch and validate a promocode against all business rules."""
    try:
        promocode = Promocode.objects.select_related('category').get(code=code)
    except Promocode.DoesNotExist:
        raise PromocodeError(f'Promocode {code!r} does not exist.')

    if promocode.expires_at < timezone.now():
        raise PromocodeError(f'Promocode {code!r} has expired.')

    if PromocodeUsage.objects.filter(promocode=promocode).count() >= promocode.max_usages:
        raise PromocodeError(f'Promocode {code!r} has reached its usage limit.')

    if PromocodeUsage.objects.filter(promocode=promocode, user=user).exists():
        raise PromocodeError(f'Promocode {code!r} has already been used by this user.')

    return promocode


def _calculate_prices(
    items: list[OrderItemData],
    products: dict,
    promocode: Promocode | None,
) -> tuple[Decimal, Decimal]:
    """
    Calculate total and discounted prices.

    Discount applies only to eligible products:
    - product.is_promo_excluded=False
    - if promocode has a category restriction, product must be in that category
    """
    total_price = Decimal('0')
    discounted_price = Decimal('0')

    for item in items:
        product = products[item.product_id]
        line_total = product.price * item.quantity
        total_price += line_total

        if promocode and _is_eligible(product, promocode):
            discount = line_total * (promocode.discount_percent / Decimal('100'))
            discounted_price += line_total - discount
        else:
            discounted_price += line_total

    return total_price, discounted_price


def _is_eligible(product, promocode: Promocode) -> bool:
    """Check whether a product is eligible for the promocode discount."""
    if product.is_promo_excluded:
        return False
    if promocode.category and product.category_id != promocode.category_id: #type: ignore
        return False
    return True