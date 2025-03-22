from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BookForm, SchoolForm, SubjectForm, StationaryForm
from Auth.models import Book, Order, Subject, School, Stationary
from BookPanel.forms import AdminLoginForm
from django.http import JsonResponse

def admin_login(request):
    form = AdminLoginForm(request.POST or None)  # Instantiate form with POST data if available

    if request.method == 'POST':
        if form.is_valid():  # Validate form, including captcha
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_superuser:
                login(request, user)
                return redirect('admin-homepage')
            else:
                messages.error(request, 'Incorrect username or password.')
        else:
            messages.error(request, 'Invalid captcha. Please try again.')

    return render(request, 'Admin/login.html', {'form': form})

@login_required
def homepage(request):
    if not request.user.is_superuser:
        return redirect('admin_login')
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
    if not request.user.is_superuser:
        return redirect('admin_login')
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
def view_stationary(request):
    if not request.user.is_superuser:
        return redirect('admin-login')

    stationary_items = Stationary.objects.all()

    if request.method == 'POST':
        stationary_id = request.POST.get('stationary_id')
        action = request.POST.get('action')

        if stationary_id and action == 'delete':
            stationary_item = get_object_or_404(Stationary, id=stationary_id)
            stationary_item.delete()
            return redirect('view_stationary')
        elif action == 'update':
            return redirect('update_stationary', stationary_id=stationary_id)
        return HttpResponseBadRequest("Invalid action or missing stationary_id.")

    return render(request, 'Admin/view_stationary.html', {'stationary_items': stationary_items})


# Create new stationary item
@login_required
def create_stationary(request):
    if not request.user.is_superuser:
        return redirect('admin-login')

    if request.method == 'POST' and request.user.is_superuser:
        form = StationaryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('view_stationary')  # Redirect after saving the new stationary item.
    else:
        form = StationaryForm()

    return render(request, 'Admin/create_stationary.html', {'form': form})


@login_required
def delete_book(request, book_id):
    pass

@login_required
def confirm_order(request):
    # Logic for order confirmation
    pass


def create_school(request):
    if not request.user.is_superuser:
        return redirect('admin_login')
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
    if not request.user.is_superuser:
        return redirect('admin_login')
    schools = School.objects.all().order_by('name')
    return render(request, 'Admin/view_all_schools.html', {'schools': schools})

# View to delete a school
def delete_school(request, school_id):
    if not request.user.is_superuser:
        return redirect('admin_login')
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
    if not request.user.is_superuser:
        return redirect('admin_login')
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()

    return render(request, 'Admin/create_subject.html', {'form': form})

def subject_list(request):
    if not request.user.is_superuser:
        return redirect('admin_login')
    subjects = Subject.objects.all().order_by('school__name')  # Sort subjects by school name
    return render(request, 'Admin/subject_list.html', {'subjects': subjects})


def update_subject(request):
    pass


@login_required
def delete_subject(request, subject_id):
    if not request.user.is_superuser:
        return redirect('admin_login')
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
    if not request.user.is_superuser:
        return redirect('admin_login')
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