from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from .models import Book, Stationary  # Import your Book model


def index(request):
    books = Book.objects.all()[:50]
    stationaries = Stationary.objects.all()[:50]
    book_content_type = ContentType.objects.get_for_model(Book)
    stationary_content_type = ContentType.objects.get_for_model(Stationary)

    # Add content_type_id to each book
    for book in books:
        book.content_type_id = book_content_type.id

    for stationary in stationaries:
        stationary.content_type_id = stationary_content_type.id

    return render(request, 'Auth/home.html', {'books': books, 'stationaries': stationaries})


def search_books(request):
    query = request.GET.get('q', '').strip()

    if query:
        # Fetch book results
        book_results = Book.objects.filter(title__icontains=query)
        book_content_type = ContentType.objects.get_for_model(Book)
        book_data = [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "image": book.image,
                "cost": float(book.cost),  # Ensure JSON serializable
                "content_type_id": book_content_type.id,
            }
            for book in book_results
        ]

        # Fetch stationary results
        stationary_results = Stationary.objects.filter(title__icontains=query)
        stationary_content_type = ContentType.objects.get_for_model(Stationary)
        stationary_data = [
            {
                "id": item.id,
                "title": item.title,
                "image": item.image,
                "cost": float(item.cost),  # Ensure JSON serializable
                "content_type_id": stationary_content_type.id,
            }
            for item in stationary_results
        ]

        # Combine results
        book_data.extend(stationary_data)

        return JsonResponse({'results': book_data})

    return JsonResponse({'results': []})

