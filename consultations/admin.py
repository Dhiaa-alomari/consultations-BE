from django.contrib import admin
from .models import ConsultationCategory, Appointment

# Register your models here.
@admin.register(ConsultationCategory)
class ConsultationCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'price_per_15min')
    search_fields = ('category',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'date', 'time', 'duration', 'total_price', 'is_paid')
    list_filter = ('is_paid', 'category', 'date')
    search_fields = ('user__username', 'category__category')
    readonly_fields = ('total_price',)
