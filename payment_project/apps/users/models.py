import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# class User(AbstractUser): # If extending AbstractUser for more fields
#     # Add custom fields here if needed, beyond what AbstractUser provides
#     # email = models.EmailField(unique=True) # Ensure email is unique
#     # USERNAME_FIELD = 'email' # If using email as username
#     # REQUIRED_FIELDS = ['username'] # If email is username, username might still be required for AbstractUser
#     pass

# For this project, we'll use the default Django User model for simplicity,
# as the schema didn't specify custom user fields beyond standard auth.
# If custom fields like a separate profile or specific user roles were needed,
# extending AbstractUser or using a OneToOneField to a Profile model would be appropriate.

# However, the schema provided a 'users' table with specific fields.
# Let's implement that directly. For a real project, integrating with Django's
# auth system (AbstractUser or AbstractBaseUser) is generally recommended.

class User(models.Model):
    id = models.AutoField(primary_key=True) # AutoField is int auto_increment by default
    username = models.CharField(max_length=255, unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False) # Store hashed passwords only
    email = models.EmailField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users' # Match the table name from the schema
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

# Note: For actual password management and authentication,
# Django's built-in auth system (django.contrib.auth) is highly recommended.
# Storing password_hash directly like this requires manual hashing and checking,
# which is error-prone. If this model is to be used with Django admin or auth forms,
# it needs to inherit from AbstractBaseUser and implement required methods/managers,
# or use AbstractUser.
# Given the context of the schema, this is a direct translation.
# For a new project, `django.contrib.auth.models.User` is often sufficient,
# or `AbstractUser` for customization.
