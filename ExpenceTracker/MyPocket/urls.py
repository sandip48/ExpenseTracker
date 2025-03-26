
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.views.decorators.cache import cache_page
from .views import (
    home, register, edit_profile, profile, test_error_view,
    ExpenseListView, ExpenseCreateView, ExpenseDetailView,
    ExpenseUpdateView, ExpenseDeleteView,
    add_expense_ajax, expense_detail_ajax, custom_login, custom_logout,
    category_list, category_create, category_edit, category_delete
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ========================
    # Core Application URLs
    # ========================
    path('', home, name='home'),
    path('test-error/', test_error_view, name='test_error'),

    # ========================
    # Expense Management URLs
    # ========================
    path('expenses/', ExpenseListView.as_view(), name='expenses'), 
    path('expenses/', ExpenseListView.as_view(), name='expenses_list'),
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_edit'),
    path('expenses/<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),

    # ========================
    # Category Management URLs
    # ========================
    path('categories/', category_list, name='category_list'),
    path('categories/new/', category_create, name='category_create'),
    path('categories/<int:pk>/edit/', category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', category_delete, name='category_delete'),

    # ========================
    # API Endpoints
    # ========================
    path('api/expenses/add/', add_expense_ajax, name='add_expense_ajax'),
    path('api/expenses/<int:pk>/', expense_detail_ajax, name='expense_detail_ajax'),

    # ========================
    # Authentication URLs
    # ========================
    path('accounts/register/', register, name='register'),
    path('accounts/login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),

    # ========================
    # Profile URLs
    # ========================
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    # Django's built-in auth URLs
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)