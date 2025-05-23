from django.test import TestCase
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.transactions.models import PaymentTransaction
from apps.orders.services.batch_service import create_payment_batches_for_orders, MAX_ORDERS_PER_BATCH
from apps.orders.services import alipay_service # To mock its functions
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class BatchServiceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='batchservicetestuser', 
            email='batchservice@example.com', 
            password_hash=make_password('testpass123')
        )
        # Create some PENDING orders for this user
        cls.pending_orders = []
        for i in range(5): # Create 5 pending orders
            order = Order.objects.create(
                user=cls.user, 
                amount=Decimal(f'10.{i:02d}'), 
                status='PENDING',
                product_description=f'Test Order {i+1}'
            )
            cls.pending_orders.append(order)

        cls.other_user = User.objects.create(
            username='otheruserbatch', 
            email='otheruserbatch@example.com', 
            password_hash=make_password('testpass')
        )
        cls.other_user_order = Order.objects.create(
            user=cls.other_user, amount=Decimal('5.00'), status='PENDING'
        )
        cls.processed_order = Order.objects.create(
            user=cls.user, amount=Decimal('1.00'), status='SUCCESS' # Not PENDING
        )
        cls.batched_order = Order.objects.create(
            user=cls.user, amount=Decimal('2.00'), status='PENDING' # Will be put in a batch
        )
        existing_batch = PaymentBatch.objects.create(created_by_user=cls.user, total_amount='2.00', total_orders=1)
        cls.batched_order.payment_batch = existing_batch
        cls.batched_order.save()


    def test_create_payment_batches_single_batch(self):
        """Test creating a single batch with a few orders."""
        order_ids_to_batch = [self.pending_orders[0].id, self.pending_orders[1].id]
        
        created_batches = create_payment_batches_for_orders(self.user, order_ids_to_batch)
        
        self.assertEqual(len(created_batches), 1)
        batch = created_batches[0]
        self.assertEqual(batch.total_orders, 2)
        self.assertEqual(batch.created_by_user, self.user)
        expected_total_amount = self.pending_orders[0].amount + self.pending_orders[1].amount
        self.assertEqual(batch.total_amount, expected_total_amount)
        
        # Verify orders are updated
        for order_id in order_ids_to_batch:
            order = Order.objects.get(id=order_id)
            self.assertEqual(order.payment_batch, batch)
            self.assertEqual(order.status, 'PROCESSING') # As per service logic

    def test_create_payment_batches_multiple_batches_due_to_size_limit(self):
        """Test creating multiple batches if order count exceeds MAX_ORDERS_PER_BATCH."""
        # Temporarily reduce MAX_ORDERS_PER_BATCH for this test
        original_max_orders = MAX_ORDERS_PER_BATCH
        # from apps.orders.services import batch_service # Re-import for patching module variable
        # with patch('apps.orders.services.batch_service.MAX_ORDERS_PER_BATCH', 2):
        # For simplicity, we'll use a number of orders that naturally splits.
        # Create enough orders to ensure splitting based on current MAX_ORDERS_PER_BATCH (2000)
        # This test would be very slow if we actually create 2001 orders.
        # So, we'll mock MAX_ORDERS_PER_BATCH or test the logic conceptually.
        # Let's test with a smaller set and assume the chunking logic is sound.
        
        # If MAX_ORDERS_PER_BATCH is 2, and we pass 3 orders:
        with patch('apps.orders.services.batch_service.MAX_ORDERS_PER_BATCH', 2):
            order_ids_to_batch = [
                self.pending_orders[0].id, 
                self.pending_orders[1].id, 
                self.pending_orders[2].id
            ]
            created_batches = create_payment_batches_for_orders(self.user, order_ids_to_batch)
            self.assertEqual(len(created_batches), 2) # Should create two batches
            self.assertEqual(created_batches[0].total_orders, 2)
            self.assertEqual(created_batches[1].total_orders, 1)

    def test_create_payment_batches_no_order_ids(self):
        """Test ValueError is raised if no order IDs are provided."""
        with self.assertRaisesRegex(ValueError, "Order IDs list cannot be empty."):
            create_payment_batches_for_orders(self.user, [])

    def test_create_payment_batches_no_valid_orders_found(self):
        """Test ValueError if no valid (PENDING, unbatched, user-owned) orders found."""
        with self.assertRaisesRegex(ValueError, "No valid orders found to batch."):
            create_payment_batches_for_orders(self.user, [self.processed_order.id])

    def test_create_payment_batches_invalid_order_ids(self):
        """Test ValueError for orders not meeting criteria (wrong user, status, already batched)."""
        # Order belonging to another user
        with self.assertRaises(ValueError): # Regex might be too specific due to dynamic invalid_ids
            create_payment_batches_for_orders(self.user, [self.other_user_order.id])
        # Order already processed
        with self.assertRaises(ValueError):
            create_payment_batches_for_orders(self.user, [self.processed_order.id])
        # Order already in another batch
        with self.assertRaises(ValueError):
            create_payment_batches_for_orders(self.user, [self.batched_order.id])
        # Non-existent order ID
        with self.assertRaises(ValueError):
            create_payment_batches_for_orders(self.user, [99999]) # Assuming 99999 doesn't exist


class AlipayServiceTests(TestCase):
    # These tests will mock external interactions with Alipay

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='alipaysvcuser', email='alipaysvc@example.com', password_hash=make_password('test'))
        cls.order = Order.objects.create(user=cls.user, amount='10.00', order_uid=uuid.uuid4())
        cls.batch = PaymentBatch.objects.create(created_by_user=cls.user, total_amount='10.00', total_orders=1, batch_uid=uuid.uuid4())
        cls.order.payment_batch = cls.batch
        cls.order.save()

    @patch('apps.orders.services.alipay_service.random.random') # Mock random for predictable success/failure
    def test_initiate_payment_for_order_simulated_success(self, mock_random):
        """Test simulate individual order payment success."""
        mock_random.return_value = 0.5 # Ensures success (random < 0.9)
        response = alipay_service.initiate_payment_for_order(self.order)
        self.assertTrue(response['success'])
        self.assertIn('alipay_trade_no', response)
        self.assertIsNotNone(response['alipay_trade_no'])

    @patch('apps.orders.services.alipay_service.random.random')
    def test_initiate_payment_for_order_simulated_failure(self, mock_random):
        """Test simulate individual order payment failure."""
        mock_random.return_value = 0.95 # Ensures failure (random >= 0.9)
        response = alipay_service.initiate_payment_for_order(self.order)
        self.assertFalse(response['success'])
        self.assertIn('error_code', response)
        self.assertIn('error_message', response)

    @patch('apps.orders.services.alipay_service.random.random')
    def test_initiate_batch_payment_to_alipay_simulated_success(self, mock_random):
        """Test simulate batch payment submission success."""
        mock_random.return_value = 0.5 # Ensures success (random < 0.95)
        response = alipay_service.initiate_batch_payment_to_alipay(self.batch)
        self.assertTrue(response['success'])
        self.assertIn('alipay_batch_no', response)

    @patch('apps.orders.services.alipay_service.random.random')
    def test_initiate_batch_payment_to_alipay_simulated_failure(self, mock_random):
        """Test simulate batch payment submission failure."""
        mock_random.return_value = 0.98 # Ensures failure (random >= 0.95)
        response = alipay_service.initiate_batch_payment_to_alipay(self.batch)
        self.assertFalse(response['success'])
        self.assertIn('error_code', response)

    def test_verify_and_process_notification_single_order_success(self):
        """Test processing a successful single order notification."""
        # This is a simplified notification data
        notification_data = {
            'out_trade_no': str(self.order.order_uid),
            'trade_no': 'ALIPAY_TRANS_ID_SINGLE_SUCCESS',
            'trade_status': 'TRADE_SUCCESS',
            'sign': 'mock_signature' # Verification is currently a placeholder in service
        }
        self.order.status = 'PROCESSING' # Assume order was processing
        self.order.save()
        
        result = alipay_service.verify_and_process_notification(notification_data)
        
        self.assertTrue(result['processed'])
        self.assertEqual(result.get('updated_orders', 0), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'SUCCESS')
        self.assertEqual(self.order.alipay_trade_no, 'ALIPAY_TRANS_ID_SINGLE_SUCCESS')
        self.assertTrue(PaymentTransaction.objects.filter(order=self.order, status='SUCCESS').exists())

    def test_verify_and_process_notification_batch_detailed_success(self):
        """Test processing a successful batch notification with per-order details."""
        self.order.status = 'PROCESSING'
        self.order.save()
        self.batch.status = 'PROCESSING'
        self.batch.save()

        notification_data = {
            'out_batch_no': str(self.batch.batch_uid),
            'batch_no': 'ALIPAY_BATCH_TRANS_ID_SUCCESS',
            'success_details': [{
                'out_trade_no': str(self.order.order_uid), 
                'status': 'SUCCESS', # Assuming Alipay uses this, might be different
                'trade_no': 'ALIPAY_ORDER_IN_BATCH_ID'
            }],
            'sign': 'mock_signature_batch_detailed'
        }
        
        result = alipay_service.verify_and_process_notification(notification_data)
        
        self.assertTrue(result['processed'])
        self.assertEqual(result.get('updated_orders', 0), 1)
        self.assertEqual(result.get('updated_batches', 0), 1)
        
        self.order.refresh_from_db()
        self.batch.refresh_from_db()
        
        self.assertEqual(self.order.status, 'SUCCESS')
        self.assertEqual(self.order.alipay_trade_no, 'ALIPAY_ORDER_IN_BATCH_ID')
        self.assertEqual(self.batch.status, 'COMPLETED') # Since all orders in batch (1) are successful
        self.assertEqual(self.batch.successful_orders, 1)
        self.assertTrue(PaymentTransaction.objects.filter(order=self.order, payment_batch=self.batch, status='SUCCESS').exists())

    def test_verify_and_process_notification_invalid_signature(self):
        """Placeholder: Test that invalid signature (if verification was real) is rejected."""
        # To truly test this, alipay_service.verify_and_process_notification would need
        # a mockable signature verification step.
        # For now, it's a conceptual test. If signature verification was implemented and mocked:
        # with patch('apps.orders.services.alipay_service.verify_alipay_signature') as mock_verify:
        # mock_verify.return_value = False
        # notification_data = {'out_trade_no': str(self.order.order_uid), 'trade_status': 'TRADE_SUCCESS'}
        # result = alipay_service.verify_and_process_notification(notification_data)
        # self.assertFalse(result['processed'])
        # self.assertEqual(result['reason'], 'Signature verification failed')
        pass # Current service has placeholder for signature verification

    def test_verify_and_process_notification_order_not_found(self):
        notification_data = {'out_trade_no': str(uuid.uuid4()), 'trade_status': 'TRADE_SUCCESS'}
        result = alipay_service.verify_and_process_notification(notification_data)
        self.assertFalse(result['processed'])
        self.assertTrue("not found" in result.get('reason', '').lower())

# TODO: Add more tests for alipay_service.verify_and_process_notification:
# - Different trade_status values (FAILURE, PENDING, etc.)
# - Batch notifications with overall status vs. detailed per-order status.
# - Notifications for batches/orders not found.
# - Notifications with missing critical data.
