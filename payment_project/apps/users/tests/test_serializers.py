from django.test import TestCase
from apps.users.serializers import UserSerializer, UserDisplaySerializer
from apps.users.models import User # Using the custom User model
from django.contrib.auth.hashers import check_password

class UserSerializerTests(TestCase):

    def setUp(self):
        self.user_attributes = {
            'username': 'testserializeruser',
            'email': 'serializer@example.com',
            'password': 'securepassword123'
        }
        self.user_data_for_create = {**self.user_attributes}

        # For testing serialization of an existing user instance
        self.user_instance = User.objects.create(
            username='existinguser',
            email='existing@example.com',
            password_hash=UserSerializer().create(self.user_attributes).password_hash # Use serializer's hashing
        )

    def test_user_serializer_create(self):
        """Test UserSerializer can create a new user with hashed password."""
        serializer = UserSerializer(data=self.user_data_for_create)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, self.user_data_for_create['username'])
        self.assertEqual(user.email, self.user_data_for_create['email'])
        self.assertTrue(check_password(self.user_data_for_create['password'], user.password_hash))
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
    
    def test_user_serializer_update(self):
        """Test UserSerializer can update a user, including password."""
        new_username = "updatedusername"
        new_password = "newsecurepassword456"
        data_for_update = {
            'username': new_username,
            'password': new_password
        }
        serializer = UserSerializer(self.user_instance, data=data_for_update, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        self.assertEqual(updated_user.username, new_username)
        self.assertTrue(check_password(new_password, updated_user.password_hash))

    def test_user_serializer_serialization_excludes_password_hash(self):
        """Test UserSerializer output does not include password_hash or password."""
        serializer = UserSerializer(self.user_instance)
        serialized_data = serializer.data

        self.assertIn('id', serialized_data)
        self.assertIn('username', serialized_data)
        self.assertIn('email', serialized_data)
        self.assertNotIn('password', serialized_data) # write_only=True
        self.assertNotIn('password_hash', serialized_data) # Not in Meta.fields for output

    def test_user_serializer_validation_required_fields(self):
        """Test UserSerializer validation for required fields during creation."""
        invalid_data = {} # Missing username, email, password
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)
        self.assertIn('password', serializer.errors)

class UserDisplaySerializerTests(TestCase):

    def setUp(self):
        self.user_instance = User.objects.create(
            username='displayuser',
            email='display@example.com',
            password_hash='somehashedpassword' # Hashing not focus of this serializer test
        )

    def test_user_display_serializer_output(self):
        """Test UserDisplaySerializer includes expected fields and excludes sensitive ones."""
        serializer = UserDisplaySerializer(self.user_instance)
        data = serializer.data

        self.assertEqual(data['username'], self.user_instance.username)
        self.assertEqual(data['email'], self.user_instance.email)
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        
        self.assertNotIn('password', data)
        self.assertNotIn('password_hash', data)

    def test_user_display_serializer_is_read_only(self):
        """Test that UserDisplaySerializer fields are read-only."""
        # Attempting to update using UserDisplaySerializer should ideally not work
        # as all its fields are marked read_only in its Meta.
        # However, DRF allows data to be passed if serializer is not instantiated with read_only=True context.
        # The Meta class read_only_fields ensures that if .save() were called, these fields wouldn't be written.
        data_for_update = {
            'username': 'new_username_via_display_serializer',
            'email': 'new_email@example.com'
        }
        serializer = UserDisplaySerializer(self.user_instance, data=data_for_update, partial=True)
        
        # is_valid() might be true as it doesn't prevent unknown fields by default unless extra_kwargs used.
        # The key is that .save() would not update these if they were truly read-only at field level.
        # For this test, we'll just confirm the output structure again.
        self.assertTrue(serializer.is_valid()) # This will be true
        
        # If we were to call serializer.save(), it would depend on how `read_only_fields` is implemented
        # in the base ModelSerializer. Typically, they are dropped from validated_data.
        # No .save() call here as it's a display serializer.
        
        self.assertIn('username', serializer.validated_data) # Data is validated
        
        # Check output structure again (though this doesn't directly test read_only nature of update)
        output_data = serializer.data
        self.assertEqual(output_data['username'], self.user_instance.username) # Should still be original username as not saved
        self.assertNotEqual(output_data['username'], data_for_update['username']) # Confirming original data in output after "update" attempt
        
        # A better test for read_only would be to check validated_data after is_valid()
        # and ensure that if save() were called, the read_only fields are not present in validated_data
        # or are ignored by the update logic.
        # For UserDisplaySerializer, its purpose is purely for safe data representation.
        # No .save() method should be called on it in practice.
        
        # A more direct test:
        for field_name in UserDisplaySerializer.Meta.fields:
            if field_name in serializer.fields:
                self.assertTrue(serializer.fields[field_name].read_only, f"{field_name} should be read-only")

# TODO: Add tests for unique field validation (username, email) at serializer level if not covered by model tests.
#       This is often implicitly handled by DRF when model field has unique=True.
#       Explicit tests can be added by trying to create/update with existing values.
