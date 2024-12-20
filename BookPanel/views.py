from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
    # Logic for book creation
    pass

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
def logout(request):
    logout(request)
    return redirect('admin-login')