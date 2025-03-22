from django import forms
from django.core.exceptions import ValidationError
from Auth.models import Book, Subject, School, Stationary

class BookForm(forms.ModelForm):
    quantity = forms.IntegerField(initial=0)
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.all(),
                                              widget=forms.CheckboxSelectMultiple(),
                                              required=False,
                                              label="Subjects")
    class Meta:
        model = Book
        fields = ['title', 'isbn', 'author', 'publisher', 'quantity', 'cost', 'image', 'subjects']
        widgets = {
            'image': forms.URLInput(attrs={'placeholder': 'Enter image URL'}),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if Book.objects.filter(isbn=isbn).exists():
            raise ValidationError(f"A book with ISBN '{isbn}' already exists.")
        return isbn

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['title', 'name']

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'school']

class StationaryForm(forms.ModelForm):
    quantity = forms.IntegerField(initial=0)
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.all(),
                                              widget=forms.CheckboxSelectMultiple(),
                                              required=False,
                                              label="Subjects")
    class Meta:
        model = Stationary
        quantity = forms.IntegerField(initial=0)
        fields = ['title', 'quantity', 'cost', 'image', 'subjects']
        widgets = {
            'image': forms.URLInput(attrs={'placeholder': 'Enter image URL'}),
        }