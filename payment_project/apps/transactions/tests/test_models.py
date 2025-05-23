from django.test import TestCase
from decimal import Decimal
from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.transactions.models import PaymentTransaction
from django.contrib.auth.hashers import make_password
import uuid

class PaymentTransactionModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='transactionuser',
            email='transactionuser@example.com',
            password_hash=make_password('testpass123')
        )
        cls.order = Order.objects.create(
            user=cls.user,
            amount=Decimal('200.00'),
            currency='EUR'
        )
        cls.batch = PaymentBatch.objects.create(
            created_by_user=cls.user,
            total_amount=cls.order.amount,
            total_orders=1
        )
        # Link order to batch for some tests
        cls.order.payment_batch = cls.batch
        cls.order.save()

        cls.transaction = PaymentTransaction.objects.create(
            order=cls.order,
            payment_batch=cls.batch, # Can be null if order not part of batch
            amount=cls.order.amount,
            currency=cls.order.currency,
            status='INITIATED' # Initial status
        )

    def test_payment_transaction_creation(self):
        """Test that a PaymentTransaction can be created with valid data."""
        self.assertEqual(PaymentTransaction.objects.count(), 1)
        self.assertEqual(self.transaction.order, self.order)
        self.assertEqual(self.transaction.payment_batch, self.batch)
        self.assertEqual(self.transaction.amount, self.order.amount)
        self.assertEqual(self.transaction.currency, self.order.currency)
        self.assertEqual(self.transaction.status, 'INITIATED')
        self.assertIsNotNone(self.transaction.transaction_uid)
        self.assertIsNotNone(self.transaction.created_at)
        self.assertIsNotNone(self.transaction.updated_at)

    def test_payment_transaction_str_representation(self):
        """Test the __str__ method of the PaymentTransaction model."""
        expected_str = f"Transaction {self.transaction.transaction_uid} for Order {self.order.order_uid} - Status: {self.transaction.status}"
        self.assertEqual(str(self.transaction), expected_str)

    def test_transaction_status_choices(self):
        """Test status choices and updates for PaymentTransaction."""
        self.assertEqual(self.transaction.get_status_display(), 'Initiated')
        self.transaction.status = 'SUCCESS'
        self.transaction.save()
        self.assertEqual(self.transaction.get_status_display(), 'Success')
        
        self.transaction.status = 'FAILED'
        self.transaction.error_code = 'ALIPAY_ERR_001'
        self.transaction.error_message = 'User balance insufficient.'
        self.transaction.save()
        self.assertEqual(self.transaction.get_status_display(), 'Failed')
        self.assertEqual(self.transaction.error_code, 'ALIPAY_ERR_001')

    def test_transaction_payload_fields(self):
        """Test JSON fields for request and response payloads."""
        request_data = {'param1': 'value1', 'timestamp': timezone.now().isoformat()}
        response_data = {'success': True, 'trade_no': 'ALIPAY123'}
        
        self.transaction.request_payload = request_data
        self.transaction.response_payload = response_data
        self.transaction.save()
        
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.request_payload['param1'], 'value1')
        self.assertTrue(self.transaction.response_payload['success'])

    def test_transaction_order_cascade_delete(self):
        """Test that deleting an Order cascades to its PaymentTransactions."""
        transaction_id = self.transaction.id
        self.order.delete()
        with self.assertRaises(PaymentTransaction.DoesNotExist):
            PaymentTransaction.objects.get(id=transaction_id)
            
    def test_transaction_batch_set_null_on_delete(self):
        """Test that deleting a PaymentBatch sets payment_batch to NULL on transactions."""
        # Recreate transaction for this specific test to avoid interference
        order = Order.objects.create(user=self.user, amount='10.00')
        batch_to_delete = PaymentBatch.objects.create(created_by_user=self.user, total_amount='10.00', total_orders=1)
        order.payment_batch = batch_to_delete
        order.save()
        transaction_with_batch = PaymentTransaction.objects.create(
            order=order, payment_batch=batch_to_delete, amount='10.00', currency='USD', status='PENDING'
        )
        
        batch_to_delete.delete()
        transaction_with_batch.refresh_from_db()
        self.assertIsNone(transaction_with_batch.payment_batch)


# More tests could include:
# - Ensuring transaction_uid is unique (though default=uuid.uuid4 handles this well).
# - Testing behavior if Order is deleted (should cascade and delete transactions).
# - Testing behavior if PaymentBatch is deleted (should set payment_batch to NULL).
# - Validations if any custom `clean` methods or validators are added to the model.
