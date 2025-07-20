# grading/models.py
# ────────────────────────────────────────────────────────────────
# Minimal models for the grading app.

from django.db import models
from portalaccount.models import StudentProfile
from academic.models import Classroom, Subject

# ────────────────────────────────────────────────────────────────
# 1. Exam‑type (e.g. Midterm, Quiz …)
class ExamType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# ────────────────────────────────────────────────────────────────
# 2. Grade scale (A, B, C …)
class Grade(models.Model):
    name        = models.CharField(max_length=5)               # “A”, “B+” …
    score_from  = models.DecimalField(max_digits=5, decimal_places=2)
    score_to    = models.DecimalField(max_digits=5, decimal_places=2)
    comment     = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-score_from"]          # highest mark first

    def __str__(self):
        return f"{self.name} ({self.score_from}-{self.score_to})"


# ────────────────────────────────────────────────────────────────
# 3. ManageExam – one row per result
class ManageExam(models.Model):
    classroom   = models.ForeignKey(Classroom,        on_delete=models.CASCADE)
    section     = models.CharField(max_length=50, blank=True, null=True)  # optional
    subject     = models.ForeignKey(Subject,          on_delete=models.CASCADE)
    student     = models.ForeignKey(StudentProfile,   on_delete=models.CASCADE)
    exam_type   = models.ForeignKey(ExamType,         on_delete=models.CASCADE)
    score       = models.DecimalField(max_digits=5, decimal_places=2)
    comment     = models.TextField(blank=True, null=True)
    date_recorded = models.DateField(auto_now_add=True)

    # NEW ▶ keeps a snapshot of the grade that matched the score
    grade       = models.ForeignKey(
        Grade, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="exam_records"
    )

    class Meta:
        # stop the same record being captured twice
        unique_together = ("student", "subject", "exam_type", "classroom")

    # nice string in the admin
    def __str__(self):
        return f"{self.student} – {self.exam_type} – {self.subject}"

    # helper to calculate grade on the fly
    def get_grade(self):
        if self.grade:                      # already stored?
            return self.grade
        return Grade.objects.filter(
            score_from__lte=self.score,
            score_to__gte=self.score
        ).first()
