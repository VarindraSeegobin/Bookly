from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BookForm
from Auth.models import Book

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin-homepage')
        else:
            messages.error(request, 'Incorrect username or password.')

    return render(request, 'Admin/login.html')

@login_required
def homepage(request):
    return render(request, 'Admin/home.html')

@login_required
def view_books(request):
    if not request.user.is_superuser:
        return redirect('admin-login')

    books = Book.objects.all()
    print(books)

    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        action = request.POST.get('action')

        if book_id and action == 'delete':
            book = get_object_or_404(Book, id=book_id)
            book.delete()
            return redirect('view_books')
        elif action == 'update':
            return redirect('update_book', book_id=book_id)
        return HttpResponseBadRequest(request,"Invalid action or missing book_id.")
    return render(request, 'Admin/view_books.html', {'books': books})
#TODO style



@login_required
def create_book(request):
    if request.method == 'POST' and request.user.is_superuser:
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('view_books')  #TODO add view books, update and delete books.
    elif request.user.is_superuser:
        form = BookForm()
        return render(request, 'Admin/create_book.html', {'form': form})
    else:
        return redirect('admin-login')

@login_required
def update_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not request.user.is_superuser:
        return redirect('admin-login')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)  # Include request.FILES for file uploads
        if form.is_valid():
            isbn = form.cleaned_data.get('isbn')
            if Book.objects.filter(isbn=isbn).exclude(id=book_id).exists():
                form.add_error('isbn', f"A book with ISBN '{isbn}' already exists.")
            else:
                form.save()
                return redirect('view_books')
        else:
            # Render the form with errors if validation fails
            return render(request, 'Admin/update_book.html', {'form': form, 'book': book})

    elif request.method == 'GET':
        form = BookForm(instance=book)  # Pre-fill the form with existing data
        return render(request, 'Admin/update_book.html', {'form': form, 'book': book})

    return HttpResponseBadRequest("Invalid request method.") #TODO prepopulate update book with all field data.


@login_required
def delete_book(request):
    # Logic for book deletion
    pass

@login_required
def confirm_order(request):
    # Logic for order confirmation
    pass


@login_required
def view_orders(request):
    # Logic for viewing all orders
    pass

@login_required
def view_activity_log(request):
    # Logic for viewing activity log
    pass

@login_required
def logout_user(request):
    logout(request)
    return redirect('admin-login')