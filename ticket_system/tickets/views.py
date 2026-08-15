from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Ticket, TicketResponse
from .serializers import UserSerializer, TicketSerializer, TicketResponseSerializer

# ثبت‌نام
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user).data,
            "message": "ثبت‌نام با موفقیت انجام شد"
        }, status=status.HTTP_201_CREATED)


# تیکت‌ها
class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # کاربر عادی فقط تیکت‌های خودش را می‌بیند، ادمین همه را
        user = self.request.user
        if user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=user)

    def perform_create(self, serializer):
        # هنگام ساخت تیکت، کاربر فعلی را ثبت می‌کنیم
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        ticket = self.get_object()
        # فقط کاربر صاحب تیکت یا ادمین می‌توانند پاسخ دهند
        if request.user != ticket.user and not request.user.is_staff:
            return Response(
                {"detail": "شما مجاز به پاسخ دادن به این تیکت نیستید."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = TicketResponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(ticket=ticket, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)