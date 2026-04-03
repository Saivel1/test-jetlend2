from django.contrib import admin

from .models import Category, Order, OrderItem, Product, Promocode, PromocodeUsage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'is_promo_excluded')
    list_filter = ('category', 'is_promo_excluded')
    search_fields = ('name',)


@admin.register(Promocode)
class PromocodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'discount_percent', 'expires_at', 'max_usages', 'category')
    list_filter = ('category',)
    search_fields = ('code',)


@admin.register(PromocodeUsage)
class PromocodeUsageAdmin(admin.ModelAdmin):
    list_display = ('id', 'promocode', 'user', 'used_at')
    list_filter = ('promocode',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'promocode', 'total_price', 'discounted_price', 'created_at')
    list_filter = ('promocode',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    inlines = (OrderItemInline,)