from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import plotly.express as px
import logging
from django.views.decorators.cache import cache_control
from datetime import datetime
from collections import defaultdict
from django.db.models import Sum, Count, Min, Max
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import Expense, UserProfile, Category
from .forms import ExpenseForm, CustomUserCreationForm, UserProfileForm, CategoryForm

logger = logging.getLogger('django')

# ========================
# Core Application Views
# ========================

def home(request):
    """Home page view with caching"""
    if request.user.is_authenticated:
        return redirect('expenses_list')
    return render(request, 'home/home.html')

# ========================
# Authentication Views
# ========================

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def register(request):
    """Improved user registration view with better profile handling"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Get the UserProfile created by the signal
                    profile = user.profile
                    
                    # Update profile with additional fields
                    profile.mobile_number = form.cleaned_data['mobile_number']
                    
                    # Handle profile picture upload if provided
                    if 'profile_picture' in request.FILES:
                        profile_picture = request.FILES['profile_picture']
                        if profile_picture.size > settings.MAX_UPLOAD_SIZE:
                            raise ValidationError("Image size too large (max 2MB)")
                        profile.profile_picture = profile_picture
                    
                    profile.save()
                    
                    # Log the user in
                    login(request, user)
                    return redirect('expenses_list')
                    
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                form.add_error(None, f"Registration failed: {str(e)}")
        else:
            logger.error(f"Form validation errors: {form.errors}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'error_messages': form.errors.get('__all__', [])
    })

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def custom_login(request):
    """Custom login view with next-page redirect support"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"User logged in: {user.username}")
            return redirect(request.GET.get("next", "expenses_list"))
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def custom_logout(request):
    """Custom logout view with logging"""
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.username}")
        logout(request)
    return redirect('home')

# ========================
# Category Management Views
# ========================

@login_required
def category_list(request):
    """List all categories for the current user"""
    categories = Category.objects.filter(user=request.user)
    return render(request, 'categories/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'categories/category_form.html', {'form': form})

@login_required
def category_edit(request, pk):
    """Edit an existing category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'categories/category_form.html', {'form': form})

@login_required
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'categories/category_confirm_delete.html', {'category': category})

# ========================
# Profile Views
# ========================

@login_required
def profile(request):
    """User profile view with expense statistics"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    stats = Expense.objects.filter(user=request.user).aggregate(
        total_expenses=Sum('amount'),
        expense_count=Count('id'),
        first_expense=Min('date'),
        last_expense=Max('date')
    )
    return render(request, 'profile.html', {
        'profile': user_profile,
        'stats': stats
    })

@login_required
def edit_profile(request):
    """Profile editing view"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'registration/edit_profile.html', {'form': form})

# ========================
# Expense AJAX Views
# ========================

@login_required
@require_POST
def add_expense_ajax(request):
    """Secure AJAX endpoint for adding expenses with category support"""
    form = ExpenseForm(request.POST, user=request.user)
    if form.is_valid():
        try:
            expense = form.save(commit=False)
            expense.user = request.user
            
            # Handle new category creation if provided
            new_category = form.cleaned_data.get('new_category')
            if new_category and not form.cleaned_data.get('category'):
                category, created = Category.objects.get_or_create(
                    name=new_category.strip(),
                    user=request.user
                )
                expense.category = category
            
            expense.save()
            return JsonResponse({
                'success': True,
                'message': 'Expense added successfully!',
                'data': {
                    'id': expense.id,
                    'name': expense.name,
                    'amount': expense.amount,
                    'category': expense.category.name if expense.category else 'Uncategorized',
                    'date': expense.date.strftime('%Y-%m-%d')
                }
            })
        except Exception as e:
            logger.error(f"AJAX expense save error: {str(e)}")
            return JsonResponse({
                'success': False,
                'errors': {'server': ['Failed to save expense']}
            }, status=500)
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)

@login_required
def expense_detail_ajax(request, pk):
    """AJAX endpoint for expense details with category support"""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    return JsonResponse({
        'name': expense.name,
        'amount': expense.amount,
        'category': expense.category.name if expense.category else 'Uncategorized',
        'date': expense.date.strftime('%Y-%m-%d'),
        'description': expense.description or 'No description',
        'long_term': expense.long_term,
        'interest_rate': expense.interest_rate or 'N/A',
        'monthly_expenses': expense.monthly_expenses or 'N/A'
    })

# ========================
# Expense Views
# ========================

@login_required
def expenses_list(request):
    """Optimized expense list view with chart data and categories"""
    expenses = Expense.objects.filter(user=request.user).select_related('category').order_by('-date')
    
    # Calculate statistics
    stats = expenses.aggregate(
        total_amount=Sum('amount'),
        expense_count=Count('id'),
        first_expense_date=Min('date'),
        last_expense_date=Max('date')
    )
    
    # Process data for charts
    monthly_data = defaultdict(float)
    category_data = defaultdict(float)
    
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        monthly_data[month_key] += expense.amount
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_data[category_name] += expense.amount
    
    context = {
        'expenses': expenses,
        'bar_chart': generate_graph(monthly_data, 'bar'),
        'pie_chart': generate_graph(category_data, 'pie'),
        'expense_form': ExpenseForm(user=request.user),
        'total_amount': stats['total_amount'] or 0,
        'expense_count': stats['expense_count'],
        'first_expense_date': stats['first_expense_date'],
        'last_expense_date': stats['last_expense_date'],
        'categories': Category.objects.filter(user=request.user)
    }
    return render(request, 'exp_tracker/expenses_list.html', context)

def generate_graph(data, chart_type='bar'):
    """Helper function for generating Plotly charts"""
    if not data:
        return mark_safe('{}')
    
    try:
        if chart_type == 'bar':
            fig = px.bar(
                x=list(data.keys()),
                y=list(data.values()),
                title='Monthly Expenses',
                labels={'x': 'Month', 'y': 'Amount'},
                color=list(data.values()),
                color_continuous_scale='Bluered'
            )
        else:
            fig = px.pie(
                values=list(data.values()),
                names=list(data.keys()),
                title='Expense Distribution',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return mark_safe(fig.to_json())
    except Exception as e:
        logger.error(f"Chart generation error: {str(e)}")
        return mark_safe('{}')

# ========================
# Expense Class-Based Views
# ========================

@method_decorator(cache_control(max_age=3600), name='dispatch')
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'exp_tracker/expenses_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).select_related('category').order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expenses = context['expenses']
        
        stats = expenses.aggregate(
            total_amount=Sum('amount'),
            expense_count=Count('id'),
            first_expense_date=Min('date'),
            last_expense_date=Max('date')
        )
        
        context.update({
            'total_amount': stats['total_amount'] or 0,
            'expense_count': stats['expense_count'],
            'first_expense_date': stats['first_expense_date'],
            'last_expense_date': stats['last_expense_date'],
            'expense_form': ExpenseForm(user=self.request.user),
            'categories': Category.objects.filter(user=self.request.user)
        })
        return context

@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'exp_tracker/expense_form.html'
    success_url = reverse_lazy('expenses_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'exp_tracker/expense_detail.html'
    context_object_name = 'expense'
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).select_related('category')

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'exp_tracker/expense_form.html'
    success_url = reverse_lazy('expenses_list')
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).select_related('category')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'exp_tracker/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses_list')
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

# ========================
# Utility Views
# ========================

def test_error_view(request):
    """Test view for error logging"""
    logger.error("Test error logged successfully")
    return HttpResponse("Error test completed")