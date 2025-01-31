from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AccountForm
from Auth.models import User

def account_view(request):
    user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        if user:
            form = AccountForm(request.POST, instance=user)
        else:
            form = AccountForm(request.POST)

        if form.is_valid():
            if user:
                form.save()
                messages.success(request, 'Your details have been updated successfully.')
            else:
                account_data = form.cleaned_data
                new_user = User.objects.create_user(
                    username=account_data['email'],
                    first_name=account_data['first_name'],
                    last_name=account_data['last_name'],
                    email=account_data['email'],
                )
                new_user.set_unusable_password()
                new_user.save()
                request.session['account_data'] = account_data
                messages.success(request, 'Details saved. Account created successfully.')
            return redirect('account')

    else:
        if user:
            form = AccountForm(instance=user)
        else:
            account_data = request.session.get('account_data', {})
            form = AccountForm(initial=account_data)

    return render(request, 'Auth/account.html', {"form": form, "user": user})



