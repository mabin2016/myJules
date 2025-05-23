from django.test import TestCase
# from django.contrib.auth import get_user_model # Use this if using Django's default User or AbstractUser
from apps.users.models import User # Using the custom User model
from django.contrib.auth.hashers import check_password, make_password

# User = get_user_model() # If you switch to Django's auth User

class UserModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Note: Our custom User model doesn't have a create_user helper by default.
        # For a model not inheriting from AbstractBaseUser, we create directly.
        # Password hashing should ideally be handled by a manager or during form/serializer validation.
        # For testing the model directly, we'll set the hashed password.
        cls.raw_password = 'testpassword123'
        hashed_password = make_password(cls.raw_password)
        cls.user = User.objects.create(
            username='testuser',
            email='testuser@example.com',
            password_hash=hashed_password
        )

    def test_user_creation(self):
        """Test that a user can be created with valid data."""
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@example.com')
        self.assertTrue(check_password(self.raw_password, self.user.password_hash))

    def test_user_str_representation(self):
        """Test the __str__ method of the User model."""
        self.assertEqual(str(self.user), 'testuser')

    def test_username_uniqueness(self):
        """Test that username must be unique."""
        with self.assertRaises(Exception): # Depending on DB, could be IntegrityError
            User.objects.create(
                username='testuser', 
                email='another@example.com', 
                password_hash=make_password('anotherpass')
            )

    def test_email_uniqueness(self):
        """Test that email must be unique."""
        with self.assertRaises(Exception): # Depending on DB, could be IntegrityError
             User.objects.create(
                username='anotheruser', 
                email='testuser@example.com', 
                password_hash=make_password('anotherpass')
            )

    def test_user_timestamps(self):
        """Test that created_at and updated_at are set."""
        self.assertIsNotNone(self.user.created_at)
        self.assertIsNotNone(self.user.updated_at)
        # Check that updated_at is greater or equal to created_at
        self.assertTrue(self.user.updated_at >= self.user.created_at)

        # Further test: save user and check if updated_at changes
        # old_updated_at = self.user.updated_at
        # import time; time.sleep(0.01) # Ensure time difference
        # self.user.username = 'testuser_updated'
        # self.user.save()
        # self.user.refresh_from_db()
        # self.assertTrue(self.user.updated_at > old_updated_at) # This might be flaky in some test runners/DBs
        # A more reliable way is to check it's different if the save actually happened.
        # For now, existence is sufficient for this basic test.

# If using Django's default User model or a custom one derived from AbstractUser:
# class DjangoUserModelTests(TestCase):
#     def test_create_user(self):
#         User = get_user_model()
#         user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
#         self.assertEqual(user.username, 'testuser')
#         self.assertTrue(user.check_password('password123'))
#         self.assertFalse(user.is_staff)
#         self.assertFalse(user.is_superuser)

#     def test_create_superuser(self):
#         User = get_user_model()
#         admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password123')
#         self.assertTrue(admin_user.is_staff)
#         self.assertTrue(admin_user.is_superuser)
