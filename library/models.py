from django.db import models

# Create your models here.
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='books/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PastPaper(models.Model):
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    year = models.IntegerField()
    file = models.FileField(upload_to='past_papers/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.year}"
