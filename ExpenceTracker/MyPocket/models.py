from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date

# User Profile Model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.png', blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Expense Model
class Expense(models.Model):
    name = models.CharField(max_length=100)
    amount = models.FloatField(default=0)
    date = models.DateField(default=timezone.now)
    long_term = models.BooleanField(default=False)
    interest_rate = models.FloatField(default=0, null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_expenses = models.FloatField(default=0, null=True, blank=True)
    description = models.TextField(blank=True, null=True)  # ✅ Added description field
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')

    def __str__(self):
        return self.name

    def clean(self):
        if self.long_term:
            if not self.end_date:
                raise ValidationError("End date is required for long-term expenses.")
            if self.interest_rate is not None and self.interest_rate < 0:
                raise ValidationError("Interest rate cannot be negative.")

        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")

        self.monthly_expenses = self.calculate_monthly_expense()

    def calculate_monthly_expense(self):
        if not self.long_term or not self.end_date:
            return 0.01  # Prevent division by zero

        months = (self.end_date.year - self.date.year) * 12 + (self.end_date.month - self.date.month)
        if months <= 0:
            return 0.01  # Avoid errors when months are zero or negative

        if self.interest_rate == 0:
            return self.amount / months

        monthly_rate = self.interest_rate / 12 / 100
        return (self.amount * monthly_rate) / (1 - (1 + monthly_rate) ** -months)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# Account Model
class Account(models.Model):
    name = models.CharField(max_length=100)
    expense = models.FloatField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    expense_list = models.ManyToManyField(Expense, blank=True)

    def __str__(self):
        return self.name
