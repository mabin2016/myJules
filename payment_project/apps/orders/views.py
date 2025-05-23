import logging
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponse # For plain text responses to Alipay

from .models import Order, PaymentBatch
from .serializers import (
    OrderSerializer, 
    PaymentBatchSerializer, 
    PaymentBatchCreateSerializer
)
from .tasks import process_batch_payment_task, handle_alipay_notification_task # Import Celery tasks
from .services.batch_service import create_payment_batches_for_orders

logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the orders
        for the currently authenticated user.
        """
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Set the user of the order to the currently authenticated user.
        """
        serializer.save(user=self.request.user)

class PaymentBatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Payment Batches.
    """
    serializer_class = PaymentBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the payment batches
        for the currently authenticated user.
        """
        return PaymentBatch.objects.filter(created_by_user=self.request.user).prefetch_related('orders').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Creates one or more PaymentBatches from a list of Order IDs.
        Orders are grouped into batches, ensuring no batch exceeds 2000 orders.
        """
        create_serializer = PaymentBatchCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            logger.warning(f"PaymentBatch creation failed validation: {create_serializer.errors}")
            return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_ids = create_serializer.validated_data['order_ids']
        
        try:
            created_batches = create_payment_batches_for_orders(
                user=request.user, 
                order_ids=order_ids
            )
        except ValueError as e:
            logger.error(f"ValueError during batch creation for user {request.user.id}, order_ids {order_ids}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Unexpected error during batch creation for user {request.user.id}, order_ids {order_ids}: {e}")
            return Response({'detail': 'An unexpected error occurred during batch creation.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not created_batches:
            logger.info(f"No batches created for user {request.user.id}, order_ids {order_ids}. May be due to invalid/processed orders.")
            return Response(
                {'detail': 'No batches were created. This might be due to all orders already being processed or invalid.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        response_serializer = self.get_serializer(created_batches, many=True)
        logger.info(f"User {request.user.id} created {len(created_batches)} batches successfully.")
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='trigger-payment')
    def trigger_payment(self, request, pk=None):
        """
        Triggers the payment process for a specific batch by enqueuing a Celery task.
        """
        batch = self.get_object() # Checks user ownership via get_queryset

        if batch.status not in ['PENDING_PROCESSING', 'FAILED', 'PARTIALLY_COMPLETED', 'RETRY_PROCESSING']:
            logger.warning(f"User {request.user.id} attempt to trigger payment for batch {batch.batch_uid} in invalid state: {batch.status}")
            return Response(
                {'detail': f'Batch cannot be processed in its current status: {batch.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If the batch previously failed or was partial, set to a retry state
        if batch.status in ['FAILED', 'PARTIALLY_COMPLETED']:
            batch.status = 'RETRY_PROCESSING' 
            # Potentially reset some fields here if needed, or let the task handle it.
            # For example, if processing_started_at should be updated for the retry.
            batch.save(update_fields=['status', 'updated_at'])

        task = process_batch_payment_task.delay(batch_id=batch.id)
        logger.info(f"User {request.user.id} triggered payment for batch {batch.batch_uid} (ID: {batch.id}). Celery task ID: {task.id}")
        
        return Response(
            {'detail': f'Payment processing triggered for batch {batch.batch_uid}. Task ID: {task.id}'},
            status=status.HTTP_202_ACCEPTED # Accepted for processing
        )


from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class AlipayNotifyView(APIView):
    """
    Handles asynchronous notifications from Alipay.
    This endpoint should be exposed publicly but secured by signature verification (simulated in service).
    """
    permission_classes = [AllowAny] 

    # @transaction.atomic # The Celery task should handle its own transactions if needed
    def post(self, request, *args, **kwargs):
        notification_data = request.data.dict() # Or request.data if content type is JSON
        logger.info(f"Received Alipay notification: {notification_data}")

        # Basic validation: check if it's a notification we can process
        # This depends heavily on Alipay's actual notification structure.
        # For example, check for 'trade_status' or 'batch_no' or 'out_trade_no'.
        if not notification_data or not ('out_trade_no' in notification_data or 'out_batch_no' in notification_data):
            logger.warning("Received empty or unidentifiable Alipay notification.")
            # Alipay expects a plain text "failure" for invalid notifications it shouldn't retry.
            return HttpResponse("failure", content_type="text/plain", status=status.HTTP_400_BAD_REQUEST)

        # Enqueue Celery task to handle the notification processing
        # Pass the raw notification data to the task.
        # The task will then call the alipay_service for signature verification and processing.
        handle_alipay_notification_task.delay(notification_data=notification_data)
        
        logger.info(f"Alipay notification for {notification_data.get('out_batch_no') or notification_data.get('out_trade_no')} enqueued for processing.")

        # Respond to Alipay immediately indicating receipt.
        # Alipay expects a plain text "success" or "failure".
        # Do NOT return detailed JSON from DRF's Response here.
        return HttpResponse("success", content_type="text/plain", status=status.HTTP_200_OK)
