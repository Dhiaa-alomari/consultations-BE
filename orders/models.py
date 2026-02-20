from django.db   import models
from django.conf import settings
from decimal     import Decimal


class Cart(models.Model):
    """One cart per user (created automatically on first add)."""
    user       = models.OneToOneField(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.CASCADE,
                     related_name='cart',
                 )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total(self):
        """Sum of all item totals — always derived from server-side prices."""
        return sum(item.computed_price() for item in self.items.all())

    def __str__(self):
        return f'Cart({self.user.username})'


class CartItem(models.Model):
    """
    A pending (not-yet-paid) consultation booking in the cart.

    We store category + date + time + duration here (not a FK to Appointment)
    because the Appointment is only created after payment succeeds.
    The price is computed server-side on read — never stored in the cart row.
    """
    DURATION_CHOICES = [
        (15,  '15 minutes'),
        (30,  '30 minutes'),
        (60,  '1 hour'),
        (120, '2 hours'),
    ]

    cart       = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    category   = models.ForeignKey(
                     'consultations.ConsultationCategory',
                     on_delete=models.CASCADE,
                 )
    date       = models.DateField()
    time       = models.TimeField()
    duration   = models.IntegerField(choices=DURATION_CHOICES)
    added_at   = models.DateTimeField(auto_now_add=True)

    def computed_price(self):
        """
        Always read price_per_15min from the DB — the client can never
        supply or manipulate this value.
        """
        return (Decimal(self.category.price_per_15min) / Decimal(15)) * Decimal(self.duration)

    def __str__(self):
        return (
            f'{self.cart.user.username} → {self.category.category} '
            f'| {self.date} {self.time} | {self.duration}min'
        )


class Order(models.Model):
    """
    Created when the user initiates checkout.
    Linked to a Stripe PaymentIntent.
    Confirmed (status=paid) by the Stripe webhook.
    """
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('paid',      'Paid'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user             = models.ForeignKey(
                           settings.AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='orders',
                       )
    # Snapshot total — computed at order creation from CartItem prices
    total_amount     = models.DecimalField(max_digits=10, decimal_places=2)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order#{self.pk} | {self.user.username} | {self.status} | ${self.total_amount}'


class OrderItem(models.Model):
    """Snapshot of each cart item at the time of ordering."""
    DURATION_CHOICES = [
        (15,  '15 minutes'),
        (30,  '30 minutes'),
        (60,  '1 hour'),
        (120, '2 hours'),
    ]

    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    category    = models.ForeignKey(
                      'consultations.ConsultationCategory',
                      on_delete=models.SET_NULL,
                      null=True,
                  )
    category_name = models.CharField(max_length=60)   # Snapshot name
    date        = models.DateField()
    time        = models.TimeField()
    duration    = models.IntegerField(choices=DURATION_CHOICES)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)  # price_per_15min at order time
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # computed total

    # FK to the real Appointment (created after payment)
    appointment = models.OneToOneField(
                      'consultations.Appointment',
                      on_delete=models.SET_NULL,
                      null=True, blank=True,
                      related_name='order_item',
                  )

    def __str__(self):
        return f'OrderItem({self.order.pk} | {self.category_name} | {self.date} {self.time})'
