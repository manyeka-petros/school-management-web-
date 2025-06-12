from rest_framework import serializers
from .models import Classroom, Subject, Grade
from portalaccount.models import StudentProfile, TeacherProfile

# -------------------- Classroom Serializer --------------------

class ClassroomSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'teacher', 'teacher_name']
        extra_kwargs = {
            'teacher': {'read_only': True}
        }

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance

# -------------------- Grade Serializer --------------------

from rest_framework import serializers
from .models import Grade
from portalaccount.models import StudentProfile
from django.contrib.auth.models import User


class GradeSerializer(serializers.ModelSerializer):
    # Allow student name as input
    student_name = serializers.CharField(write_only=True, required=False)  # Optional input
    student_display = serializers.CharField(source='student.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    graded_by_name = serializers.CharField(source='graded_by.user.get_full_name', read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id',
            'student',            # Accepts ID input
            'student_name',       # Accepts "First Last" input
            'student_display',    # Shows student full name in response
            'subject',
            'subject_name',
            'exam_type',
            'score',
            'graded_by',
            'graded_by_name',
            'graded_at'
        ]
        read_only_fields = [
            'graded_by', 'graded_by_name', 'graded_at',
            'student_display', 'subject_name'
        ]

    def validate(self, attrs):
        student_name = attrs.pop('student_name', None)
        student = attrs.get('student', None)

        if student_name and not student:
            try:
                first_name, last_name = student_name.strip().split(' ', 1)
            except ValueError:
                raise serializers.ValidationError("Student name must include both first and last name.")

            user = User.objects.filter(
                first_name__iexact=first_name.strip(),
                last_name__iexact=last_name.strip()
            ).first()

            if not user:
                raise serializers.ValidationError(f'Student "{student_name}" not found.')

            student_profile = StudentProfile.objects.filter(user=user).first()
            if not student_profile:
                raise serializers.ValidationError(f'"{student_name}" is not a student.')

            attrs['student'] = student_profile

        if not attrs.get('student'):
            raise serializers.ValidationError("Student is required, either by ID or name.")

        return attrs

# -------------------- Subject Serializer --------------------

class SubjectSerializer(serializers.ModelSerializer):
    students = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=StudentProfile.objects.all(),
        required=False
    )
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    grades = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ['id', 'name', 'classroom', 'teacher', 'teacher_name', 'students', 'grades']
        extra_kwargs = {
            'teacher': {'read_only': True}
        }

    def get_grades(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'studentprofile'):
            student = request.user.studentprofile
            return GradeSerializer(
                obj.grades.filter(student=student),
                many=True
            ).data
        return []

    def create(self, validated_data):
        students = validated_data.pop('students', [])
        subject = super().create(validated_data)
        subject.students.set(students)
        return subject

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.classroom = validated_data.get('classroom', instance.classroom)

        if 'students' in validated_data:
            students = validated_data.pop('students')
            instance.students.set(students)

        instance.save()
        return instance
