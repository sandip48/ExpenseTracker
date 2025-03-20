from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Expense, Account
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    mobile_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[RegexValidator(r'^[\d\s+-]+$', 'Enter a valid mobile number.')]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'mobile_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, mobile_number=self.cleaned_data['mobile_number'])
        return user

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'amount', 'interest_rate', 'date', 'end_date', 'long_term']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter interest rate'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'long_term': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        if amount and amount <= 0:
            self.add_error('amount', "Amount must be a positive number.")
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'mobile_number', 'date_of_birth', 'address', 'gender', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'form-control'}, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }