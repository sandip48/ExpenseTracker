from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.db import transaction
import plotly.express as px
import logging
from django.views.decorators.cache import cache_control
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View

from .models import Expense, UserProfile
from .forms import ExpenseForm, CustomUserCreationForm, UserProfileForm

logger = logging.getLogger('django')

# Home Page
def home(request):
    return render(request, 'home/home.html')

# User Registration View
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    UserProfile.objects.create(user=user, mobile_number=form.cleaned_data['mobile_number'])
                    login(request, user)
                    logger.info(f"New user registered: {user.username}")
                    return redirect('home')
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}")
                form.add_error(None, "An error occurred. Please try again.")
        else:
            logger.error("Form submission error: %s", str(form.errors))
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# Custom Login View
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            logger.info(f"User logged in: {username}")
            return redirect('home')
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return render(request, 'registration/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'registration/login.html')

# Custom Logout View
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def custom_logout(request):
    logger.info(f"User logged out: {request.user.username}")
    logout(request)
    return redirect('home')

# User Profile View
@login_required
def profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, 'profile.html', {'profile': user_profile})

# Edit Profile View
@login_required
def edit_profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'registration/edit_profile.html', {'form': form})

# AJAX Add Expense
@login_required
def add_expense_ajax(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return JsonResponse({'success': True, 'message': 'Expense added successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid data!'})
    return JsonResponse({'success': False, 'message': 'Invalid request!'})

# AJAX Expense Detail
@login_required
def expense_detail_ajax(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    data = {
        'id': expense.id,
        'amount': expense.amount,
        'category': getattr(expense, 'category', 'Unknown'),
        'date': expense.date.strftime('%Y-%m-%d'),
        'description': getattr(expense, 'description', 'No description'),
    }
    return JsonResponse(data)

# Expense List View (Function-Based)
@login_required
def expenses_list(request):
    expenses = Expense.objects.filter(user=request.user)
    expense_data = {}
    for expense in expenses:
        year_month = expense.date.strftime('%Y-%m')
        expense_data.setdefault(year_month, 0)
        expense_data[year_month] += expense.amount
    
    graph_data = {'months': list(expense_data.keys()), 'expenses': list(expense_data.values())}
    context = {
        'expenses': expenses,
        'bar_chart': generate_graph(graph_data, 'bar'),
        'pie_chart': generate_graph(graph_data, 'pie'),
        'expense_form': ExpenseForm()
    }
    return render(request, 'exp_tracker/expenses_list.html', context)

# Helper Function for Chart Generation
def generate_graph(data, chart_type='bar'):
    if not data.get('months') or not data.get('expenses'):
        return mark_safe({'error': 'No data available for graph generation.'})
    try:
        if chart_type == 'bar':
            fig = px.bar(data, x='months', y='expenses', title='Monthly Expenses')
        elif chart_type == 'pie':
            fig = px.pie(data, values='expenses', names='months', title='Expense Distribution')
        return mark_safe(fig.to_json())
    except Exception as e:
        logger.error(f"Graph generation failed: {str(e)}")
        return mark_safe({'error': 'Graph generation error.'})

# Expense Class-Based Views
@method_decorator(cache_control(max_age=3600), name='dispatch')  
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'exp_tracker/expenses_list.html'
    context_object_name = 'expenses'

@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'exp_tracker/expenses_list.html'
    success_url = reverse_lazy('expenses')

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'exp_tracker/expense_detail.html'
    context_object_name = 'expense'

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'exp_tracker/expense_form.html'
    success_url = reverse_lazy('expenses')

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'exp_tracker/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses')

def test_error_view(request):
    logger.error("This is a test error log.")
    return HttpResponse("Error log test.")