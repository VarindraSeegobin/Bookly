from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BookForm, SchoolForm, SubjectForm
from Auth.models import Book, Order, Subject, School
from django.http import JsonResponse

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
def delete_book(request, book_id):
    pass

@login_required
def confirm_order(request):
    # Logic for order confirmation
    pass


def create_school(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('view_all_schools')
    else:
        form = SchoolForm()

    return render(request, 'Admin/create_school.html', {'form': form})



def update_school(request):
    pass

def view_all_schools(request):
    schools = School.objects.all().order_by('name')
    return render(request, 'Admin/view_all_schools.html', {'schools': schools})

# View to delete a school
def delete_school(request, school_id):
    if request.method == 'POST':
        try:
            school = School.objects.get(id=school_id)
            school.delete()
            return JsonResponse({'status': 'success'})
        except School.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

@login_required
def create_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()

    return render(request, 'Admin/create_subject.html', {'form': form})

def subject_list(request):
    subjects = Subject.objects.all().order_by('school__name')  # Sort subjects by school name
    return render(request, 'Admin/subject_list.html', {'subjects': subjects})


def update_subject(request):
    pass

def delete_subject(request, subject_id):
    if request.method == 'POST':
        try:
            subject = Subject.objects.get(id=subject_id)
            subject.delete()
            return JsonResponse({'status': 'success'})
        except Subject.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return render(request, subject_list)

@login_required
def view_orders(request):
    orders = Order.objects.all().filter(paid_for=True)
    return render(request, 'Admin/view_all_orders.html',{'orders': orders})


@login_required
def view_activity_log(request):
    # Logic for viewing activity log
    pass

@login_required
def logout_user(request):
    logout(request)
    return redirect('admin-login')