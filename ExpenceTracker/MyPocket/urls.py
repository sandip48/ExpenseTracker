from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.views.decorators.cache import cache_page
from .views import (
    home, register, edit_profile, profile, test_error_view,
    ExpenseListView, ExpenseCreateView, ExpenseDetailView, ExpenseUpdateView, ExpenseDeleteView,
    add_expense_ajax, expense_detail_ajax, custom_login, custom_logout, expenses_list
)

urlpatterns = [
    # Home Page
    path('', cache_page(3600)(home), name='home'),
    path('test-error/', test_error_view),

    # Expense-related URLs
    path('expenses/', ExpenseListView.as_view(), name='expenses'),
    path('expenses/list/', expenses_list, name='expenses_list'),
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense_detail'),  # ✅ Corrected detail view
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_edit'),  # ✅ Corrected edit view
    path('expenses/<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),  # ✅ Added delete confirmation view
    
    # AJAX requests
    path('expenses/ajax_add_expense/', add_expense_ajax, name='ajax_add_expense'),
    path('expenses/ajax_expense_detail/<int:pk>/', expense_detail_ajax, name='ajax_expense_detail'),

    # User authentication URLs (Updated to use custom views)
    path('accounts/register/', register, name='register'),
    path('accounts/login/', custom_login, name='login'),  
    path('logout/', custom_logout, name='logout'),  

    # Profile-related URLs
    path('profile/', profile, name='profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),

    # Django's built-in authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
]
