from django.db import models
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Classroom, Subject, ClassroomSubject, Enrollment, StudentSubject
from portalaccount.models import StudentProfile, TeacherProfile
from .serializers import ClassroomSerializer, SubjectSerializer, ClassroomSubjectSerializer, StudentSubjectSerializer


def sync_student_subjects(student):
    """
    Ensure that all classroom subjects are assigned explicitly as StudentSubject to the given student.
    """
    if not student.classroom:
        return 0

    classroom_subjects = ClassroomSubject.objects.filter(classroom=student.classroom)
    created_count = 0
    for cs in classroom_subjects:
        obj, created = StudentSubject.objects.get_or_create(
            student=student,
            subject=cs.subject,
            classroom=student.classroom,
        )
        if created:
            created_count += 1
    return created_count


class ClassroomListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        data = ClassroomSerializer(Classroom.objects.all(), many=True, context={"request": request}).data
        return Response(data)

    def post(self, request):
        ser = ClassroomSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        data = SubjectSerializer(Subject.objects.all(), many=True, context={"request": request}).data
        return Response(data)

    def post(self, request):
        ser = SubjectSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignClassroomSubject(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        data = ClassroomSubjectSerializer(
            ClassroomSubject.objects.select_related("classroom", "subject", "teacher", "teacher__user"),
            many=True,
            context={"request": request},
        ).data
        return Response(data)

    def post(self, request):
        classroom_id   = request.data.get("classroom")
        subject_id     = request.data.get("subject")
        teacher_userid = request.data.get("teacher")

        if not all([classroom_id, subject_id, teacher_userid]):
            return Response(
                {"error": "Fields 'classroom', 'subject', and 'teacher' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        classroom = get_object_or_404(Classroom, id=classroom_id)
        subject   = get_object_or_404(Subject,   id=subject_id)
        teacher   = TeacherProfile.objects.filter(user_id=teacher_userid).first()

        if not teacher:
            return Response(
                {"error": f"No TeacherProfile found for user ID {teacher_userid}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cs, created = ClassroomSubject.objects.get_or_create(
            classroom=classroom,
            subject=subject,
            defaults={"teacher": teacher},
        )
        if not created:
            cs.teacher = teacher
            cs.save()

        return Response(
            {
                "message": "Assignment successful.",
                "classroom": classroom.name,
                "subject": subject.name,
                "teacher": teacher.user.get_full_name() or teacher.user.username,
            },
            status=status.HTTP_201_CREATED,
        )


class EnrollInClassroom(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        classroom_id = request.data.get("classroom_id")
        if not classroom_id:
            return Response({"error": "classroom_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(StudentProfile, user=request.user)
        classroom = get_object_or_404(Classroom, id=classroom_id)

        if student.classroom:
            return Response({"error": "Student is already enrolled."}, status=status.HTTP_400_BAD_REQUEST)

        if Enrollment.objects.filter(student=student).exists():
            return Response({"error": "Enrollment already exists."}, status=status.HTTP_400_BAD_REQUEST)

        Enrollment.objects.create(student=student, classroom=classroom, status="active")
        student.classroom = classroom
        student.save(update_fields=["classroom"])

        # Assign classroom subjects explicitly to student
        created_count = sync_student_subjects(student)

        return Response(
            {
                "message": f"Enrolled in {classroom.name} successfully.",
                "subjects_assigned": created_count,
            },
            status=status.HTTP_201_CREATED,
        )


class StudentSubjectsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request, uid=None):
        if uid is None:
            student = get_object_or_404(StudentProfile, user=request.user)
        else:
            if not (request.user.is_staff or hasattr(request.user, "teacher_profile")):
                return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            student = get_object_or_404(StudentProfile, pk=uid)

        subjects = StudentSubject.objects.select_related("subject", "classroom").filter(student=student)
        if subjects.exists():
            return Response(StudentSubjectSerializer(subjects, many=True).data, status=status.HTTP_200_OK)

        # fallback: classroom subjects dynamically if no explicit StudentSubject
        if not student.classroom:
            return Response({"message": "Student is not in a classroom."}, status=status.HTTP_404_NOT_FOUND)

        fallback = ClassroomSubject.objects.select_related("subject", "teacher", "teacher__user").filter(
            classroom=student.classroom
        )

        data = [
            {
                "subject": row.subject.name,
                "teacher": row.teacher.user.get_full_name() if row.teacher else "Unassigned",
            }
            for row in fallback
        ]
        return Response(data, status=status.HTTP_200_OK)


class MyAssignedSubjectsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        student = get_object_or_404(StudentProfile, user=request.user)
        subjects_qs = StudentSubject.objects.select_related("subject").filter(student=student)
        data = StudentSubjectSerializer(subjects_qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class ClassroomDetailsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request, pk):
        classroom = get_object_or_404(Classroom, pk=pk)

        students_qs = StudentProfile.objects.filter(
            models.Q(classroom=classroom) |
            models.Q(enrollments__classroom=classroom, enrollments__status="active")
        ).select_related("user").distinct()

        subjects_qs = Subject.objects.filter(classroom_subjects__classroom=classroom).distinct()

        students = [
            {
                "id": s.id,
                "full_name": s.user.get_full_name(),
                "user_id": s.user.id,
                "first_name": s.user.first_name,
                "last_name": s.user.last_name,
            }
            for s in students_qs
        ]

        subjects = [{"id": s.id, "name": s.name} for s in subjects_qs]

        return Response({"students": students, "subjects": subjects}, status=status.HTTP_200_OK)
