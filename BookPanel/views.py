from django.shortcuts import render, redirect, get_object_or_404
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
def create_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('view_books')  #TODO add view books, update and delete books.
    else:
        form = BookForm()
    return render(request, 'Admin/create_book.html', {'form': form})

@login_required
def update_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            # Skip ISBN check for the current book
            isbn = form.cleaned_data.get('isbn')
            if Book.objects.filter(isbn=isbn).exclude(id=book_id).exists():
                form.add_error('isbn', f"A book with ISBN '{isbn}' already exists.")
            else:
                form.save()
                return redirect('view_books')
    else:
        form = BookForm(instance=book)
    return render(request, 'Admin/update_book.html', {'form': form, 'book': book})

@login_required
def delete_book(request):
    # Logic for book deletion
    pass

@login_required
def confirm_order(request):
    # Logic for order confirmation
    pass

@login_required
def view_books(request):
    # Logic for viewing all books and request counts
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