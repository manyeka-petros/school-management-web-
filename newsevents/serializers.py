from rest_framework import serializers
from .models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'file',  'posted_at']
        read_only_fields = ['posted_at']
