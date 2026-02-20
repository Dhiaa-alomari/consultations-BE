from django.db   import models
from django.conf import settings


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('general',       'General Inquiry'),
        ('billing',       'Billing & Payments'),
        ('technical',     'Technical Support'),
        ('legal',         'Legal Question'),
        ('complaint',     'Complaint'),
        ('other',         'Other'),
    ]

    # Sender info — optional FK if logged in
    user       = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.SET_NULL,
                     null=True, blank=True,
                     related_name='contact_messages',
                 )
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    subject    = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default='general')
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_subject_display()}] {self.name} — {self.email}'
