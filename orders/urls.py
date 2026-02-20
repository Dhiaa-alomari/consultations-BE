from django.urls import path
from .views import (
    CartView,
    CartItemView,
    ClearCartView,
    CreateCheckoutSessionView,
    StripeWebhookView,
    OrderListView,
    OrderDetailView,
)

urlpatterns = [
    # Cart
    path('cart/',               CartView.as_view(),             name='cart'),
    path('cart/items/<int:pk>/',CartItemView.as_view(),         name='cart_item'),
    path('cart/clear/',         ClearCartView.as_view(),        name='cart_clear'),

    # Checkout
    path('checkout/',           CreateCheckoutSessionView.as_view(), name='checkout'),

    # Stripe webhook (Stripe POSTs here after payment)
    path('webhook/',            StripeWebhookView.as_view(),    name='stripe_webhook'),

    # Order history
    path('',                    OrderListView.as_view(),        name='order_list'),
    path('<int:pk>/',           OrderDetailView.as_view(),      name='order_detail'),
]
