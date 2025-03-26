from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date
from django.db.models import Sum
import re
from django.conf import settings
import os

# User Profile Model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        default='default.png', 
        blank=True, 
        null=True
    )
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], 
        blank=True, 
        null=True
    )
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def clean(self):
        """Ensure mobile number follows valid format and profile picture size is within limits"""
        super().clean()
        
        if self.mobile_number:
            pattern = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
            if not pattern.match(self.mobile_number):
                raise ValidationError("Invalid mobile number format.")
        
        if self.profile_picture:
            if self.profile_picture.size > settings.MAX_UPLOAD_SIZE:
                raise ValidationError(
                    f"Image size too large (max {settings.MAX_UPLOAD_SIZE/1024/1024}MB)"
                )
    
    def save(self, *args, **kwargs):
        """Handle profile picture cleanup"""
        try:
            old = UserProfile.objects.get(pk=self.pk)
            if old.profile_picture != self.profile_picture and old.profile_picture.name != 'default.png':
                old.profile_picture.delete(save=False)
        except UserProfile.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def get_age(self):
        """Calculate user's age from date of birth"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

# Category Model
class Category(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='categories', 
        null=True, 
        blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    budget_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_category_per_user',
                condition=models.Q(user__isnull=False)
            )
        ]
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate category name and budget limit."""
        if not self.name.strip():
            raise ValidationError("Category name cannot be empty.")
        if self.budget_limit and self.budget_limit <= 0:
            raise ValidationError("Budget limit must be positive.")

    def get_remaining_budget(self):
        """Calculate remaining budget for this category."""
        if not self.budget_limit:
            return None
        total_spent = self.expenses.aggregate(total=Sum('amount'))['total'] or 0
        return max(0, self.budget_limit - total_spent)

    def get_expense_count(self):
        """Get count of expenses in this category"""
        return self.expenses.count()

# Expense Model with Category
class Expense(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='expenses'
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='expenses'
    )
    date = models.DateField(default=timezone.now)
    long_term = models.BooleanField(default=False)
    interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        null=True, 
        blank=True
    )
    end_date = models.DateField(null=True, blank=True)
    monthly_expenses = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        null=True, 
        blank=True
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        category_name = self.category.name if self.category else "Uncategorized"
        return f"{self.name} - ₹{self.amount} ({category_name})"

    def clean(self):
        """Validate that data is correct before saving."""
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")

        if self.long_term:
            if not self.end_date:
                raise ValidationError("End date is required for long-term expenses.")
            if self.end_date <= self.date:
                raise ValidationError("End date must be after the start date.")
            if self.interest_rate and self.interest_rate < 0:
                raise ValidationError("Interest rate cannot be negative.")

        self.monthly_expenses = self.calculate_monthly_expenses()

    def calculate_monthly_expenses(self):
        """Calculate monthly payments based on term and interest rate."""
        if not self.long_term or not self.end_date:
            return self.amount  # Short-term: full amount at once

        months = (self.end_date.year - self.date.year) * 12 + (self.end_date.month - self.date.month)
        if months <= 0:
            return self.amount  # Avoid division errors

        if self.interest_rate == 0:
            return round(float(self.amount) / max(1, months), 2)  # Avoid division by zero

        monthly_rate = float(self.interest_rate) / 12 / 100
        monthly_payment = (float(self.amount) * monthly_rate) / (1 - (1 + monthly_rate) ** -months)
        return round(monthly_payment, 2)

    def save(self, *args, **kwargs):
        """Ensure clean is called before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def get_duration_months(self):
        """Get duration in months for long-term expenses"""
        if self.long_term and self.end_date:
            return (self.end_date.year - self.date.year) * 12 + (self.end_date.month - self.date.month)
        return 0

# Account Model
class Account(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='accounts'
    )
    name = models.CharField(max_length=100)
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    expenses = models.ManyToManyField(
        Expense, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} - ₹{self.balance}"

    def total_expenses(self):
        """Calculate total expenses linked to this account."""
        return self.expenses.aggregate(total=Sum('amount'))['total'] or 0

    def update_balance(self, save=False):
        """Update account balance without infinite recursion."""
        new_balance = self.total_expenses()
        if self.balance != new_balance:
            self.balance = new_balance
            if save:
                super().save(update_fields=['balance'])

    def save(self, *args, **kwargs):
        """Ensure balance is updated before saving."""
        self.update_balance(save=False)  
        super().save(*args, **kwargs)

    def get_expense_count(self):
        """Get count of expenses linked to this account"""
        return self.expenses.count()