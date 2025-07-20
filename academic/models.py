from django.db import models
from portalaccount.models import StudentProfile, TeacherProfile


# =============================
# Subject Model
# =============================
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


# =============================
# Classroom Model
# =============================
class Classroom(models.Model):
    CLASS_CHOICES = [
        ('Form 1', 'Form 1'),
        ('Form 2', 'Form 2'),
        ('Form 3', 'Form 3'),
        ('Form 4', 'Form 4'),
    ]

    name = models.CharField(max_length=50, choices=CLASS_CHOICES)
    section = models.CharField(max_length=30, blank=True, null=True)
    academic_year = models.CharField(max_length=100)
    class_teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_teacher_of'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.section or 'No Section'} ({self.academic_year})"


# =============================
# ClassroomSubject (Join Table)
# =============================
class ClassroomSubject(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='classroom_subjects'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='classroom_subjects'
    )
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_subjects'
    )

    class Meta:
        unique_together = ('classroom', 'subject')
        verbose_name = 'Classroom Subject'
        verbose_name_plural = 'Classroom Subjects'

    def __str__(self):
        teacher_name = self.teacher.user.full_name if self.teacher else 'No Teacher Assigned'
        return f"{self.classroom} - {self.subject.name} ({teacher_name})"
class StudentSubject(models.Model):
    student = models.ForeignKey('portalaccount.StudentProfile', on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'classroom')

    def __str__(self):
        return f"{self.student} - {self.subject}"


# =============================
# Enrollment (Student to Classroom)
# =============================
class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'classroom')
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'

    def __str__(self):
        return f"{self.student.user.full_name} - {self.classroom} ({self.status})"
