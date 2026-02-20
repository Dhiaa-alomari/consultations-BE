from rest_framework              import generics, status
from rest_framework.views        import APIView
from rest_framework.response     import Response
from rest_framework.permissions  import IsAuthenticated, IsAdminUser, AllowAny

from .models       import ConsultationCategory, Appointment
from .serializers  import (
    ConsultationCategorySerializer,
    AppointmentSerializer,
    CreateAppointmentSerializer,
)


# ─── Categories (public) ──────────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    """GET /api/consultations/categories/  — Public"""
    queryset           = ConsultationCategory.objects.all()
    serializer_class   = ConsultationCategorySerializer
    permission_classes = [AllowAny]


# Admin-only CRUD for categories
class CategoryAdminCreateView(generics.CreateAPIView):
    """POST /api/consultations/categories/create/  — Admin only"""
    queryset           = ConsultationCategory.objects.all()
    serializer_class   = ConsultationCategorySerializer
    permission_classes = [IsAdminUser]


class CategoryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/consultations/categories/<pk>/  — Admin only"""
    queryset           = ConsultationCategory.objects.all()
    serializer_class   = ConsultationCategorySerializer
    permission_classes = [IsAdminUser]


# ─── Appointment History (per user) ──────────────────────────────────────────

class AppointmentHistoryView(generics.ListAPIView):
    """
    GET /api/consultations/my-appointments/
    Returns ONLY the authenticated user's appointments.
    """
    serializer_class   = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own appointments
        return Appointment.objects.filter(
            user=self.request.user
        ).select_related('category').order_by('-date', '-time')


# ─── Appointment Create (adds to cart flow) ──────────────────────────────────

class AppointmentCreateView(generics.CreateAPIView):
    """
    POST /api/consultations/appointments/
    Creates appointment directly — only after payment is confirmed.
    Used internally by the Stripe webhook (and for testing via Postman).
    Requires authentication.
    """
    serializer_class   = CreateAppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )


class AppointmentDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/consultations/appointments/<pk>/  — view single appointment
    DELETE /api/consultations/appointments/<pk>/  — cancel appointment (owner only)
    """
    serializer_class   = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only access their own appointments
        return Appointment.objects.filter(
            user=self.request.user
        ).select_related('category')

    def destroy(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.is_paid:
            return Response(
                {'error': 'Paid appointments cannot be cancelled directly. '
                          'Please contact support.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.delete()
        return Response(
            {'message': 'Appointment cancelled successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ─── Calendar availability ───────────────────────────────────────────────────

class SlotAvailabilityView(APIView):
    """
    GET /api/consultations/availability/?category=<id>&date=<YYYY-MM-DD>
    Returns booked times for a category on a given date.
    Anyone (even unauthenticated) can query availability.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        category_id = request.query_params.get('category')
        date        = request.query_params.get('date')

        if not category_id or not date:
            return Response(
                {'error': 'Both category and date query params are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booked = Appointment.objects.filter(
            category_id=category_id,
            date=date,
        ).values_list('time', flat=True)

        return Response({'booked_times': list(booked)})
