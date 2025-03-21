from django import forms
from Auth.models import User, School
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

class AccountForm(forms.ModelForm):
    school = forms.ModelChoiceField(queryset=School.objects.all())
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'school']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email already exists in the database
        try:
            user = User.objects.get(email=email)
            # If email exists, we can handle it as a login instead of registration
            self.instance = user  # Associate the existing user with the form instance
        except User.DoesNotExist:
            pass  # No need to do anything, it's a new account

        return email
