from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Classroom, Subject, Grade, Enrollment
from portalaccount.models import StudentProfile, TeacherProfile
from .serializers import ClassroomSerializer, SubjectSerializer, GradeSerializer

User = get_user_model()

# -------------------- Classroom --------------------
class ClassroomListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        classrooms = Classroom.objects.all()
        serializer = ClassroomSerializer(classrooms, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        teacher_profile = get_object_or_404(TeacherProfile, user=user)
        data = request.data.copy()
        data["teacher"] = teacher_profile.id
        serializer = ClassroomSerializer(data=data)
        if serializer.is_valid():
            serializer.save(teacher=teacher_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------- Subject --------------------
class SubjectCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        teacher_profile = get_object_or_404(TeacherProfile, user=user)
        data = request.data.copy()
        serializer = SubjectSerializer(data=data)
        if serializer.is_valid():
            serializer.save(teacher=teacher_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubjectEnrollStudent(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        student_id = request.data.get("student_id")
        student = get_object_or_404(StudentProfile, id=student_id)

        if Enrollment.objects.filter(student=student, subject=subject).exists():
            return Response({'message': 'Student is already enrolled in this subject.'}, status=status.HTTP_200_OK)

        Enrollment.objects.create(student=student, subject=subject)
        return Response({'message': 'Student enrolled successfully.'}, status=status.HTTP_201_CREATED)

# -------------------- Grade --------------------
class GradeCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.user_type != User.UserType.TEACHER:
            return Response({'detail': 'Only teachers can assign grades.'}, status=status.HTTP_403_FORBIDDEN)

        teacher_profile = get_object_or_404(TeacherProfile, user=user)
        data = request.data.copy()

        student_name = data.get('student_name')
        subject_id = data.get('subject')
        exam_type = data.get('exam_type')

        if not student_name or not subject_id or not exam_type:
            return Response({'detail': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        # Match student by full name
        student_user = None
        for student in User.objects.filter(user_type=User.UserType.STUDENT):
            full_name = f"{student.first_name.strip()} {student.last_name.strip()}"
            if full_name.lower() == student_name.strip().lower():
                student_user = student
                break

        if not student_user:
            return Response({'detail': f'Student "{student_name}" not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch StudentProfile
        try:
            student_profile = StudentProfile.objects.get(user=student_user)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Student profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent duplicate grade
        if Grade.objects.filter(student=student_profile, subject_id=subject_id, exam_type=exam_type).exists():
            return Response({'detail': 'Grade already exists for this student, subject, and exam type.'},
                            status=status.HTTP_400_BAD_REQUEST)

        data['student'] = student_profile.id

        serializer = GradeSerializer(data=data)
        if serializer.is_valid():
            serializer.save(graded_by=teacher_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GradeCreateOrUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        teacher_profile = get_object_or_404(TeacherProfile, user=user)
        data = request.data.copy()

        student_id = data.get('student')
        subject_id = data.get('subject')
        exam_type = data.get('exam_type')

        if not (student_id and subject_id and exam_type):
            return Response({"error": "student, subject, and exam_type are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(StudentProfile, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)

        grade_qs = Grade.objects.filter(student=student, subject=subject, exam_type=exam_type)
        if grade_qs.exists():
            grade_instance = grade_qs.first()
            serializer = GradeSerializer(grade_instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = GradeSerializer(data=data)
        if serializer.is_valid():
            serializer.save(graded_by=teacher_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentGrades(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get("student_id")
        student_profile = get_object_or_404(StudentProfile, id=student_id)
        grades = Grade.objects.filter(student=student_profile)
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

# -------------------- Classroom Students --------------------
class ClassroomStudents(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, classroom_id):
        subjects = Subject.objects.filter(classroom_id=classroom_id)
        student_ids = Enrollment.objects.filter(subject__in=subjects).values_list("student_id", flat=True).distinct()
        students = StudentProfile.objects.filter(id__in=student_ids)

        data = [
            {
                "id": student.id,
                "full_name": student.user.get_full_name(),
                "email": student.user.email
            }
            for student in students
        ]
        return Response(data)

# -------------------- Profiles --------------------
class TeacherProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        teacher_profile = get_object_or_404(TeacherProfile, user=user)
        data = {
            'id': teacher_profile.id,
            'full_name': user.get_full_name(),
            'email': user.email,
        }
        return Response(data)

class StudentProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        student_profile = get_object_or_404(StudentProfile, user=user)
        data = {
            'id': student_profile.id,
            'full_name': user.get_full_name(),
            'email': user.email,
        }
        return Response(data)

# -------------------- Dashboard --------------------
class TeacherDashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        teacher_profile = get_object_or_404(TeacherProfile, user=user)
        classrooms = Classroom.objects.filter(teacher=teacher_profile)
        serializer = ClassroomSerializer(classrooms, many=True)
        return Response({
            "teacher": teacher_profile.user.username,
            "classrooms": serializer.data
        }, status=status.HTTP_200_OK)

# -------------------- Subjects for Students --------------------
class SubjectListForStudents(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        student = get_object_or_404(StudentProfile, user=user)

        enrolled_subject_ids = Enrollment.objects.filter(student=student).values_list('subject_id', flat=True)
        enrolled_subjects = Subject.objects.filter(id__in=enrolled_subject_ids)
        available_subjects = Subject.objects.exclude(id__in=enrolled_subject_ids)

        enrolled_serializer = SubjectSerializer(enrolled_subjects, many=True, context={'request': request})
        available_serializer = SubjectSerializer(available_subjects, many=True, context={'request': request})

        return Response({
            "available_subjects": available_serializer.data,
            "enrolled_subjects": enrolled_serializer.data
        }, status=status.HTTP_200_OK)

class EnrollInSubject(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, subject_id):
        user = request.user
        student = get_object_or_404(StudentProfile, user=user)
        subject = get_object_or_404(Subject, id=subject_id)

        if Enrollment.objects.filter(student=student, subject=subject).exists():
            return Response({'message': 'You are already enrolled in this subject.'}, status=status.HTTP_200_OK)

        Enrollment.objects.create(student=student, subject=subject)
        return Response({'message': 'You have successfully enrolled in this subject.'}, status=status.HTTP_201_CREATED)

class EnrolledSubjectsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id')
        if student_id:
            student = get_object_or_404(StudentProfile, id=student_id)
        else:
            student = get_object_or_404(StudentProfile, user=request.user)

        subject_ids = Enrollment.objects.filter(student=student).values_list("subject_id", flat=True)
        subjects = Subject.objects.filter(id__in=subject_ids)

        serializer = SubjectSerializer(subjects, many=True, context={'request': request})
        return Response({"enrolled_subjects": serializer.data}, status=status.HTTP_200_OK)

class AllSubjectsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subjects = Subject.objects.all()
        serializer = SubjectSerializer(subjects, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class GradeDetailOrList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, grade_id=None):
        if grade_id:
            grade = get_object_or_404(Grade, id=grade_id)
            serializer = GradeSerializer(grade)
            return Response(serializer.data)
        grades = Grade.objects.all()
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)
# -------------------- Grade Delete --------------------
class GradeDelete(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, grade_id):
        user = request.user

        if user.user_type != User.UserType.TEACHER:
            return Response({'detail': 'Only teachers can delete grades.'}, status=status.HTTP_403_FORBIDDEN)

        grade = get_object_or_404(Grade, id=grade_id)

        # Optional: Ensure the teacher trying to delete the grade is the one who assigned it
        if grade.graded_by.user != user:
            return Response({'detail': 'You do not have permission to delete this grade.'}, status=status.HTTP_403_FORBIDDEN)

        grade.delete()
        return Response({'detail': 'Grade deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
