from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.users.models import User # Custom User model
from apps.orders.models import Order, PaymentBatch
from django.contrib.auth.hashers import make_password


class OrderModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='orderuser',
            email='orderuser@example.com',
            password_hash=make_password('testpass123')
        )
        cls.order = Order.objects.create(
            user=cls.user,
            amount=Decimal('100.50'),
            currency='CNY',
            product_description='Test Product'
        )

    def test_order_creation(self):
        """Test that an Order can be created with valid data."""
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.amount, Decimal('100.50'))
        self.assertEqual(self.order.currency, 'CNY')
        self.assertEqual(self.order.status, 'PENDING') # Default status
        self.assertIsNotNone(self.order.order_uid)
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)

    def test_order_str_representation(self):
        """Test the __str__ method of the Order model."""
        expected_str = f"Order {self.order.order_uid} - Amount: {self.order.amount} {self.order.currency} - Status: {self.order.status}"
        self.assertEqual(str(self.order), expected_str)

    def test_order_status_choices(self):
        """Test that status choices are available and default is PENDING."""
        self.assertEqual(self.order.get_status_display(), 'Pending')
        self.order.status = 'SUCCESS'
        self.order.save()
        self.assertEqual(self.order.get_status_display(), 'Success')

    def test_order_currency_default(self):
        """Test currency defaults to CNY if not specified (though our model requires it)."""
        # Model field for currency is not nullable and has a default.
        # If we create without specifying, default should apply.
        order_with_default_currency = Order.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            # currency field has default='CNY', null=False
        )
        self.assertEqual(order_with_default_currency.currency, 'CNY')


class PaymentBatchModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='batchuser',
            email='batchuser@example.com',
            password_hash=make_password('testpass123')
        )
        cls.batch = PaymentBatch.objects.create(
            created_by_user=cls.user,
            total_amount=Decimal('0.00'), # Will be updated by orders
            total_orders=0 # Will be updated by orders
        )
        # Create some orders for the batch
        cls.order1 = Order.objects.create(user=cls.user, amount=Decimal('50.25'), payment_batch=cls.batch)
        cls.order2 = Order.objects.create(user=cls.user, amount=Decimal('100.75'), payment_batch=cls.batch)

        # Simulate updating batch totals (in real app, this might be a method or service)
        cls.batch.total_amount = cls.order1.amount + cls.order2.amount
        cls.batch.total_orders = 2
        cls.batch.save()


    def test_payment_batch_creation(self):
        """Test that a PaymentBatch can be created."""
        self.assertEqual(PaymentBatch.objects.count(), 1)
        self.assertEqual(self.batch.created_by_user, self.user)
        self.assertEqual(self.batch.status, 'PENDING_PROCESSING') # Default status
        self.assertIsNotNone(self.batch.batch_uid)
        self.assertIsNotNone(self.batch.created_at)
        self.assertIsNotNone(self.batch.updated_at)

    def test_payment_batch_str_representation(self):
        """Test the __str__ method of the PaymentBatch model."""
        expected_str = f"Batch {self.batch.batch_uid} - Status: {self.batch.status}"
        self.assertEqual(str(self.batch), expected_str)

    def test_payment_batch_order_relationship(self):
        """Test the relationship between PaymentBatch and Order."""
        self.assertEqual(self.batch.orders.count(), 2)
        self.assertIn(self.order1, self.batch.orders.all())
        self.assertIn(self.order2, self.batch.orders.all())
        self.assertEqual(self.order1.payment_batch, self.batch)

    def test_batch_status_choices(self):
        """Test status choices for PaymentBatch."""
        self.assertEqual(self.batch.get_status_display(), 'Pending Processing')
        self.batch.status = 'COMPLETED'
        self.batch.save()
        self.assertEqual(self.batch.get_status_display(), 'Completed')

    def test_batch_cascade_delete_behavior(self):
        """Test on_delete behavior for created_by_user (PROTECT)."""
        with self.assertRaises(models.ProtectedError): # or IntegrityError depending on DB
            self.user.delete()
        
        # Test on_delete for orders (SET_NULL)
        # If an order is deleted, its payment_batch FK should be set to NULL if nullable.
        # Our Order.payment_batch is on_delete=models.SET_NULL, null=True
        order_id_to_delete = self.order1.id
        self.order1.delete()
        # Re-fetch batch to ensure its state is current
        self.batch.refresh_from_db() 
        # The order should be removed from the batch's related manager
        self.assertEqual(self.batch.orders.count(), 1) 
        # Check if the deleted order now has payment_batch = None
        # This is hard to check directly as the order is gone.
        # The test for SET_NULL is more about ensuring the batch itself is not deleted.
        self.assertTrue(PaymentBatch.objects.filter(id=self.batch.id).exists())
        
        # Test what happens if a batch is deleted - orders' payment_batch field becomes NULL
        self.order2.payment_batch = self.batch # Ensure it's linked
        self.order2.save()
        
        batch_id_to_delete = self.batch.id
        self.batch.delete()
        
        self.order2.refresh_from_db()
        self.assertIsNone(self.order2.payment_batch)
        self.assertFalse(PaymentBatch.objects.filter(id=batch_id_to_delete).exists())

# More tests could include:
# - Validation of fields (e.g. total_amount >= 0) if model has clean() methods or validators.
# - Testing custom model methods if any are added.
# - Testing default values for all fields not explicitly set.
