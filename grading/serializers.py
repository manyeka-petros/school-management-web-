# grading/serializers.py
# ────────────────────────────────────────────────────────────────
# Serialisers for:
#   1. Exam Type
#   2. Grade scale
#   3. Exam records (ManageExam)
# ────────────────────────────────────────────────────────────────
from django.db import transaction
from rest_framework import serializers

from .models import ExamType, Grade, ManageExam
from academic.models import Classroom, Subject          # (import kept – used by DRF browsable API)
from portalaccount.models import StudentProfile


# ╭────────────────────────────────────────────╮
# │ 1. Exam Type                              │
# ╰────────────────────────────────────────────╯
class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ExamType
        fields = ["id", "name"]


# ╭────────────────────────────────────────────╮
# │ 2. Grade scale                             │
# ╰────────────────────────────────────────────╯
class GradeSerializer(serializers.ModelSerializer):
    # Front‑end may send “grade_name” instead of “name”
    grade_name = serializers.CharField(
        source="name", write_only=True, required=False
    )

    class Meta:
        model  = Grade
        fields = ["id", "name", "grade_name", "score_from", "score_to", "comment"]
        extra_kwargs = {"name": {"required": True}}

    # Map grade_name → name if only that is supplied
    def to_internal_value(self, data):
        if data.get("grade_name") and not data.get("name"):
            data["name"] = data["grade_name"]
        return super().to_internal_value(data)

    # Simple range check
    def validate(self, attrs):
        if attrs["score_to"] < attrs["score_from"]:
            raise serializers.ValidationError(
                "'score_to' cannot be smaller than 'score_from'."
            )
        return attrs


# ╭────────────────────────────────────────────╮
# │ 3. Exam record (ManageExam)                │
# ╰────────────────────────────────────────────╯
class ManageExamSerializer(serializers.ModelSerializer):
    # Read‑only “nice strings” for the UI
    classroom_name = serializers.CharField(source="classroom.__str__", read_only=True)
    subject_name   = serializers.CharField(source="subject.name",        read_only=True)
    student_name   = serializers.CharField(source="student.user.full_name",
                                           read_only=True)
    exam_type_name = serializers.CharField(source="exam_type.name",      read_only=True)

    # Optional explicit grade override
    grade_id = serializers.PrimaryKeyRelatedField(
        source="grade",
        queryset=Grade.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    grade_name    = serializers.CharField(read_only=True)
    grade_comment = serializers.CharField(read_only=True)

    class Meta:
        model  = ManageExam
        fields = [
            "id",
            "classroom",
            "subject",
            "student",
            "exam_type",
            "score",
            "comment",
            "date_recorded",

            # helper strings
            "classroom_name",
            "subject_name",
            "student_name",
            "exam_type_name",

            # grade info
            "grade_id",
            "grade_name",
            "grade_comment",
        ]
        read_only_fields = ["date_recorded"]

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────
    @staticmethod
    def _grade_for_score(score: int | float) -> Grade | None:
        """Return the Grade that matches this score (or None)."""
        return Grade.objects.filter(score_from__lte=score, score_to__gte=score).first()

    def _auto_set_grade(self, instance: ManageExam) -> None:
        """
        After save: attach the correct Grade based on score
        (unless the user already chose one).
        """
        grade = self._grade_for_score(instance.score)
        if grade and instance.grade_id != grade.id:
            instance.grade = grade
            instance.save(update_fields=["grade"])
        # keep for to_representation
        self._cached_grade = grade

    # ──────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────
    def validate_score(self, value):
        if value < 0:
            raise serializers.ValidationError("Score cannot be negative.")
        return value

    def validate(self, attrs):
        """
        Block duplicate rows:
        same student + subject + exam‑type + classroom.
        """
        instance = getattr(self, "instance", None)

        # values to check – take new data if present, else existing value
        check = {
            "classroom": attrs.get("classroom", instance.classroom if instance else None),
            "subject":   attrs.get("subject",   instance.subject   if instance else None),
            "student":   attrs.get("student",   instance.student   if instance else None),
            "exam_type": attrs.get("exam_type", instance.exam_type if instance else None),
        }

        qs = ManageExam.objects.filter(**check)
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "An exam record for this student / subject / exam type already exists."
            )
        return attrs

    # ──────────────────────────────────────────
    # Hook in grade auto‑assignment
    # ──────────────────────────────────────────
    @transaction.atomic
    def create(self, validated_data):
        obj = super().create(validated_data)
        self._auto_set_grade(obj)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        obj = super().update(instance, validated_data)
        self._auto_set_grade(obj)
        return obj

    # ──────────────────────────────────────────
    # Add grade details to output
    # ──────────────────────────────────────────
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        grade = getattr(self, "_cached_grade", None) or self._grade_for_score(instance.score)
        if grade:
            rep["grade_name"]    = grade.name
            rep["grade_comment"] = grade.comment
        return rep
