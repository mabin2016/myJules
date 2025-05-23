from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.transactions.models import PaymentTransaction
from django.contrib.auth.hashers import make_password
from decimal import Decimal

class PaymentTransactionViewSetTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='transviewuser', 
            email='transview@example.com', 
            password_hash=make_password('testpass123')
        )
        cls.admin_user = User.objects.create( # To test admin access
            username='adminuser_trans', 
            email='admintrans@example.com', 
            password_hash=make_password('adminpass'),
            # For a real admin, you'd set is_staff=True if using Django's User model
            # Our custom User model doesn't have is_staff. View logic checks for it though.
            # We'll simulate is_staff in the test by patching or by having different querysets.
        )

        cls.order1 = Order.objects.create(user=cls.user, amount=Decimal('100.00'))
        cls.transaction1 = PaymentTransaction.objects.create(order=cls.order1, amount=cls.order1.amount, currency='USD', status='SUCCESS')
        
        cls.order2 = Order.objects.create(user=cls.user, amount=Decimal('200.00'))
        cls.transaction2 = PaymentTransaction.objects.create(order=cls.order2, amount=cls.order2.amount, currency='USD', status='FAILED')

        # Transaction for another user
        cls.other_user = User.objects.create(username='otherusertrans', email='othertrans@example.com', password_hash=make_password('pass'))
        cls.other_user_order = Order.objects.create(user=cls.other_user, amount=Decimal('50.00'))
        cls.other_user_transaction = PaymentTransaction.objects.create(order=cls.other_user_order, amount='50.00', currency='EUR', status='SUCCESS')
        
        cls.list_url = reverse('paymenttransaction-list') # Default DRF naming

    def setUp(self):
        # Default to authenticating as the regular user
        self.client.force_authenticate(user=self.user)

    def test_list_transactions_for_authenticated_user(self):
        """Test that authenticated user can only see their own transactions."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2) # transaction1 and transaction2 for self.user
        
        transaction_ids_in_response = {t['id'] for t in results}
        self.assertIn(self.transaction1.id, transaction_ids_in_response)
        self.assertIn(self.transaction2.id, transaction_ids_in_response)
        self.assertNotIn(self.other_user_transaction.id, transaction_ids_in_response)

    def test_retrieve_transaction_for_authenticated_user(self):
        """Test retrieving a specific transaction belonging to the user."""
        detail_url = reverse('paymenttransaction-detail', kwargs={'pk': self.transaction1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.transaction1.id)

    def test_retrieve_transaction_forbidden_for_other_user(self):
        """Test retrieving a transaction not belonging to the user returns 404."""
        detail_url = reverse('paymenttransaction-detail', kwargs={'pk': self.other_user_transaction.pk})
        response = self.client.get(detail_url)
        # ViewSet filters by user, so it will be a 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_transactions_as_admin_user(self):
        """Test that an admin user (simulated by is_staff) can see all transactions."""
        # Simulate admin user by setting is_staff attribute (if User model supported it directly)
        # For custom User model, the view logic `if user.is_staff:` needs careful testing.
        # We can patch the user object in the request or adjust the test user.
        # For this test, let's assume self.admin_user is recognized as staff by the view logic.
        # A simple way: make our custom User model have an `is_staff` field for testing this.
        # If not, this test relies on how `user.is_staff` is evaluated for our custom User model.
        # Let's assume our custom User model has an `is_staff` field for this test to be meaningful.
        
        # Add is_staff to our custom User model for testing purposes if it's not there
        if not hasattr(User, 'is_staff'):
            User.add_to_class('is_staff', models.BooleanField(default=False))
        
        self.admin_user.is_staff = True # Simulate staff user
        self.admin_user.save() # Save if 'is_staff' was dynamically added and needs saving
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Admin should see all transactions (transaction1, transaction2, other_user_transaction)
        self.assertEqual(len(results), 3) 
        
        # Clean up added field if it was dynamically added for test
        if hasattr(User, '_meta') and 'is_staff' in [f.name for f in User._meta.local_fields if f.name == 'is_staff']:
             # This is a bit hacky for a test; ideally the model supports is_staff or use mocks
             pass


    def test_list_transactions_unauthenticated(self):
        """Test listing transactions fails if not authenticated."""
        self.client.logout() # Or self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # Or 403 if default is AllowAny

    # PaymentTransactionViewSet is ReadOnly, so no POST/PUT/DELETE tests are needed.

# Note: The admin test (`test_list_transactions_as_admin_user`) assumes that `user.is_staff`
# can be set and used by the view. If your custom User model doesn't have `is_staff`,
# you might need to mock the `request.user.is_staff` property within the view for this test
# or adjust the User model to include it for more realistic admin permission testing.
# For simplicity, the test attempts to set it directly, which might only work if the model field exists.
# A more robust way would be to use Django's permission system or groups if `is_staff` is not on the custom User.
