from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Ticket, TicketResponse
from .serializers import UserSerializer, TicketSerializer, TicketResponseSerializer


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


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # کاربر عادی فقط تیکت‌های خودش، پشتیبان همه
        queryset = Ticket.objects.all() if user.is_staff else Ticket.objects.filter(user=user)

        # فیلتر بر اساس وضعیت (مثلاً ?status=open)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        ticket = self.get_object()
        # اجازه به صاحب تیکت یا هر پشتیبان
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
        # فقط پشتیبان‌ها مجازند
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