from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Ticket, TicketResponse

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class TicketResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TicketResponse
        fields = ('id', 'ticket', 'user', 'text', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    responses = TicketResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ('id', 'user', 'title', 'description', 'status', 'priority', 'created_at', 'updated_at', 'responses')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def create(self, validated_data):
        # کاربر از درخواست گرفته می‌شود
        return Ticket.objects.create(**validated_data)