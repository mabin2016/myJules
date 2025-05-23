from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch # For mocking Celery tasks

from apps.users.models import User
from apps.orders.models import Order, PaymentBatch
from apps.orders.serializers import OrderSerializer, PaymentBatchSerializer # For response data comparison
from django.contrib.auth.hashers import make_password
from decimal import Decimal

class OrderViewSetTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='testorderviewuser', 
            email='testorderview@example.com', 
            password_hash=make_password('testpass123')
        )
        # For DRF APITestCase, it's often better to simulate login via client.force_authenticate
        # or by setting token if using token auth. For simplicity, if your views use IsAuthenticated,
        # ensure the client is authenticated before making requests.

    def setUp(self):
        # Authenticate the client for each test method
        self.client.force_authenticate(user=self.user)
        # Or if using token auth (e.g. SimpleJWT, assuming you have a token endpoint)
        # Replace with actual token obtaining logic if not using force_authenticate
        # response = self.client.post(reverse('token_obtain_pair'), {'username': 'testorderviewuser', 'password': 'testpass123'})
        # token = response.data['access']
        # self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.list_create_url = reverse('order-list') # Default DRF naming

    def test_create_order_success(self):
        """Test creating an order successfully."""
        order_data = {
            'amount': '123.45',
            'currency': 'USD',
            'product_description': 'New Test Product'
        }
        response = self.client.post(self.list_create_url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        created_order = Order.objects.first()
        self.assertEqual(created_order.user, self.user)
        self.assertEqual(created_order.amount, Decimal('123.45'))
        self.assertEqual(response.data['amount'], '123.45') # Serializer returns string for Decimal by default

    def test_create_order_missing_fields(self):
        """Test creating an order with missing required fields fails."""
        order_data = {'amount': '10.00'} # Missing currency
        response = self.client.post(self.list_create_url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('currency', response.data)

    def test_list_orders_authenticated_user(self):
        """Test listing orders for the authenticated user."""
        Order.objects.create(user=self.user, amount='10.00', currency='USD')
        Order.objects.create(user=self.user, amount='20.00', currency='EUR')
        # Create an order for another user to ensure filtering
        other_user = User.objects.create(username='otheruser', email='other@example.com', password_hash=make_password('pass'))
        Order.objects.create(user=other_user, amount='30.00', currency='JPY')

        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data.get('results', response.data) # Handle pagination
        self.assertEqual(len(results), 2)
        for order_data in results:
            self.assertEqual(order_data['user']['id'], self.user.id) # Check if user data is nested and correct

    def test_retrieve_order_authenticated_user(self):
        """Test retrieving a specific order belonging to the authenticated user."""
        order = Order.objects.create(user=self.user, amount='55.55', currency='GBP')
        detail_url = reverse('order-detail', kwargs={'pk': order.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], order.id)
        self.assertEqual(response.data['amount'], '55.55')

    def test_retrieve_order_forbidden_for_other_user(self):
        """Test retrieving an order not belonging to the authenticated user is forbidden."""
        other_user = User.objects.create(username='otheruser2', email='other2@example.com', password_hash=make_password('pass'))
        other_order = Order.objects.create(user=other_user, amount='10.00')
        detail_url = reverse('order-detail', kwargs={'pk': other_order.pk})
        
        response = self.client.get(detail_url)
        # This should be 404 as get_queryset in OrderViewSet filters by user, so order not found for current user.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PaymentBatchViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='testbatchviewuser', 
            email='testbatchview@example.com', 
            password_hash=make_password('testpass123')
        )
        cls.order1 = Order.objects.create(user=cls.user, amount=Decimal('10.00'), status='PENDING')
        cls.order2 = Order.objects.create(user=cls.user, amount=Decimal('20.00'), status='PENDING')
        cls.order3 = Order.objects.create(user=cls.user, amount=Decimal('30.00'), status='PROCESSING') # Not pending

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        self.list_create_url = reverse('paymentbatch-list')

    def test_create_payment_batch_success(self):
        """Test creating a payment batch successfully with valid order IDs."""
        batch_data = {'order_ids': [self.order1.id, self.order2.id]}
        response = self.client.post(self.list_create_url, batch_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentBatch.objects.count(), 1)
        # response.data should be a list of created batches
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1) 
        
        created_batch_data = response.data[0]
        created_batch_db = PaymentBatch.objects.get(pk=created_batch_data['id'])

        self.assertEqual(created_batch_db.created_by_user, self.user)
        self.assertEqual(created_batch_db.total_orders, 2)
        self.assertEqual(created_batch_db.total_amount, self.order1.amount + self.order2.amount)
        self.assertIn(self.order1.id, [o['id'] for o in created_batch_data['orders']])
        self.assertIn(self.order2.id, [o['id'] for o in created_batch_data['orders']])
        
        # Check if orders status updated (service logic might change this)
        self.order1.refresh_from_db()
        self.order2.refresh_from_db()
        self.assertEqual(self.order1.status, 'PROCESSING') # As per current batch_service logic
        self.assertEqual(self.order2.status, 'PROCESSING')


    def test_create_payment_batch_invalid_order_ids(self):
        """Test batch creation fails if order IDs are invalid or orders are not suitable."""
        # Order3 is not PENDING, order4 does not exist, order5 belongs to another user
        other_user = User.objects.create(username='anotherbatchuser', email='another@example.com', password_hash=make_password('pass'))
        order_other_user = Order.objects.create(user=other_user, amount='5.00', status='PENDING')

        invalid_batch_data = {'order_ids': [self.order1.id, self.order3.id]} # order3 is PROCESSING
        response = self.client.post(self.list_create_url, invalid_batch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data) # Service raises ValueError

        invalid_batch_data_non_existent = {'order_ids': [self.order1.id, 99999]} # 99999 does not exist
        response = self.client.post(self.list_create_url, invalid_batch_data_non_existent, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_batch_data_other_user = {'order_ids': [self.order1.id, order_other_user.id]}
        response = self.client.post(self.list_create_url, invalid_batch_data_other_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @patch('apps.orders.tasks.process_batch_payment_task.delay')
    def test_trigger_payment_action(self, mock_delay):
        """Test the trigger_payment action on a PaymentBatch."""
        batch = PaymentBatch.objects.create(
            created_by_user=self.user, 
            total_amount='100.00', 
            total_orders=1,
            status='PENDING_PROCESSING'
        )
        trigger_url = reverse('paymentbatch-trigger-payment', kwargs={'pk': batch.pk})
        
        response = self.client.post(trigger_url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('detail', response.data)
        self.assertTrue('Payment processing triggered' in response.data['detail'])
        
        mock_delay.assert_called_once_with(batch_id=batch.id)
        
        batch.refresh_from_db()
        # The view sets status to RETRY_PROCESSING if it was FAILED/PARTIALLY_COMPLETED.
        # If it was PENDING_PROCESSING, it remains as is, task will change it.
        # Let's check if it was set to RETRY_PROCESSING for a previously failed batch.
        batch.status = 'FAILED'
        batch.save()
        self.client.post(trigger_url)
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'RETRY_PROCESSING')


class AlipayNotifyViewTests(APITestCase):
    
    def setUp(self):
        self.notify_url = reverse('alipay-callback') # Make sure this name matches your URL conf
        self.user = User.objects.create(username='notifyuser', email='notify@example.com', password_hash=make_password('pass'))
        self.order = Order.objects.create(user=self.user, amount='10.00', order_uid='test-order-uid-for-notify')
        self.batch = PaymentBatch.objects.create(created_by_user=self.user, total_amount='10.00', total_orders=1, batch_uid='test-batch-uid-for-notify')
        self.order.payment_batch = self.batch
        self.order.save()

    @patch('apps.orders.tasks.handle_alipay_notification_task.delay')
    def test_alipay_notify_view_success_response(self, mock_delay):
        """Test AlipayNotifyView receives data and enqueues task, returns 'success'."""
        # This is a simplified notification data structure
        alipay_data = {
            'out_trade_no': str(self.order.order_uid), 
            'trade_no': 'alipay_trade_123',
            'trade_status': 'TRADE_SUCCESS',
            'sign': 'mock_signature', # Real signature verification is in service (mocked here)
            'sign_type': 'RSA2'
        }
        response = self.client.post(self.notify_url, alipay_data, format='json') # Or 'multipart/form-data' if Alipay sends that
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), 'success') # Plain text "success"
        mock_delay.assert_called_once_with(notification_data=alipay_data)

    @patch('apps.orders.tasks.handle_alipay_notification_task.delay')
    def test_alipay_notify_view_batch_notification(self, mock_delay):
        alipay_batch_data = {
            'out_batch_no': str(self.batch.batch_uid),
            'batch_no': 'alipay_batch_id_456',
            'success_details': [{'out_trade_no': str(self.order.order_uid), 'status':'SUCCESS', 'trade_no':'alipay_order_trade_789'}],
            'sign': 'mock_signature_batch',
        }
        response = self.client.post(self.notify_url, alipay_batch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), 'success')
        mock_delay.assert_called_once_with(notification_data=alipay_batch_data)

    def test_alipay_notify_view_empty_data(self):
        """Test view returns 'failure' for empty or unidentifiable notification."""
        response = self.client.post(self.notify_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content.decode(), 'failure')

# Note: For views using IsAuthenticated, self.client.force_authenticate(user=self.user) is crucial.
# If your custom User model doesn't work well with force_authenticate, you'd need to set up
# token authentication (e.g., SimpleJWT) and acquire a token to set in client.credentials() for tests.
