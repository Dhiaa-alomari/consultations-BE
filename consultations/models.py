from django.db   import models
from django.conf import settings
from decimal     import Decimal


class ConsultationCategory(models.Model):
    CATEGORY_CHOICES = [
        ('Felonies',              'Felonies'),
        ('Misdemeanors',          'Misdemeanors'),
        ('Immigration',           'Immigration'),
        ('Property Management',   'Property Management'),
        ('Family Law',            'Family Law'),
        ('Commercial Law',        'Commercial Law'),
        ('Labor Law',             'Labor Law'),
        ('Tax Consulting',        'Tax Consulting'),
        ('Contracts',             'Contracts'),
        ('Intellectual Property', 'Intellectual Property'),
    ]

    category         = models.CharField(max_length=60, choices=CATEGORY_CHOICES, unique=True)
    price_per_15min  = models.DecimalField(max_digits=10, decimal_places=2)
    description      = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Consultation Categories'
        ordering = ['category']

    def __str__(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)


class Appointment(models.Model):
    """
    One row = one booked consultation slot.

    Uniqueness rule: (category, date, time) — same category cannot be
    double-booked at the same date+time.  Different categories at the same
    slot are fine.

    Price is calculated server-side and stored; the frontend can never tamper
    with it because we recompute on every save().
    """
    DURATION_CHOICES = [
        (15,  '15 minutes'),
        (30,  '30 minutes'),
        (60,  '1 hour'),
        (120, '2 hours'),
    ]

    user        = models.ForeignKey(
                      settings.AUTH_USER_MODEL,
                      on_delete=models.CASCADE,
                      related_name='appointments',
                  )
    category    = models.ForeignKey(
                      ConsultationCategory,
                      on_delete=models.CASCADE,
                      related_name='appointments',
                  )
    date        = models.DateField()
    time        = models.TimeField()
    duration    = models.IntegerField(choices=DURATION_CHOICES)

    # Computed & stored server-side — never editable via API
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    # Set to True only after Stripe payment succeeds (webhook)
    is_paid     = models.BooleanField(default=False)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('category', 'date', 'time')
        ordering = ['-date', '-time']

    def compute_price(self):
        """
        Price = (price_per_15min / 15) * duration_in_minutes
        Always computed from the DB-stored price_per_15min, never from
        user-supplied data.
        """
        return (Decimal(self.category.price_per_15min) / Decimal(15)) * Decimal(self.duration)

    def save(self, *args, **kwargs):
        # Recompute on every save — prevents any tampering
        self.total_price = self.compute_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.user.username} | {self.category.category} | '
            f'{self.date} {self.time} | {self.duration}min | '
            f'{"Paid" if self.is_paid else "Unpaid"}'
        )
