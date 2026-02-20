"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Auth & Users ───────────────────────────────
    path('api/auth/', include('users.urls')),

    # ── Consultations ──────────────────────────────
    path('api/consultations/', include('consultations.urls')),

    # ── Orders / Cart / Stripe ─────────────────────
    path('api/orders/', include('orders.urls')),

    # ── Contact ────────────────────────────────────
    path('api/contact/', include('contact.urls')),
]


'''
from consultations.models import Appointment, ConsultationCategory
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
category = ConsultationCategory.objects.get(category='Felonies')

Appointment.objects.create(
    user=user,
    category=category,
    date='2026-03-08',
    time='13:30:00',
    duration=30,
    is_paid=True
)
print("Appointment created!")
exit()

'''