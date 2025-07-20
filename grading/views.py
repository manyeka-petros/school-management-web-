from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.db import models

from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import ExamType, Grade, ManageExam
from .serializers import ExamTypeSerializer, GradeSerializer, ManageExamSerializer

from academic.models import (
    Classroom, StudentProfile, ClassroomSubject, StudentSubject
)
from academic.serializers import StudentSubjectSerializer


# ─────────────────────────────────────────────
# 1. ExamType – list and create new exam types
# ─────────────────────────────────────────────
class ExamTypeListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all exam types (like Midterm, Final)
        try:
            qs = ExamType.objects.all().order_by("name")
            data = ExamTypeSerializer(qs, many=True).data
            return Response(data)
        except Exception as e:
            print("[ExamType LIST]", e)
            return Response({"detail": "Something went wrong"}, status=500)

    def post(self, request):
        # Add a new exam type
        ser = ExamTypeSerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            return Response(ExamTypeSerializer(obj).data, status=201)
        print("[ExamType CREATE]", ser.errors)
        return Response(ser.errors, status=400)


# ─────────────────────────────────────────────
# 2. Grade – Full CRUD for grading system
# ─────────────────────────────────────────────
class GradeListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all grade ranges (A, B, C, etc.)
        try:
            qs = Grade.objects.all().order_by("-score_from")
            data = GradeSerializer(qs, many=True).data
            return Response(data)
        except Exception as e:
            print("[Grade LIST]", e)
            return Response({"detail": "Something went wrong"}, status=500)

    def post(self, request):
        # Create a new grade range
        ser = GradeSerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            return Response(GradeSerializer(obj).data, status=201)
        print("[Grade CREATE]", ser.errors)
        return Response(ser.errors, status=400)


class GradeDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Grade, pk=pk)

    def get(self, request, pk):
        # Get details of one grade
        return Response(GradeSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        # Update a grade fully
        grade = self.get_object(pk)
        ser = GradeSerializer(grade, data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def patch(self, request, pk):
        # Update part of a grade (e.g. comment only)
        grade = self.get_object(pk)
        ser = GradeSerializer(grade, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        # Delete a grade
        grade = self.get_object(pk)
        grade.delete()
        return Response(status=204)


# ─────────────────────────────────────────────
# 3. Manage Exams – Add, edit, and list exams
# ─────────────────────────────────────────────
class ManageExamListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def _filtered_queryset(self, request):
        # Apply filters if classroom, student, subject, or exam_type is selected
        qs = ManageExam.objects.select_related(
            "classroom", "subject", "student__user", "exam_type"
        ).all()
        params = {
            "classroom": request.query_params.get("classroom"),
            "subject": request.query_params.get("subject"),
            "student": request.query_params.get("student"),
            "exam_type": request.query_params.get("exam_type"),
        }
        params = {k: v for k, v in params.items() if v}
        return qs.filter(**params) if params else qs

    def get(self, request):
        # Get list of exams, filtered if needed
        try:
            qs = self._filtered_queryset(request).order_by("-date_recorded")
            data = ManageExamSerializer(qs, many=True).data
            return Response(data)
        except Exception as e:
            print("[ManageExam LIST]", e)
            return Response({"detail": "Something went wrong"}, status=500)

    def post(self, request):
        # Create a new exam record
        ser = ManageExamSerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            return Response(ManageExamSerializer(obj).data, status=201)
        print("[ManageExam CREATE]", ser.errors)
        return Response(ser.errors, status=400)


class ManageExamDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(ManageExam, pk=pk)

    def get(self, request, pk):
        # Get one exam
        return Response(ManageExamSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        # Update exam fully
        exam = self.get_object(pk)
        ser = ManageExamSerializer(exam, data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def patch(self, request, pk):
        # Update part of exam
        exam = self.get_object(pk)
        ser = ManageExamSerializer(exam, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        # Delete exam record
        exam = self.get_object(pk)
        exam.delete()
        return Response(status=204)


class MyExamsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get(self, request):
        # Show exams for the currently logged-in student
        try:
            student = request.user.student_profile
            qs = ManageExam.objects.filter(student=student).order_by("-date_recorded")
            return Response(ManageExamSerializer(qs, many=True).data)
        except AttributeError:
            return Response({"detail": "Only students can access this."}, status=403)


# ─────────────────────────────────────────────
# 4. Helper View – Get students in a classroom
# ─────────────────────────────────────────────
class StudentsByClassroomAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get(self, request):
        # classroom=<id>
        classroom_id = request.query_params.get("classroom")
        if not classroom_id:
            return Response({"detail": "classroom parameter required"}, status=400)

        classroom = get_object_or_404(Classroom, pk=classroom_id)
        students = StudentProfile.objects.filter(classroom=classroom).select_related("user")

        data = [
            {
                "id": s.id,
                "user_id": s.user.id,
                "full_name": s.user.get_full_name()
            }
            for s in students
        ]
        return Response(data, status=200)


# ─────────────────────────────────────────────
# 5. Helper View – Get subjects for a student
# ─────────────────────────────────────────────
class SubjectsByStudentAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def get(self, request):
        # student=<id>
        student_id = request.query_params.get("student")
        if not student_id:
            return Response({"detail": "student parameter required"}, status=400)

        student = get_object_or_404(StudentProfile, pk=student_id)

        # First check StudentSubject (manual assignment)
        subjects = StudentSubject.objects.select_related("subject", "classroom").filter(student=student)
        if subjects.exists():
            return Response(StudentSubjectSerializer(subjects, many=True).data, status=200)

        # If no direct subject, use classroom subjects
        if not student.classroom:
            return Response([], status=200)

        classroom_subjects = ClassroomSubject.objects.select_related("subject", "teacher", "teacher__user").filter(classroom=student.classroom)

        data = [
            {
                "subject": row.subject.name,
                "subject_id": row.subject.id,
                "teacher": row.teacher.user.get_full_name() if row.teacher else "Unassigned"
            }
            for row in classroom_subjects
        ]
        return Response(data, status=200)
