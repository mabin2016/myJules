from django.test import TestCase
from unittest.mock import patch, MagicMock, call
from decimal import Decimal
from django.utils import timezone

from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.transactions.models import PaymentTransaction
from apps.orders.tasks import process_batch_payment_task, handle_alipay_notification_task
from django.contrib.auth.hashers import make_password
import uuid

class CeleryTaskTests(TestCase):
    # Note: For more in-depth Celery task testing, especially with retries and state,
    # you might use celery.contrib.testing.worker or similar utilities.
    # These tests will primarily mock service dependencies and check outcomes.

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='taskuser', 
            email='taskuser@example.com', 
            password_hash=make_password('testpass')
        )
        cls.batch = PaymentBatch.objects.create(
            created_by_user=cls.user,
            total_amount=Decimal('150.00'),
            total_orders=2,
            status='PENDING_PROCESSING' # Initial state for processing
        )
        cls.order1 = Order.objects.create(user=cls.user, payment_batch=cls.batch, amount=Decimal('50.00'), status='PENDING')
        cls.order2 = Order.objects.create(user=cls.user, payment_batch=cls.batch, amount=Decimal('100.00'), status='PENDING')

    @patch('apps.orders.services.alipay_service.initiate_batch_payment_to_alipay')
    @patch('apps.orders.services.alipay_service.initiate_payment_for_order')
    def test_process_batch_payment_task_full_success(self, mock_initiate_payment_for_order, mock_initiate_batch_payment):
        """Test process_batch_payment_task where all orders succeed."""
        
        # Mock Alipay service responses
        mock_initiate_batch_payment.return_value = {
            "success": True,
            "alipay_batch_no": "mock_alipay_batch_no_123",
            "message": "Batch submission successful."
        }
        # Simulate individual order payments all succeeding
        mock_initiate_payment_for_order.side_effect = [
            {"success": True, "alipay_trade_no": "mock_trade_no_o1", "order_uid": str(self.order1.order_uid)},
            {"success": True, "alipay_trade_no": "mock_trade_no_o2", "order_uid": str(self.order2.order_uid)},
        ]

        # Create a mock task instance to pass `self` if `bind=True`
        mock_celery_task_self = MagicMock()
        mock_celery_task_self.request.id = "mock_task_id_success"
        mock_celery_task_self.update_state = MagicMock()

        # Execute the task directly
        result_message = process_batch_payment_task.run(mock_celery_task_self, self.batch.id) # Use .run() for direct execution in tests if needed
        # Or process_batch_payment_task(self.batch.id) if not using bind=True features heavily in mocked logic

        self.batch.refresh_from_db()
        self.order1.refresh_from_db()
        self.order2.refresh_from_db()

        self.assertEqual(self.batch.status, 'COMPLETED')
        self.assertEqual(self.batch.successful_orders, 2)
        self.assertEqual(self.batch.failed_orders, 0)
        self.assertEqual(self.batch.processed_orders, 2)
        self.assertEqual(self.batch.alipay_batch_no, "mock_alipay_batch_no_123")
        self.assertIsNotNone(self.batch.completed_at)

        self.assertEqual(self.order1.status, 'SUCCESS')
        self.assertEqual(self.order1.alipay_trade_no, "mock_trade_no_o1")
        self.assertEqual(self.order2.status, 'SUCCESS')
        self.assertEqual(self.order2.alipay_trade_no, "mock_trade_no_o2")

        self.assertEqual(PaymentTransaction.objects.filter(payment_batch=self.batch, status='SUCCESS').count(), 2)
        self.assertTrue("processing complete. Status: COMPLETED" in result_message)
        # Check if update_state was called appropriately
        mock_celery_task_self.update_state.assert_any_call(state='PROGRESS', meta={'batch_id': self.batch.id, 'status': 'Fetching batch details'})
        mock_celery_task_self.update_state.assert_any_call(state='SUCCESS', meta={'batch_id': self.batch.id, 'result': result_message, 'status': 'COMPLETED'})


    @patch('apps.orders.services.alipay_service.initiate_batch_payment_to_alipay')
    @patch('apps.orders.services.alipay_service.initiate_payment_for_order')
    def test_process_batch_payment_task_partial_success(self, mock_initiate_payment_for_order, mock_initiate_batch_payment):
        """Test process_batch_payment_task where one order fails."""
        mock_initiate_batch_payment.return_value = {"success": True, "alipay_batch_no": "mock_alipay_batch_no_456"}
        mock_initiate_payment_for_order.side_effect = [
            {"success": True, "alipay_trade_no": "mock_trade_no_o1_partial", "order_uid": str(self.order1.order_uid)},
            {"success": False, "error_message": "Insufficient funds", "error_code": "INSUFFICIENT_FUNDS", "order_uid": str(self.order2.order_uid)},
        ]
        
        mock_celery_task_self = MagicMock()
        mock_celery_task_self.request.id = "mock_task_id_partial"
        mock_celery_task_self.update_state = MagicMock()

        result_message = process_batch_payment_task.run(mock_celery_task_self, self.batch.id)

        self.batch.refresh_from_db()
        self.order1.refresh_from_db()
        self.order2.refresh_from_db()

        self.assertEqual(self.batch.status, 'PARTIALLY_COMPLETED')
        self.assertEqual(self.batch.successful_orders, 1)
        self.assertEqual(self.batch.failed_orders, 1)
        self.assertEqual(self.batch.processed_orders, 2)
        self.assertEqual(self.order1.status, 'SUCCESS')
        self.assertEqual(self.order2.status, 'FAILED')
        self.assertEqual(self.order2.error_message, "Insufficient funds")
        
        self.assertEqual(PaymentTransaction.objects.filter(payment_batch=self.batch, status='SUCCESS').count(), 1)
        self.assertEqual(PaymentTransaction.objects.filter(payment_batch=self.batch, status='FAILED').count(), 1)
        self.assertTrue("Status: PARTIALLY_COMPLETED" in result_message)
        mock_celery_task_self.update_state.assert_called_with(state='SUCCESS', meta={'batch_id': self.batch.id, 'result': result_message, 'status': 'PARTIALLY_COMPLETED'})


    @patch('apps.orders.services.alipay_service.initiate_batch_payment_to_alipay')
    def test_process_batch_payment_task_batch_submission_failure(self, mock_initiate_batch_payment):
        """Test scenario where the initial batch submission to Alipay fails."""
        mock_initiate_batch_payment.return_value = {
            "success": False, 
            "error_message": "Alipay system error",
            "error_code": "ALIPAY_SYSTEM_ERROR"
        }
        
        mock_celery_task_self = MagicMock()
        mock_celery_task_self.request.id = "mock_task_id_batch_fail"
        mock_celery_task_self.update_state = MagicMock()

        result_message = process_batch_payment_task.run(mock_celery_task_self, self.batch.id)

        self.batch.refresh_from_db()
        self.order1.refresh_from_db() # Orders should also be marked FAILED
        self.order2.refresh_from_db()

        self.assertEqual(self.batch.status, 'FAILED')
        self.assertEqual(self.batch.error_message, "Alipay system error")
        self.assertEqual(self.order1.status, 'FAILED')
        self.assertEqual(self.order2.status, 'FAILED')
        self.assertTrue("Alipay batch submission failed" in result_message)
        # No update_state to SUCCESS in this case for the task itself, as it returns early

    def test_process_batch_payment_task_batch_not_found(self):
        """Test task behavior when batch ID does not exist."""
        mock_celery_task_self = MagicMock()
        mock_celery_task_self.request.id = "mock_task_id_not_found"
        mock_celery_task_self.update_state = MagicMock()
        
        non_existent_batch_id = 99999
        with self.assertRaises(PaymentBatch.DoesNotExist): # Task re-raises this
            process_batch_payment_task.run(mock_celery_task_self, non_existent_batch_id)


    @patch('apps.orders.services.alipay_service.verify_and_process_notification')
    def test_handle_alipay_notification_task_success(self, mock_verify_and_process):
        """Test handle_alipay_notification_task successfully processes a notification."""
        mock_notification_data = {'trade_no': 'some_alipay_trade_id', 'status': 'TRADE_SUCCESS'}
        mock_verify_and_process.return_value = {"processed": True, "updated_orders": 1, "updated_batches": 0}
        
        mock_celery_task_self = MagicMock()
        mock_celery_task_self.request.id = "mock_task_id_notify_success"
        mock_celery_task_self.update_state = MagicMock()

        result = handle_alipay_notification_task.run(mock_celery_task_self, mock_notification_data)

        mock_verify_and_process.assert_called_once_with(mock_notification_data)
        self.assertTrue("Notification processed. Updates: Orders - 1" in result)
        mock_celery_task_self.update_state.assert_called_with(state='SUCCESS', meta={'result': mock_verify_and_process.return_value})


    @patch('apps.orders.services.alipay_service.verify_and_process_notification')
    def test_handle_alipay_notification_task_processing_failure(self, mock_verify_and_process):
        """Test handle_alipay_notification_task when service reports processing failure."""
        mock_notification_data = {'trade_no': 'failed_trade_id', 'status': 'SYSTEM_ERROR'}
        mock_verify_and_process.return_value = {"processed": False, "reason": "Signature mismatch"}

        mock_celery_task_self = MagicMock()
        mock_celery_task_self.request.id = "mock_task_id_notify_fail"
        mock_celery_task_self.update_state = MagicMock()

        with self.assertRaisesRegex(Exception, "Notification processing failed: Signature mismatch"):
            handle_alipay_notification_task.run(mock_celery_task_self, mock_notification_data)
        
        mock_verify_and_process.assert_called_once_with(mock_notification_data)
        # Check that update_state was called for PROGRESS but not SUCCESS
        mock_celery_task_self.update_state.assert_any_call(state='PROGRESS', meta={'status': 'Processing notification'})
        
        # Ensure SUCCESS state was not called by checking call_args_list
        success_state_call = call(state='SUCCESS', meta={'result': mock_verify_and_process.return_value})
        self.assertNotIn(success_state_call, mock_celery_task_self.update_state.call_args_list)


# TODO: More tests for edge cases in tasks:
# - Batch status not allowing processing.
# - Retries (this requires more advanced Celery testing setup like TaskTestMixin or celery.contrib.testing.worker).
# - Idempotency tests for notification handling if applicable.
