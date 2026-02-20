from django.urls import path
from .views import ContactCreateView, ContactListView

urlpatterns = [
    path('',          ContactCreateView.as_view(), name='contact_create'),
    path('messages/', ContactListView.as_view(),   name='contact_messages'),
]
