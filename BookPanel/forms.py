from django import forms
from django.core.exceptions import ValidationError
from Auth.models import Book, Subject

class BookForm(forms.ModelForm):
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