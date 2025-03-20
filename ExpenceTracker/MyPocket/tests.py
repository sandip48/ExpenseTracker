from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now
from .models import Expense, Account, UserProfile

class ExpenseModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.expense = Expense.objects.create(
            name='Test Expense',
            amount=100,
            date=now().date(),
            long_term=True,
            interest_rate=5.0,
            end_date=now().date().replace(year=now().year + 1),  # 1 year later
            user=cls.user
        )

    def test_expense_creation(self):
        self.assertEqual(self.expense.name, 'Test Expense')
        self.assertEqual(self.expense.amount, 100)
        self.assertTrue(self.expense.long_term)
        self.assertEqual(self.expense.user, self.user)

    def test_expense_string_representation(self):
        self.assertEqual(str(self.expense), 'Test Expense')

    def test_monthly_expense_calculation(self):
        """Ensure monthly expense calculation works for long-term expenses"""
        self.assertGreater(self.expense.calculate_monthly_expense(), 0)

class AccountModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.account = Account.objects.create(
            name='Test Account',
            expense=0,
            user=cls.user
        )

    def test_account_creation(self):
        self.assertEqual(self.account.name, 'Test Account')
        self.assertEqual(self.account.expense, 0)
        self.assertEqual(self.account.user, self.user)

    def test_account_string_representation(self):
        self.assertEqual(str(self.account), 'Test Account')

class UserProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.profile = UserProfile.objects.create(user=cls.user, mobile_number='1234567890')

    def test_profile_creation(self):
        """Test if the user profile is created correctly"""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.mobile_number, '1234567890')

    def test_profile_string_representation(self):
        """Test the __str__ method of UserProfile model"""
        self.assertEqual(str(self.profile), "testuser's Profile")
