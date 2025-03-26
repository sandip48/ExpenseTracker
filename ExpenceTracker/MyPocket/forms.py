from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Expense, Category
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email',
            'id': 'id_email'
        }),
    )
    mobile_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
            'id': 'id_mobile_number'
        }),
        validators=[RegexValidator(r'^\+?[1-9]\d{1,14}$', 'Enter a valid mobile number (+1234567890).')],
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'id_profile_picture'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'mobile_number', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username',
                'id': 'id_username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter password',
                'id': 'id_password1'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirm password',
                'id': 'id_password2'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number')
        if UserProfile.objects.filter(mobile_number=mobile_number).exists():
            raise ValidationError("This mobile number is already registered.")
        return mobile_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Profile will be created by the signal
            # We'll update it in the view
        return user

class ExpenseForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        empty_label="Select a category"
    )
    
    new_category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Or enter new category'
        }),
        help_text="Leave blank to use existing category"
    )

    class Meta:
        model = Expense
        fields = ['name', 'amount', 'category', 'interest_rate', 'date', 'end_date', 'long_term', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Enter interest rate'
            }),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'long_term': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Optional description'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        long_term = cleaned_data.get("long_term")
        end_date = cleaned_data.get("end_date")
        interest_rate = cleaned_data.get("interest_rate")
        category = cleaned_data.get("category")
        new_category = cleaned_data.get("new_category")

        if amount and amount <= 0:
            self.add_error('amount', "Amount must be a positive number.")
        
        if long_term:
            if not end_date:
                self.add_error('end_date', "End date is required for long-term expenses.")
            if interest_rate is not None and interest_rate < 0:
                self.add_error('interest_rate', "Interest rate cannot be negative.")
        
        if new_category and not category:
            category, created = Category.objects.get_or_create(
                name=new_category.strip(),
                defaults={'user': self.instance.user if hasattr(self.instance, 'user') else None}
            )
            cleaned_data['category'] = category
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk and hasattr(self, 'user'):
            instance.user = self.user
        if commit:
            instance.save()
        return instance

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'budget_limit']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional description'
            }),
            'budget_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly budget limit (optional)'
            }),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'mobile_number', 'date_of_birth', 'address', 'gender', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }