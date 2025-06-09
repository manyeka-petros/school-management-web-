from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from .models import Book, PastPaper
from .serializers import BookSerializer, PastPaperSerializer

class BookAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        books = Book.objects.all().order_by('-uploaded_at')
        serializer = BookSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PastPaperAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        papers = PastPaper.objects.all().order_by('-uploaded_at')
        serializer = PastPaperSerializer(papers, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = PastPaperSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
