from rest_framework import serializers
from django.utils   import timezone
from .models        import Cart, CartItem, Order, OrderItem
from consultations.models import Appointment


class CartItemSerializer(serializers.ModelSerializer):
    category_name   = serializers.CharField(source='category.category',        read_only=True)
    price_per_15min = serializers.DecimalField(
        source='category.price_per_15min', max_digits=10, decimal_places=2, read_only=True
    )
    computed_price  = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = (
            'id', 'category', 'category_name', 'price_per_15min',
            'date', 'time', 'duration', 'computed_price', 'added_at',
        )
        read_only_fields = ('computed_price', 'added_at')

    def get_computed_price(self, obj):
        return str(obj.computed_price())


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model  = Cart
        fields = ('id', 'items', 'total', 'updated_at')

    def get_total(self, obj):
        return str(obj.total())


class AddToCartSerializer(serializers.ModelSerializer):
    """Validates item to add to cart."""

    class Meta:
        model  = CartItem
        fields = ('category', 'date', 'time', 'duration')

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError('Date cannot be in the past.')
        return value

    def validate_duration(self, value):
        if value not in [15, 30, 60, 120]:
            raise serializers.ValidationError('Duration must be 15, 30, 60, or 120 minutes.')
        return value

    def validate(self, data):
        # Prevent adding a slot already booked as a paid appointment
        if Appointment.objects.filter(
            category=data['category'],
            date=data['date'],
            time=data['time'],
            is_paid=True,
        ).exists():
            raise serializers.ValidationError(
                'This time slot is already booked. Please choose another time.'
            )
        return data


class UpdateCartItemSerializer(serializers.ModelSerializer):
    """Allows changing duration or category (type) of a cart item."""

    class Meta:
        model  = CartItem
        fields = ('duration', 'category', 'date', 'time')

    def validate_duration(self, value):
        if value not in [15, 30, 60, 120]:
            raise serializers.ValidationError('Duration must be 15, 30, 60, or 120 minutes.')
        return value

    def validate(self, data):
        instance = self.instance
        category = data.get('category', instance.category)
        date     = data.get('date',     instance.date)
        time     = data.get('time',     instance.time)

        if Appointment.objects.filter(
            category=category, date=date, time=time, is_paid=True,
        ).exclude(
            pk=getattr(instance, 'appointment_id', None)
        ).exists():
            raise serializers.ValidationError(
                'This time slot is already booked.'
            )
        return data


# ─── Order Serializers ────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = (
            'id', 'category_name', 'date', 'time',
            'duration', 'unit_price', 'total_price',
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = (
            'id', 'total_amount', 'status',
            'stripe_payment_intent_id', 'created_at', 'items',
        )
        read_only_fields = fields
