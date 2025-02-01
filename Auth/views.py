from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Book

def index(request):
    return render(request, 'Auth/home.html')

def search_books(request):
    query = request.GET.get('q', '')
    if query:
        results = Book.objects.filter(title__icontains=query)
        book_data = [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "image": book.image,  # Ensure `image` is a field in your model
                "cost": book.cost
            }
            for book in results
        ]
        return JsonResponse({'results': book_data})
    return JsonResponse({'results': []})
