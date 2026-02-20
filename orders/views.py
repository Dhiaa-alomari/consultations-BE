import stripe
from decimal import Decimal

from django.conf             import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator

from rest_framework              import status, generics
from rest_framework.views        import APIView
from rest_framework.response     import Response
from rest_framework.permissions  import IsAuthenticated

from .models       import Cart, CartItem, Order, OrderItem
from .serializers  import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    OrderSerializer,
)
from consultations.models      import Appointment, ConsultationCategory
from consultations.serializers import CreateAppointmentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


# ─── Cart Views ───────────────────────────────────────────────────────────────

class CartView(APIView):
    """
    GET  /api/orders/cart/     — view current cart
    POST /api/orders/cart/     — add item to cart
    """
    permission_classes = [IsAuthenticated]

    def _get_or_create_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def get(self, request):
        cart = self._get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self._get_or_create_cart(request.user)
        item = CartItem.objects.create(cart=cart, **serializer.validated_data)

        return Response(
            {'message': 'Item added to cart.', 'cart': CartSerializer(cart).data},
            status=status.HTTP_201_CREATED,
        )


class CartItemView(APIView):
    """
    PATCH  /api/orders/cart/items/<pk>/   — update duration or category
    DELETE /api/orders/cart/items/<pk>/   — remove item
    """
    permission_classes = [IsAuthenticated]

    def _get_item(self, pk, user):
        try:
            return CartItem.objects.get(pk=pk, cart__user=user)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, pk):
        item = self._get_item(pk, request.user)
        if not item:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        cart = item.cart
        return Response(
            {'message': 'Cart item updated.', 'cart': CartSerializer(cart).data}
        )

    def delete(self, request, pk):
        item = self._get_item(pk, request.user)
        if not item:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart = item.cart
        item.delete()
        return Response(
            {'message': 'Item removed from cart.', 'cart': CartSerializer(cart).data}
        )


class ClearCartView(APIView):
    """DELETE /api/orders/cart/clear/ — empty the whole cart."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            request.user.cart.items.all().delete()
            return Response({'message': 'Cart cleared.'})
        except Cart.DoesNotExist:
            return Response({'message': 'Cart is already empty.'})


# ─── Stripe Checkout ──────────────────────────────────────────────────────────

class CreateCheckoutSessionView(APIView):
    """
    POST /api/orders/checkout/
    Validates cart, creates an Order (status=pending), creates a Stripe
    PaymentIntent and returns the client_secret to the frontend.
    The total is always computed server-side — never taken from the request.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        items = cart.items.select_related('category').all()
        if not items.exists():
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Server-side total (tamper-proof) ─────────────────────────────────
        total = cart.total()
        if total <= 0:
            return Response({'error': 'Invalid cart total.'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Create Order ─────────────────────────────────────────────────────
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            status='pending',
        )

        for item in items:
            computed = item.computed_price()
            OrderItem.objects.create(
                order=order,
                category=item.category,
                category_name=item.category.category,
                date=item.date,
                time=item.time,
                duration=item.duration,
                unit_price=item.category.price_per_15min,
                total_price=computed,
            )

        # ── Stripe PaymentIntent (amount in cents) ────────────────────────────
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),     # Stripe uses smallest currency unit
                currency='usd',
                metadata={
                    'order_id': str(order.pk),
                    'user_id':  str(request.user.pk),
                },
            )
        except stripe.error.StripeError as e:
            order.delete()
            return Response(
                {'error': f'Stripe error: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        order.stripe_payment_intent_id = intent.id
        order.save()

        return Response({
            'client_secret':      intent.client_secret,
            'order_id':           order.pk,
            'total_amount':       str(total),
            'stripe_public_key':  settings.STRIPE_PUBLISHABLE_KEY,
        })


# ─── Stripe Webhook ───────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    POST /api/orders/webhook/
    Receives Stripe events.  On payment_intent.succeeded:
      1. Marks Order as paid
      2. Creates Appointment rows for each OrderItem
      3. Clears the user's cart
    """
    permission_classes = []   # Stripe calls this unauthenticated
    authentication_classes = []

    def post(self, request):
        payload    = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({'error': 'Invalid webhook signature.'}, status=400)

        if event['type'] == 'payment_intent.succeeded':
            intent   = event['data']['object']
            order_id = intent.get('metadata', {}).get('order_id')

            try:
                order = Order.objects.get(pk=order_id, status='pending')
            except Order.DoesNotExist:
                return Response({'error': 'Order not found.'}, status=404)

            # ── Confirm Order ─────────────────────────────────────────────────
            order.status = 'paid'
            order.save()

            # ── Create Appointments ───────────────────────────────────────────
            for oi in order.items.select_related('category').all():
                # Only create if slot is still free (guard against race conditions)
                appt, created = Appointment.objects.get_or_create(
                    category=oi.category,
                    date=oi.date,
                    time=oi.time,
                    defaults={
                        'user':     order.user,
                        'duration': oi.duration,
                        'is_paid':  True,
                    }
                )
                if created:
                    oi.appointment = appt
                    oi.save()
                else:
                    # Slot was grabbed between cart-add and payment — rare edge case
                    # Mark order item but don't block the webhook response
                    pass

            # ── Clear Cart ────────────────────────────────────────────────────
            try:
                order.user.cart.items.all().delete()
            except Cart.DoesNotExist:
                pass

        elif event['type'] == 'payment_intent.payment_failed':
            intent   = event['data']['object']
            order_id = intent.get('metadata', {}).get('order_id')
            Order.objects.filter(pk=order_id, status='pending').update(status='failed')

        return Response({'status': 'ok'})


# ─── Order History ────────────────────────────────────────────────────────────

class OrderListView(generics.ListAPIView):
    """GET /api/orders/  — list current user's orders (newest first)."""
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items').order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/<pk>/  — detail of a single order owned by this user."""
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
