from rest_framework import serializers
from .models import Book, PastPaper

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class PastPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastPaper
        fields = '__all__'
