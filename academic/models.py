from django.db import models
from django.conf import settings
from portalaccount.models import StudentProfile, TeacherProfile  # adjust path as needed

class Classroom(models.Model):
    name = models.CharField(max_length=50, choices=[
        ('Form 1', 'Form 1'),
        ('Form 2', 'Form 2'),
        ('Form 3', 'Form 3'),
        ('Form 4', 'Form 4')
    ])
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='classrooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='subjects')

    def __str__(self):
        return f"{self.name} ({self.classroom})"

class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'subject']

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"

# models.py
class Grade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=50)  # e.g., "midterm", "final", "quiz"
    score = models.FloatField()
    graded_by = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_type')
