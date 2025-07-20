from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Attendance
from django.utils import timezone


class AttendanceSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    classroom_name = serializers.CharField(source='classroom.__str__', read_only=True)
    date = serializers.DateField(
        required=False,
        default=serializers.CreateOnlyDefault(timezone.now().date)
    )

    class Meta:
        model = Attendance
        fields = [
            'id',
            'user',
            'full_name',
            'user_type',
            'classroom',
            'classroom_name',
            'date',
            'status',
            'remarks'
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=Attendance.objects.all(),
                fields=['user', 'date'],
                message='Attendance for this user on this date already exists.'
            )
        ]
