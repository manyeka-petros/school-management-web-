from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer,
    StudentProfileSerializer, TeacherProfileSerializer, ParentProfileSerializer
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'user': serializer.data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        user_data = UserSerializer(user).data

        profile_data = None
        if user.user_type == 'student' and hasattr(user, 'student_profile'):
            profile_data = StudentProfileSerializer(user.student_profile).data
        elif user.user_type == 'teacher' and hasattr(user, 'teacher_profile'):
            profile_data = TeacherProfileSerializer(user.teacher_profile).data
        elif user.user_type == 'parent' and hasattr(user, 'parent_profile'):
            profile_data = ParentProfileSerializer(user.parent_profile).data

        return Response({
            'refresh': str(refresh),
            'access': access_token,
            'user': user_data,
            'profile': profile_data
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        response_data = {
            'role': user.user_type,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }

        if user.user_type == 'student' and hasattr(user, 'student_profile'):
            response_data['student_profile'] = StudentProfileSerializer(user.student_profile).data
        elif user.user_type == 'teacher' and hasattr(user, 'teacher_profile'):
            response_data['teacher_profile'] = TeacherProfileSerializer(user.teacher_profile).data
        elif user.user_type == 'parent' and hasattr(user, 'parent_profile'):
            response_data['parent_profile'] = ParentProfileSerializer(user.parent_profile).data

        return Response(response_data)

    def post(self, request):
        user = request.user
        profile_data = request.data.copy()

        serializer_class = None
        profile_instance = None

        if user.user_type == 'student':
            serializer_class = StudentProfileSerializer
            profile_instance = getattr(user, 'student_profile', None)
        elif user.user_type == 'teacher':
            serializer_class = TeacherProfileSerializer
            profile_instance = getattr(user, 'teacher_profile', None)
        elif user.user_type == 'parent':
            serializer_class = ParentProfileSerializer
            profile_instance = getattr(user, 'parent_profile', None)

        if serializer_class is None:
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializer_class(
            instance=profile_instance,
            data=profile_data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        profile_data = request.data

        if user.user_type == 'student' and hasattr(user, 'student_profile'):
            serializer = StudentProfileSerializer(user.student_profile, data=profile_data, partial=True)
        elif user.user_type == 'teacher' and hasattr(user, 'teacher_profile'):
            serializer = TeacherProfileSerializer(user.teacher_profile, data=profile_data, partial=True)
        elif user.user_type == 'parent' and hasattr(user, 'parent_profile'):
            serializer = ParentProfileSerializer(user.parent_profile, data=profile_data, partial=True)
        else:
            return Response({'error': 'Invalid user type or missing profile'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetAllStudentsTeachersView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        students = User.objects.filter(user_type='student')
        teachers = User.objects.filter(user_type='teacher')
        return Response({
            'students': UserSerializer(students, many=True).data,
            'teachers': UserSerializer(teachers, many=True).data
        })


class DeleteUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class BlockUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response({
            'message': f"User {'blocked' if not user.is_active else 'unblocked'} successfully",
            'is_active': user.is_active
        })


class CountUsersView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_students = User.objects.filter(user_type='student').count()
        total_teachers = User.objects.filter(user_type='teacher').count()
        return Response({
            'total_students': total_students,
            'total_teachers': total_teachers
        })


class CheckTokenView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"User from token: {request.user}")
        return Response({"message": "Token is valid"})


class DeleteUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
