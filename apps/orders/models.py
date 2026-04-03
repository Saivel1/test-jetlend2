from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    is_promo_excluded = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self) -> str:
        return self.name


class Promocode(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    expires_at = models.DateTimeField()
    max_usages = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='promocodes',
        null=True,
        blank=True,
    )
    used_by = models.ManyToManyField(
        User,
        through='PromocodeUsage',
        related_name='promocodes',
        blank=True,
    )

    class Meta:
        verbose_name = 'Promocode'
        verbose_name_plural = 'Promocodes'

    def __str__(self) -> str:
        return self.code


class PromocodeUsage(models.Model):
    promocode = models.ForeignKey(Promocode, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promocode_usages')
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('promocode', 'user')
        verbose_name = 'Promocode Usage'
        verbose_name_plural = 'Promocode Usages'

    def __str__(self) -> str:
        return f'{self.user} — {self.promocode}'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    promocode = models.ForeignKey(
        Promocode,
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True,
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self) -> str:
        return f'Order #{self.pk} — {self.user}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot цены на момент заказа

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self) -> str:
        return f'{self.product} x{self.quantity}'