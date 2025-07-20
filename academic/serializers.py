from rest_framework import serializers

from .models import (
    Classroom,
    Subject,
    ClassroomSubject,
    StudentSubject,
)
from portalaccount.models import TeacherProfile, StudentProfile
from portalaccount.serializers import TeacherProfileSerializer

# ───────────────────────────────────────────────
# SUBJECT
# ───────────────────────────────────────────────
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "code", "description"]
        extra_kwargs = {"code": {"required": False}}

    def validate_code(self, value):
        if value and not value.isalnum():
            raise serializers.ValidationError("Subject code must be alphanumeric.")
        return value


# ───────────────────────────────────────────────
# CLASSROOM
# ───────────────────────────────────────────────
class ClassroomSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.CharField(
        source="class_teacher.user.full_name", read_only=True
    )
    class_teacher_detail = TeacherProfileSerializer(
        source="class_teacher", read_only=True
    )

    class Meta:
        model = Classroom
        fields = [
            "id",
            "name",
            "section",
            "academic_year",
            "class_teacher",
            "class_teacher_name",
            "class_teacher_detail",
            "created_at",
        ]
        extra_kwargs = {
            "class_teacher": {"required": False},
            "section": {"required": False},
        }

    def validate_academic_year(self, value):
        if len(value) < 4:
            raise serializers.ValidationError("Academic year seems invalid.")
        return value


# ───────────────────────────────────────────────
# CLASSROOM-SUBJECT ASSIGNMENT
# ───────────────────────────────────────────────
class ClassroomSubjectSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.__str__", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.full_name", read_only=True)

    classroom_detail = ClassroomSerializer(source="classroom", read_only=True)
    subject_detail = SubjectSerializer(source="subject", read_only=True)
    teacher_detail = TeacherProfileSerializer(source="teacher", read_only=True)

    teacher = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = ClassroomSubject
        fields = [
            "id",
            "classroom",
            "subject",
            "teacher",
            "classroom_name",
            "classroom_detail",
            "subject_name",
            "subject_detail",
            "teacher_name",
            "teacher_detail",
        ]

    def to_internal_value(self, data):
        validated = super().to_internal_value(data)
        teacher_user_id = data.get("teacher")
        teacher_profile = TeacherProfile.objects.filter(user_id=teacher_user_id).first()
        if not teacher_profile:
            raise serializers.ValidationError(
                {"teacher": f"No TeacherProfile found for user ID {teacher_user_id}."}
            )
        validated["teacher"] = teacher_profile
        return validated

    def validate(self, attrs):
        classroom = attrs.get("classroom") or getattr(self.instance, "classroom", None)
        subject = attrs.get("subject") or getattr(self.instance, "subject", None)

        if classroom and subject:
            qs = ClassroomSubject.objects.filter(classroom=classroom, subject=subject)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("This subject is already assigned to that classroom.")
        return attrs


# ───────────────────────────────────────────────
# STUDENT-SUBJECT (Explicit per student)
# ───────────────────────────────────────────────
class StudentSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    classroom_name = serializers.CharField(source="classroom.__str__", read_only=True)

    # OPTIONAL: Show student name (helpful for admin usage)
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)

    # OPTIONAL: Prevent student ID from being exposed unless writing
    student = serializers.PrimaryKeyRelatedField(
        queryset=StudentProfile.objects.all(), write_only=True
    )

    class Meta:
        model = StudentSubject
        fields = [
            "id",
            "student",
            "student_name",  # Optional for UI or admin display
            "subject",
            "subject_name",
            "classroom",
            "classroom_name",
            "assigned_at",
        ]
        read_only_fields = ["assigned_at", "subject_name", "classroom_name", "student_name"]
