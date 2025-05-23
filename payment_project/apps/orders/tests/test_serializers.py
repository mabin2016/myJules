from django.test import TestCase
from decimal import Decimal
from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.orders.serializers import (
    OrderSerializer,
    PaymentBatchSerializer,
    PaymentBatchCreateSerializer
)
from django.contrib.auth.hashers import make_password

class OrderSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='orderowner', 
            email='owner@example.com', 
            password_hash=make_password('testpass')
        )
        cls.order_data = {
            'user': cls.user, # Serializer will use user from context or request for create
            'amount': Decimal('199.99'),
            'currency': 'USD',
            'product_description': 'A Fine Product'
        }
        cls.order_instance = Order.objects.create(**cls.order_data)

    def test_order_serializer_serialization(self):
        """Test OrderSerializer can serialize an Order instance."""
        serializer = OrderSerializer(instance=self.order_instance)
        data = serializer.data
        self.assertEqual(data['order_uid'], str(self.order_instance.order_uid))
        self.assertEqual(Decimal(data['amount']), self.order_instance.amount)
        self.assertEqual(data['currency'], self.order_instance.currency)
        self.assertEqual(data['status'], self.order_instance.status)
        self.assertEqual(data['user']['id'], self.user.id) # Nested UserDisplaySerializer

    def test_order_serializer_create_valid_data(self):
        """Test OrderSerializer can create an order with valid data."""
        # User is typically set in the view from request.user, not passed directly in serializer data for creation
        valid_data_for_create = {
            'amount': '250.00',
            'currency': 'EUR',
            'product_description': 'Another Great Product'
        }
        # To simulate view context providing user:
        serializer = OrderSerializer(data=valid_data_for_create)
        # serializer.context['request'] = type('Request', (), {'user': self.user}) # Mock request if needed

        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Manually add user as perform_create in view would
        order = serializer.save(user=self.user) 
        
        self.assertIsInstance(order, Order)
        self.assertEqual(order.amount, Decimal('250.00'))
        self.assertEqual(order.user, self.user)

    def test_order_serializer_read_only_fields(self):
        """Test that read_only fields are not accepted during creation/update."""
        read_only_data = {
            'amount': '10.00', 'currency': 'JPY',
            'order_uid': 'some_custom_uid_should_be_ignored', # read_only
            'status': 'SUCCESS', # read_only
        }
        serializer = OrderSerializer(data=read_only_data)
        self.assertTrue(serializer.is_valid()) # order_uid and status are not input fields
        
        # Check validated_data does not contain read_only fields if they were passed
        self.assertNotIn('order_uid', serializer.validated_data)
        self.assertNotIn('status', serializer.validated_data)


class PaymentBatchCreateSerializerTests(TestCase):

    def test_payment_batch_create_serializer_valid_data(self):
        """Test PaymentBatchCreateSerializer with valid list of order IDs."""
        data = {'order_ids': [1, 2, 3]}
        serializer = PaymentBatchCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['order_ids'], [1, 2, 3])

    def test_payment_batch_create_serializer_empty_order_ids(self):
        """Test validation fails if order_ids list is empty."""
        data = {'order_ids': []}
        serializer = PaymentBatchCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order_ids', serializer.errors)

    def test_payment_batch_create_serializer_duplicate_order_ids(self):
        """Test validation fails if order_ids list has duplicates."""
        data = {'order_ids': [1, 2, 2, 3]}
        serializer = PaymentBatchCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order_ids', serializer.errors) # Custom validator should catch this
        self.assertTrue('Duplicate order_ids are not allowed.' in str(serializer.errors['order_ids']))


class PaymentBatchSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='batchowner', 
            email='batchowner@example.com', 
            password_hash=make_password('testpass')
        )
        cls.batch_instance = PaymentBatch.objects.create(
            created_by_user=cls.user,
            total_amount=Decimal('150.00'),
            total_orders=2
        )
        cls.order1 = Order.objects.create(user=cls.user, amount=Decimal('50.00'), payment_batch=cls.batch_instance)
        cls.order2 = Order.objects.create(user=cls.user, amount=Decimal('100.00'), payment_batch=cls.batch_instance)

    def test_payment_batch_serializer_serialization(self):
        """Test PaymentBatchSerializer serializes a PaymentBatch instance including nested orders."""
        serializer = PaymentBatchSerializer(instance=self.batch_instance)
        data = serializer.data

        self.assertEqual(data['batch_uid'], str(self.batch_instance.batch_uid))
        self.assertEqual(Decimal(data['total_amount']), self.batch_instance.total_amount)
        self.assertEqual(data['total_orders'], self.batch_instance.total_orders)
        self.assertEqual(data['status'], self.batch_instance.status)
        self.assertEqual(data['created_by_user']['id'], self.user.id)
        
        self.assertIn('orders', data)
        self.assertEqual(len(data['orders']), 2)
        order_uids_in_serializer = {o['order_uid'] for o in data['orders']}
        expected_order_uids = {str(self.order1.order_uid), str(self.order2.order_uid)}
        self.assertEqual(order_uids_in_serializer, expected_order_uids)

    def test_payment_batch_serializer_is_read_only(self):
        """Test that PaymentBatchSerializer is primarily read-only for its fields."""
        # The PaymentBatchSerializer is designed for display, not creation.
        # Creation is handled by PaymentBatchCreateSerializer and service logic.
        # We can check if fields are marked as read_only.
        serializer = PaymentBatchSerializer() # Instance without data for field inspection
        for field_name in PaymentBatchSerializer.Meta.read_only_fields:
            if field_name in serializer.fields: # some fields might be methods or properties
                 self.assertTrue(serializer.fields[field_name].read_only, f"Field {field_name} should be read-only.")

# TODO: Add tests for OrderSerializer when user_id is passed for write operations.
# TODO: Add more specific validation tests for all serializers if complex rules exist.
