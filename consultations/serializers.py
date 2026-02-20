from rest_framework import serializers
from django.utils   import timezone
from datetime       import time as dt_time
from .models        import ConsultationCategory, Appointment

# ─── Working Hours ────────────────────────────────────────────────────────────
WORKING_HOURS_START = dt_time(9, 0)   # 09:00 AM
WORKING_HOURS_END   = dt_time(18, 0)  # 06:00 PM


class ConsultationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ConsultationCategory
        fields = ('id', 'category', 'price_per_15min', 'description')


class AppointmentSerializer(serializers.ModelSerializer):
    """Used for listing / reading appointments."""
    category_name   = serializers.CharField(source='category.category', read_only=True)
    price_per_15min = serializers.DecimalField(
        source='category.price_per_15min', max_digits=10, decimal_places=2, read_only=True
    )
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model  = Appointment
        fields = (
            'id', 'category', 'category_name', 'price_per_15min',
            'date', 'time', 'duration', 'total_price',
            'is_paid', 'created_at',
        )
        read_only_fields = ('total_price', 'is_paid', 'created_at')


class CreateAppointmentSerializer(serializers.ModelSerializer):
    """Used for creating appointments (in cart flow)."""

    class Meta:
        model  = Appointment
        fields = ('category', 'date', 'time', 'duration')

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError(
                'Appointment date cannot be in the past.'
            )
        return value

    def validate_time(self, value):
        """
        Appointments are only allowed between 09:00 AM and 06:00 PM.
        The end time (06:00 PM) itself is rejected because there must be
        at least 15 minutes for the shortest session.
        """
        if not (WORKING_HOURS_START <= value < WORKING_HOURS_END):
            raise serializers.ValidationError(
                'Appointments are only available between '
                '9:00 AM and 6:00 PM. '
                f'You entered: {value.strftime("%I:%M %p")}.'
            )
        return value

    def validate_duration(self, value):
        valid = [15, 30, 60, 120]
        if value not in valid:
            raise serializers.ValidationError(
                f'Duration must be one of: {valid} minutes.'
            )
        return value

    def validate(self, data):
        # ── Check that appointment END time doesn't exceed working hours ──────
        appt_time     = data.get('time')
        appt_duration = data.get('duration')

        if appt_time and appt_duration:
            from datetime import datetime, timedelta
            appt_end = (
                datetime.combine(timezone.now().date(), appt_time)
                + timedelta(minutes=appt_duration)
            ).time()

            if appt_end > WORKING_HOURS_END:
                raise serializers.ValidationError(
                    f'The appointment would end at {appt_end.strftime("%I:%M %p")}, '
                    f'which is after working hours (6:00 PM). '
                    f'Please choose an earlier time or shorter duration.'
                )

        # ── Check slot availability ───────────────────────────────────────────
        qs = Appointment.objects.filter(
            category=data['category'],
            date=data['date'],
            time=data['time'],
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                'This time slot is already booked for the selected '
                'consultation type. Please choose a different time or date.'
            )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        return Appointment.objects.create(user=user, **validated_data)
