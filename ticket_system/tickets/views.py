from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from .models import Ticket, TicketResponse
from .serializers import UserSerializer, TicketSerializer, TicketResponseSerializer


# ======================== ثبت‌نام (عمومی) ========================
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    ثبت‌نام کاربر جدید – دسترسی عمومی
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "user": UserSerializer(user).data,
            "message": "ثبت‌نام با موفقیت انجام شد"
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================== مدیریت کاربران (فقط ادمین) ========================
class UserViewSet(viewsets.ModelViewSet):
    """
    مدیریت کاربران– فقط ادمین (is_superuser) دسترسی دارد
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]  # فقط ادمین


# ======================== مدیریت تیکت‌ها ========================
class TicketViewSet(viewsets.ModelViewSet):
    """
    مدیریت تیکت‌ها – کاربران عادی فقط تیکت‌های خود را می‌بینند
    """
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.all() if user.is_staff else Ticket.objects.filter(user=user)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        ticket = self.get_object()
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

    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        if not request.user.is_staff:
            return Response(
                {"detail": "تنها پشتیبان‌ها و ادمین‌ها می‌توانند وضعیت را تغییر دهند."},
                status=status.HTTP_403_FORBIDDEN
            )
        new_status = request.data.get('status')
        valid_statuses = dict(Ticket.STATUS_CHOICES)
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"وضعیت نامعتبر است. گزینه‌های مجاز: {', '.join(valid_statuses.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        ticket.status = new_status
        ticket.save()
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)