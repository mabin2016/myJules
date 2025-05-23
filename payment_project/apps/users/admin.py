from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'created_at', 'updated_at')
    search_fields = ('username', 'email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'password_hash') # password_hash should not be editable

    # If using Django's built-in User or AbstractUser, you'd use:
    # from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
    # class UserAdmin(BaseUserAdmin):
    #     # Add custom fields to fieldsets or list_display
    #     pass

# Note: Since apps.users.models.User is a custom model not inheriting from
# Django's auth user classes, the admin interface will be basic.
# For full Django auth integration (password management, permissions),
# the model would need to be derived from AbstractUser or AbstractBaseUser.
