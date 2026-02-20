from django.urls import path
from .views import (
    CategoryListView,
    CategoryAdminCreateView,
    CategoryAdminDetailView,
    AppointmentHistoryView,
    AppointmentCreateView,
    AppointmentDetailView,
    SlotAvailabilityView,
)

urlpatterns = [
    # Public
    path('categories/',            CategoryListView.as_view(),        name='category_list'),
    path('availability/',          SlotAvailabilityView.as_view(),    name='slot_availability'),

    # Auth-required
    path('appointments/',          AppointmentCreateView.as_view(),   name='appointment_create'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(),   name='appointment_detail'),
    path('my-appointments/',       AppointmentHistoryView.as_view(),  name='my_appointments'),

    # Admin-only
    path('categories/create/',     CategoryAdminCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/',   CategoryAdminDetailView.as_view(), name='category_detail'),
]
