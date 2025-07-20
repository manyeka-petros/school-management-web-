from rest_framework import serializers
from .models import (
    User, StudentProfile, TeacherProfile,
    ParentProfile, StaffProfile, HeadTeacherProfile
)
from academic.models import Classroom
from rest_framework.authtoken.models import Token


# ===========================
# USER SERIALIZER
# ===========================
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    user_type = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "full_name", "user_type", "is_active"
        ]


# ===========================
# BASE PROFILE SERIALIZER
# ===========================
class BaseProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        fields = "__all__"
        read_only_fields = ["user"]

    def create(self, validated_data):
        """
        Determine user to assign the profile to:
        1. Explicit user ID in initial_data
        2. 'student_user' injected via context
        3. request.user as fallback
        """
        user_id = self.initial_data.get("user")
        if user_id:
            try:
                validated_data["user"] = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with given ID does not exist.")

        elif self.context.get("student_user"):
            validated_data["user"] = self.context["student_user"]

        elif self.context.get("request") and not self.context["request"].user.is_anonymous:
            validated_data["user"] = self.context["request"].user

        else:
            raise serializers.ValidationError("User context or ID is required for profile creation.")

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Prevent changing the user once set
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


# ===========================
# STUDENT PROFILE SERIALIZER
# ===========================
class StudentProfileSerializer(BaseProfileSerializer):
    classroom = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(),
        required=False,
        allow_null=True,
    )
    classroom_name = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseProfileSerializer.Meta):
        model = StudentProfile
        fields = "__all__"

    def get_classroom_name(self, obj):
        if obj.classroom:
            section = obj.classroom.section if obj.classroom.section else ""
            return f"{obj.classroom.name} - {section} ({obj.classroom.academic_year})"
        return None


# ===========================
# OTHER PROFILE SERIALIZERS
# ===========================
class TeacherProfileSerializer(BaseProfileSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta(BaseProfileSerializer.Meta):
        model = TeacherProfile
        fields = "__all__"


class ParentProfileSerializer(BaseProfileSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta(BaseProfileSerializer.Meta):
        model = ParentProfile
        fields = "__all__"


class StaffProfileSerializer(BaseProfileSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta(BaseProfileSerializer.Meta):
        model = StaffProfile
        fields = "__all__"


class HeadTeacherProfileSerializer(BaseProfileSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta(BaseProfileSerializer.Meta):
        model = HeadTeacherProfile
        fields = "__all__"


# ===========================
# REGISTER SERIALIZER
# ===========================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "token"]

    def get_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
