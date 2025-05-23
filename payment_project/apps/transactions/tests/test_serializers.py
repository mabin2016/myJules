from django.test import TestCase
from decimal import Decimal
from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.transactions.models import PaymentTransaction
from apps.transactions.serializers import PaymentTransactionSerializer
from django.contrib.auth.hashers import make_password
import uuid

class PaymentTransactionSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='transerializeruser', 
            email='transerializer@example.com', 
            password_hash=make_password('testpass')
        )
        cls.order = Order.objects.create(
            user=cls.user, 
            amount=Decimal('300.00'), 
            order_uid=uuid.uuid4() # Ensure order_uid is set for source field in serializer
        )
        cls.batch = PaymentBatch.objects.create(
            created_by_user=cls.user, 
            total_amount='300.00', 
            total_orders=1, 
            batch_uid=uuid.uuid4() # Ensure batch_uid is set for source field
        )
        cls.order.payment_batch = cls.batch
        cls.order.save()

        cls.transaction_instance = PaymentTransaction.objects.create(
            order=cls.order,
            payment_batch=cls.batch,
            amount=cls.order.amount,
            currency=cls.order.currency,
            status='SUCCESS',
            alipay_trade_no='ALIPAY_SERIALIZER_TEST_NO',
            transaction_uid=uuid.uuid4() # Ensure transaction_uid is set
        )

    def test_payment_transaction_serializer_serialization(self):
        """Test PaymentTransactionSerializer can serialize a PaymentTransaction instance."""
        serializer = PaymentTransactionSerializer(instance=self.transaction_instance)
        data = serializer.data

        self.assertEqual(data['transaction_uid'], str(self.transaction_instance.transaction_uid))
        self.assertEqual(Decimal(data['amount']), self.transaction_instance.amount) # Serializer may output as string
        self.assertEqual(data['currency'], self.transaction_instance.currency)
        self.assertEqual(data['status'], self.transaction_instance.status)
        self.assertEqual(data['alipay_trade_no'], self.transaction_instance.alipay_trade_no)
        
        # Test custom source fields for UIDs
        self.assertEqual(data['order_uid'], str(self.order.order_uid))
        self.assertEqual(data['payment_batch_uid'], str(self.batch.batch_uid))
        
        # Ensure raw FK IDs are popped by to_representation
        self.assertNotIn('order', data)
        self.assertNotIn('payment_batch', data)

        # Check if payload fields are present (even if null/empty in this test instance)
        self.assertIn('request_payload', data)
        self.assertIn('response_payload', data)
        self.assertIn('error_code', data)
        self.assertIn('error_message', data)

    def test_payment_transaction_serializer_read_only_fields(self):
        """Test that read_only fields are indeed read-only."""
        # The serializer is ReadOnlyModelViewSet by default in its view,
        # but the serializer itself can be checked for field attributes.
        serializer_fields = PaymentTransactionSerializer().get_fields()
        
        # Check some key fields that should be read_only as per serializer Meta
        # Note: 'order' and 'payment_batch' are not in `fields` due to `to_representation` pop,
        # but their source fields `order_uid` and `payment_batch_uid` are.
        # The PrimaryKeyRelatedFields for 'order' and 'payment_batch' (if used for write) are not tested here
        # as this serializer is primarily for read operations.
        
        expected_read_only_fields_in_output = [
            'id', 'transaction_uid', 'order_uid', 'payment_batch_uid',
            'alipay_trade_no', 'amount', 'currency', 'status',
            'request_payload', 'response_payload', 'error_code', 'error_message',
            'created_at', 'updated_at'
        ]

        for field_name in expected_read_only_fields_in_output:
            if field_name in serializer_fields: # Some might be properties/methods if not careful
                self.assertTrue(serializer_fields[field_name].read_only, f"Field {field_name} should be read-only.")

    def test_serialization_of_transaction_without_batch(self):
        """Test serialization when a transaction is not linked to a batch."""
        order_no_batch = Order.objects.create(user=self.user, amount='50.00', order_uid=uuid.uuid4())
        transaction_no_batch = PaymentTransaction.objects.create(
            order=order_no_batch,
            payment_batch=None, # Explicitly None
            amount=order_no_batch.amount,
            currency=order_no_batch.currency,
            status='INITIATED',
            transaction_uid=uuid.uuid4()
        )
        serializer = PaymentTransactionSerializer(instance=transaction_no_batch)
        data = serializer.data
        
        self.assertIsNone(data['payment_batch_uid']) # payment_batch_uid should be None
        self.assertEqual(data['order_uid'], str(order_no_batch.order_uid))


# If this serializer were to be used for creation (it's not, typically):
# def test_payment_transaction_serializer_create(self):
#     create_data = {
#         'order': self.order.id, 
#         'payment_batch': self.batch.id,
#         'amount': '50.00',
#         'currency': 'USD',
#         'status': 'INITIATED',
#         # transaction_uid is default, alipay_trade_no is nullable
#     }
#     serializer = PaymentTransactionSerializer(data=create_data)
#     self.assertTrue(serializer.is_valid(), serializer.errors)
#     transaction = serializer.save()
#     self.assertIsInstance(transaction, PaymentTransaction)
#     self.assertEqual(transaction.order, self.order)
#     self.assertEqual(transaction.status, 'INITIATED')
#     self.assertEqual(transaction.amount, Decimal('50.00'))
