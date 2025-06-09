from rest_framework import serializers
from .models import User, StudentProfile, TeacherProfile, ParentProfile
from rest_framework.authtoken.models import Token

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'user_type', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ['user']

    def save(self, **kwargs):
        user = kwargs.pop('user', None)
        instance = super().save(**kwargs)
        if user and not getattr(instance, 'user_id', None):
            instance.user = user
            instance.save()
        return instance

class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = '__all__'
        read_only_fields = ['user']

    def save(self, **kwargs):
        user = kwargs.pop('user', None)
        instance = super().save(**kwargs)
        if user and not getattr(instance, 'user_id', None):
            instance.user = user
            instance.save()
        return instance

class ParentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentProfile
        fields = '__all__'
        read_only_fields = ['user']

    def save(self, **kwargs):
        user = kwargs.pop('user', None)
        instance = super().save(**kwargs)
        if user and not getattr(instance, 'user_id', None):
            instance.user = user
            instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    token = serializers.SerializerMethodField()

    gender = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    address = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'password',
            'user_type', 'token', 'gender', 'phone', 'address'
        ]

    def get_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key

    def create(self, validated_data):
        gender = validated_data.pop('gender', '')
        phone = validated_data.pop('phone', '')
        address = validated_data.pop('address', '')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            user_type=validated_data['user_type']
        )

        if user.user_type == 'student':
            StudentProfile.objects.create(user=user, address=address, guardian_phone=phone)
        elif user.user_type == 'teacher':
            TeacherProfile.objects.create(user=user, address=address, phone_number=phone, gender=gender)
        elif user.user_type == 'parent':
            ParentProfile.objects.create(user=user, address=address, phone_number=phone, gender=gender)

        return user
