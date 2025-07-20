from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from .models import (
    User, StudentProfile, TeacherProfile,
    ParentProfile, StaffProfile, HeadTeacherProfile
)
from .serializers import (
    UserSerializer, RegisterSerializer,
    StudentProfileSerializer, TeacherProfileSerializer,
    ParentProfileSerializer, StaffProfileSerializer,
    HeadTeacherProfileSerializer
)

from academic.models import Classroom


def coerce_single_id(value):
    """
    Coerce a value that might be a list (e.g. ['3']) into a single ID string/int.
    """
    if isinstance(value, (list, tuple)) and len(value) > 0:
        return value[0]
    return value


# ------------------------------
# Register (Self)
# ------------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Account created. Waiting for Head Teacher to assign role.",
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)


# ------------------------------
# Register Student (by Headteacher)
# ------------------------------
class RegisterStudentByHeadTeacherView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != User.UserType.HEADTEACHER:
            return Response({"error": "Only headteachers can register students."}, status=403)

        # 1. Create user
        user_data = {
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "email": request.data.get("email"),
            "password": request.data.get("password"),
        }
        user_serializer = RegisterSerializer(data=user_data)
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=400)
        user = user_serializer.save()
        user.user_type = User.UserType.STUDENT
        user.save()

        # 2. Prepare profile data (flatten)
        profile_data = {}
        for key in request.data:
            value_list = request.data.getlist(key)
            profile_data[key] = value_list[0] if len(value_list) == 1 else value_list

        profile_data["user"] = user.id

        classroom_id = coerce_single_id(profile_data.get("classroom"))
        if classroom_id:
            try:
                profile_data["classroom"] = Classroom.objects.get(id=classroom_id).id
            except Classroom.DoesNotExist:
                user.delete()
                return Response({"error": "Invalid classroom selected."}, status=400)

        # Pass the full request.data to serializer to include files automatically
        serializer = StudentProfileSerializer(data=profile_data, context={"request": request})
        if not serializer.is_valid():
            user.delete()
            return Response(serializer.errors, status=400)

        serializer.save()

        return Response({
            "message": "Student registered successfully by Headteacher.",
            "user": UserSerializer(user).data,
            "profile": serializer.data
        }, status=201)


# ------------------------------
# Login
# ------------------------------
class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })


# ------------------------------
# Assign Role (by Headteacher)
# ------------------------------
class AssignRoleView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if request.user.user_type != User.UserType.HEADTEACHER:
            return Response({"error": "Only Head Teacher can assign roles"}, status=403)

        user = get_object_or_404(User, id=user_id)
        role = request.data.get("user_type")
        if role not in User.UserType.values:
            return Response({"error": "Invalid role type"}, status=400)

        user.user_type = role
        user.save()
        return Response({"message": f"Role '{role}' assigned successfully."})


# ------------------------------
# Create Profile (Self-Service)
# ------------------------------
class CreateProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Flatten data from QueryDict to simple dict with strings
        data = {}
        for key in request.data:
            value_list = request.data.getlist(key)
            data[key] = value_list[0] if len(value_list) == 1 else value_list

        print("===== Incoming request.data =====")
        print(request.data)
        print("===== Flattened data dict =====")
        print(data)

        serializer_map = {
            User.UserType.STUDENT: StudentProfileSerializer,
            User.UserType.TEACHER: TeacherProfileSerializer,
            User.UserType.PARENT: ParentProfileSerializer,
            User.UserType.STAFF: StaffProfileSerializer,
            User.UserType.HEADTEACHER: HeadTeacherProfileSerializer,
        }

        serializer_class = serializer_map.get(user.user_type)
        if not serializer_class:
            return Response({"error": "Invalid or missing user type."}, status=400)

        if user.user_type == User.UserType.STUDENT:
            classroom_id = coerce_single_id(data.get("classroom"))
            if classroom_id:
                try:
                    data["classroom"] = Classroom.objects.get(id=classroom_id).id
                except Classroom.DoesNotExist:
                    return Response({"error": "Invalid classroom selected."}, status=400)

        serializer = serializer_class(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile created successfully."})

        print("===== Serializer errors =====")
        print(serializer.errors)
        return Response(serializer.errors, status=400)


# ------------------------------
# View Profile
# ------------------------------
class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile_map = {
            User.UserType.STUDENT: StudentProfileSerializer(getattr(user, "student_profile", None)),
            User.UserType.TEACHER: TeacherProfileSerializer(getattr(user, "teacher_profile", None)),
            User.UserType.PARENT: ParentProfileSerializer(getattr(user, "parent_profile", None)),
            User.UserType.STAFF: StaffProfileSerializer(getattr(user, "staff_profile", None)),
            User.UserType.HEADTEACHER: HeadTeacherProfileSerializer(getattr(user, "headteacher_profile", None)),
        }
        profile_serializer = profile_map.get(user.user_type)

        profile_data = profile_serializer.data if profile_serializer else None

        # Add classroom_id at top level for convenience (if profile has classroom)
        if profile_data and isinstance(profile_data, dict):
            classroom = profile_data.get("classroom")
            if isinstance(classroom, dict) and "id" in classroom:
                # If classroom is nested dict (rare), extract id
                profile_data["classroom_id"] = classroom["id"]
            else:
                # Usually classroom is just the ID integer or None
                profile_data["classroom_id"] = classroom

        return Response({
            "user": UserSerializer(user).data,
            "profile": profile_data
        })


# ------------------------------
# Update Profile
# ------------------------------
class UpdateProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        # Flatten data from QueryDict
        data = {}
        for key in request.data:
            value_list = request.data.getlist(key)
            data[key] = value_list[0] if len(value_list) == 1 else value_list

        serializer_map = {
            User.UserType.STUDENT: StudentProfileSerializer,
            User.UserType.TEACHER: TeacherProfileSerializer,
            User.UserType.PARENT: ParentProfileSerializer,
            User.UserType.STAFF: StaffProfileSerializer,
            User.UserType.HEADTEACHER: HeadTeacherProfileSerializer,
        }

        profile_instance = None
        if user.user_type == User.UserType.STUDENT:
            profile_instance = getattr(user, "student_profile", None)
            classroom_id = coerce_single_id(data.get("classroom"))
            if classroom_id:
                try:
                    data["classroom"] = Classroom.objects.get(id=classroom_id).id
                except Classroom.DoesNotExist:
                    return Response({"error": "Invalid classroom selected."}, status=400)
        else:
            profile_instance = getattr(user, f"{user.user_type}_profile", None)

        if not profile_instance:
            return Response({"error": "Profile does not exist. Please create one first."}, status=404)

        serializer_class = serializer_map.get(user.user_type)
        serializer = serializer_class(profile_instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully."})
        return Response(serializer.errors, status=400)


# ------------------------------
# User Lists & Counts
# ------------------------------
class GetAllUsers(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type not in [User.UserType.HEADTEACHER, User.UserType.STAFF]:
            return Response({"error": "Access denied"}, status=403)
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)


class GetAllStudents(APIView):
    def get(self, request):
        students = User.objects.filter(user_type=User.UserType.STUDENT)
        return Response(UserSerializer(students, many=True).data)


class GetAllTeachers(APIView):
    def get(self, request):
        teachers = User.objects.filter(user_type=User.UserType.TEACHER)
        return Response(UserSerializer(teachers, many=True).data)


class GetAllParents(APIView):
    def get(self, request):
        parents = User.objects.filter(user_type=User.UserType.PARENT)
        return Response(UserSerializer(parents, many=True).data)


class GetAllStaff(APIView):
    def get(self, request):
        staff = User.objects.filter(user_type=User.UserType.STAFF)
        return Response(UserSerializer(staff, many=True).data)


class GetAllHeadTeachers(APIView):
    def get(self, request):
        heads = User.objects.filter(user_type=User.UserType.HEADTEACHER)
        return Response(UserSerializer(heads, many=True).data)


class CountUsers(APIView):
    def get(self, request):
        counts = {
            role: User.objects.filter(user_type=role).count()
            for role in User.UserType.values
        }
        return Response(counts)


# ------------------------------
# Admin Utilities
# ------------------------------
class DeleteUser(APIView):
    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return Response({"message": "User deleted"})


class ToggleBlockUser(APIView):
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response({"status": "Blocked" if not user.is_active else "Unblocked"})


class GetUnassignedUsers(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type != User.UserType.HEADTEACHER:
            return Response({"error": "Only Head Teachers can access this."}, status=403)
        users = User.objects.filter(user_type__isnull=True)
        if not users.exists():
            return Response({"message": "There are no unassigned users at the moment."})
        return Response(UserSerializer(users, many=True).data)
