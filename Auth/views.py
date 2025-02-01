from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Book

def index(request):
    return render(request, 'Auth/home.html')

def search_books(request):
    query = request.GET.get('q', '')
    if query:
        results = Book.objects.filter(title__icontains=query)
        book_titles = [book.title for book in results]
        return JsonResponse({'results': book_titles})
    return JsonResponse({'results': []})
