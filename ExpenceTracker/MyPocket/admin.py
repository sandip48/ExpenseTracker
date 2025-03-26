from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import UserProfile, Expense, Account, Category
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Custom Admin Classes

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('mobile_number', 'profile_picture_preview', 'profile_picture', 'bio', 
              'date_of_birth', 'gender', 'address', 'website')
    readonly_fields = ('profile_picture_preview',)

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(f'<img src="{obj.profile_picture.url}" style="max-height: 100px; max-width: 100px;" />')
        return "No Image"
    profile_picture_preview.short_description = 'Preview'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_mobile_number')
    list_select_related = ('profile',)

    def get_mobile_number(self, obj):
        return obj.profile.mobile_number if hasattr(obj, 'profile') else None
    get_mobile_number.short_description = 'Mobile Number'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'profile_picture_preview', 'date_of_birth')
    search_fields = ('user__username', 'mobile_number', 'user__email')
    list_filter = ('gender', 'user__is_active', 'user__date_joined')
    readonly_fields = ('profile_picture_preview', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'mobile_number')
        }),
        ('Profile Info', {
            'fields': ('profile_picture_preview', 'profile_picture', 'bio', 'date_of_birth', 'gender')
        }),
        ('Contact Info', {
            'fields': ('address', 'website')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(f'<img src="{obj.profile_picture.url}" style="max-height: 100px; max-width: 100px;" />')
        return "No Image"
    profile_picture_preview.short_description = 'Current Profile Picture'

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'amount_with_currency', 'date', 'category_link', 'long_term_indicator', 'description_short')
    search_fields = ('name', 'user__username', 'category__name', 'description')
    list_filter = ('long_term', 'date', 'category', 'user')
    readonly_fields = ('created_at', 'updated_at', 'monthly_expenses')
    list_select_related = ('user', 'category')
    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'amount', 'category')
        }),
        ('Details', {
            'fields': ('date', 'long_term', 'interest_rate', 'end_date', 'monthly_expenses')
        }),
        ('Additional Info', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def amount_with_currency(self, obj):
        return f"₹{obj.amount:,.2f}"
    amount_with_currency.short_description = 'Amount'
    amount_with_currency.admin_order_field = 'amount'

    def category_link(self, obj):
        if obj.category:
            url = f"/admin/MyPocket/category/{obj.category.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.category.name)
        return "-"
    category_link.short_description = 'Category'
    category_link.admin_order_field = 'category__name'

    def long_term_indicator(self, obj):
        return "✔" if obj.long_term else "✖"
    long_term_indicator.short_description = 'Long Term'
    long_term_indicator.admin_order_field = 'long_term'

    def description_short(self, obj):
        return obj.description[:50] + "..." if obj.description and len(obj.description) > 50 else obj.description or "-"
    description_short.short_description = 'Description'

class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_link', 'balance_with_currency', 'expense_count')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'expense_count')
    filter_horizontal = ('expenses',)

    def user_link(self, obj):
        url = f"/admin/auth/user/{obj.user.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'

    def balance_with_currency(self, obj):
        return f"₹{obj.balance:,.2f}"
    balance_with_currency.short_description = 'Balance'
    balance_with_currency.admin_order_field = 'balance'

    def expense_count(self, obj):
        return obj.expenses.count()
    expense_count.short_description = '# Expenses'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_link', 'budget_limit_with_currency', 'expense_count', 'remaining_budget')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'expense_count', 'remaining_budget')

    def user_link(self, obj):
        if obj.user:
            url = f"/admin/auth/user/{obj.user.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "System"
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'

    def budget_limit_with_currency(self, obj):
        return f"₹{obj.budget_limit:,.2f}" if obj.budget_limit else "-"
    budget_limit_with_currency.short_description = 'Budget Limit'
    budget_limit_with_currency.admin_order_field = 'budget_limit'

    def expense_count(self, obj):
        return obj.expenses.count()
    expense_count.short_description = '# Expenses'

    def remaining_budget(self, obj):
        remaining = obj.get_remaining_budget()
        if remaining is not None:
            return f"₹{remaining:,.2f}"
        return "-"
    remaining_budget.short_description = 'Remaining Budget'

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register models with their custom admin classes
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Category, CategoryAdmin)