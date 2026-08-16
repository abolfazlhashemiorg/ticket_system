from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Ticket, TicketResponse


# ======================== سریالایزر کاربر ========================
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# ======================== سریالایزر پاسخ تیکت ========================
class TicketResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TicketResponse
        fields = ('id', 'ticket', 'user', 'text', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


# ======================== سریالایزر اصلی تیکت ========================
class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    responses = TicketResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = (
            'id',
            'user',
            'title',
            'description',
            'status',
            'priority',
            'created_at',
            'updated_at',
            'responses'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def update(self, instance, validated_data):
        """
        جلوگیری از تغییر وضعیت تیکت توسط کاربر عادی
        فقط کاربران با دسترسی staff (پشتیبان/ادمین) اجازه تغییر وضعیت دارند
        """
        request = self.context.get('request')

        # اگر کاربر درخواست تغییر وضعیت داده اما staff نیست → خطا
        if 'status' in validated_data and not (request and request.user.is_staff):
            raise serializers.ValidationError({
                "status": "تنها پشتیبان‌ها و ادمین‌ها می‌توانند وضعیت تیکت را تغییر دهند."
            })

        return super().update(instance, validated_data)