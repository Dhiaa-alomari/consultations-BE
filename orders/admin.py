from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

# Register your models here.
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('category_name', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'stripe_payment_intent_id')
    readonly_fields = ('total_amount', 'stripe_payment_intent_id')
    inlines = [OrderItemInline]