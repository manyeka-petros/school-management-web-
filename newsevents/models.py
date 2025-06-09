from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='announcements/', blank=True, null=True) 

    def __str__(self):
        return self.title
