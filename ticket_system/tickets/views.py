from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Ticket, TicketResponse
from .serializers import UserSerializer, TicketSerializer, TicketResponseSerializer


# ======================== ثبت‌نام کاربر ========================
class UserViewSet(viewsets.ModelViewSet):
    """
    ویو مربوط به ثبت‌نام کاربر جدید
    دسترسی: همه (AllowAny)
    """
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


# ======================== مدیریت تیکت‌ها ========================
class TicketViewSet(viewsets.ModelViewSet):
    """
    ویو اصلی مدیریت تیکت‌ها با قابلیت‌های:
    - جستجو در عنوان و توضیحات (?search=...)
    - مرتب‌سازی بر اساس فیلدهای مختلف (?ordering=created_at یا -created_at)
    - فیلتر بر اساس وضعیت (?status=open)
    - دسترسی مبتنی بر نقش (کاربر عادی فقط تیکت‌های خود، پشتیبان همه)
    """
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    # تنظیمات جستجو و مرتب‌سازی
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']          # جستجو در عنوان و توضیحات
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']                        # مرتب‌سازی پیش‌فرض (جدیدترین اول)

    def get_queryset(self):
        """
        تعیین لیست تیکت‌ها بر اساس نقش کاربر:
        - کاربر عادی: فقط تیکت‌های خودش
        - پشتیبان/ادمین: همه‌ی تیکت‌ها
        همچنین فیلتر بر اساس وضعیت (status) از طریق پارامتر URL
        """
        user = self.request.user
        
        # تشخیص سطح دسترسی
        if user.is_staff:
            queryset = Ticket.objects.all()
        else:
            queryset = Ticket.objects.filter(user=user)

        # فیلتر دستی بر اساس وضعیت (علاوه بر جستجو و مرتب‌سازی)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    def perform_create(self, serializer):
        """
        هنگام ایجاد تیکت جدید، کاربر فعلی را به عنوان صاحب تیکت ثبت می‌کند
        """
        serializer.save(user=self.request.user)

    # ======================== اکشن: پاسخ به تیکت ========================
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        اضافه کردن پاسخ به یک تیکت خاص
        دسترسی: صاحب تیکت یا هر کاربر پشتیبان/ادمین
        """
        ticket = self.get_object()
        
        # بررسی دسترسی
        if request.user != ticket.user and not request.user.is_staff:
            return Response(
                {"detail": "شما مجاز به پاسخ دادن به این تیکت نیستید."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # اعتبارسنجی و ذخیره‌سازی پاسخ
        serializer = TicketResponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(ticket=ticket, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ======================== اکشن: تغییر وضعیت تیکت ========================
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):"""
        تغییر وضعیت تیکت (open, in_progress, closed)
        دسترسی: فقط پشتیبان‌ها و ادمین‌ها (is_staff=True)
        """
        ticket = self.get_object()
        
        # بررسی دسترسی (فقط staff)
        if not request.user.is_staff:
            return Response(
                {"detail": "تنها پشتیبان‌ها و ادمین‌ها می‌توانند وضعیت تیکت را تغییر دهند."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت وضعیت جدید از درخواست
        new_status = request.data.get('status')
        
        # اعتبارسنجی وضعیت جدید
        valid_statuses = dict(Ticket.STATUS_CHOICES)  # {'open': 'باز', 'in_progress': 'در حال بررسی', 'closed': 'بسته شده'}
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"وضعیت نامعتبر است. گزینه‌های مجاز: {', '.join(valid_statuses.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تغییر وضعیت و ذخیره‌سازی
        ticket.status = new_status
        ticket.save()
        
        # بازگشت اطلاعات به‌روز شده
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)