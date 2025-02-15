from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Book
from django.contrib.contenttypes.models import ContentType

def index(request):
    return render(request, 'Auth/home.html')

def search_books(request):
    query = request.GET.get('q', '')
    if query:
        results = Book.objects.filter(title__icontains=query)
        content_type = ContentType.objects.get_for_model(Book)
        book_data = [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "image": book.image,
                "cost": book.cost,
                'content_type_id': content_type.id,
            }
            for book in results
        ]
        return JsonResponse({'results': book_data})
    return JsonResponse({'results': []})
