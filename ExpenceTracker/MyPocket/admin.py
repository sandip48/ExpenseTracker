from django.contrib import admin
from .models import UserProfile, Expense, Account

# Custom Admin Class for UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture')
    search_fields = ('user__username', 'bio')
    list_filter = ('user__is_active',)

# Custom Admin Class for Expense
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'date', 'user', 'long_term', 'monthly_expenses', 'description')  # ✅ Added description
    search_fields = ('name', 'user__username', 'description')  # ✅ Now searchable by description
    list_filter = ('long_term', 'date')
    readonly_fields = ('monthly_expenses',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

# Custom Admin Class for Account
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'expense', 'user')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'expense_list' in [field.name for field in Account._meta.get_fields()]:  
            self.filter_horizontal = ('expense_list',)  # ✅ Ensures this is only set if the field exists
        return form

# Register models with their custom admin classes
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Account, AccountAdmin)
