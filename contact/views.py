from rest_framework              import generics, status
from rest_framework.permissions  import AllowAny, IsAdminUser
from rest_framework.response     import Response

from .models       import ContactMessage
from .serializers  import ContactMessageSerializer


class ContactCreateView(generics.CreateAPIView):
    """POST /api/contact/  — anyone can submit a message."""
    serializer_class   = ContactMessageSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {'message': 'Your message has been sent. We will get back to you shortly.'},
            status=status.HTTP_201_CREATED,
        )


class ContactListView(generics.ListAPIView):
    """GET /api/contact/messages/  — Admin only: view all messages."""
    queryset           = ContactMessage.objects.all()
    serializer_class   = ContactMessageSerializer
    permission_classes = [IsAdminUser]
