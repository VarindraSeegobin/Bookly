from django import forms
from Auth.models import User

class AccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
