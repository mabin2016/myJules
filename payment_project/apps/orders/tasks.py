import logging
from celery import shared_task, Task
from django.utils import timezone
from django.db import transaction

from apps.orders.models import PaymentBatch, Order
from apps.transactions.models import PaymentTransaction
from apps.orders.services import alipay_service # Using the alias

logger = logging.getLogger(__name__)

class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,) # Retry on any exception
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 7000 # Max backoff in ms
    retry_jitter = True # Add jitter to avoid thundering herd

@shared_task(bind=True, base=BaseTaskWithRetry)
def process_batch_payment_task(self, batch_id: int):
    """
    Celery task to process a payment batch.
    Option 1: Assumes Alipay API allows submitting a batch in one go.
              Individual order statuses might be updated via async notifications.
    Option 2: (Less common for true batch APIs) Iterate and pay each order individually.
              This implementation will lean towards Option 1 for the initial call,
              and then simulate individual processing if Alipay doesn't give per-order
              results in the synchronous batch submission response.
    """
    logger.info(f"[Task ID: {self.request.id}] Processing batch_id: {batch_id}")
    self.update_state(state='PROGRESS', meta={'batch_id': batch_id, 'status': 'Fetching batch details'})

    try:
        batch = PaymentBatch.objects.get(id=batch_id)
    except PaymentBatch.DoesNotExist:
        logger.error(f"[Task ID: {self.request.id}] Batch with id {batch_id} not found.")
        # No retry if batch doesn't exist.
        # self.update_state(state='FAILURE', meta={'reason': 'Batch not found'}) # Not needed due to autoretry_for
        raise # Celery will handle retry based on decorator
    
    if batch.status not in ['PENDING_PROCESSING', 'RETRY_PROCESSING', 'PARTIALLY_COMPLETED']:
        logger.warning(f"[Task ID: {self.request.id}] Batch {batch.batch_uid} (ID: {batch_id}) is not in a processable state. Current status: {batch.status}")
        return f"Batch {batch.batch_uid} not processable (status: {batch.status})"

    with transaction.atomic():
        batch.status = 'PROCESSING'
        batch.processing_started_at = timezone.now()
        # Reset counts for idempotency if retrying a partially completed batch
        if batch.status == 'RETRY_PROCESSING' or batch.status == 'PARTIALLY_COMPLETED':
            batch.processed_orders = 0
            batch.successful_orders = 0
            batch.failed_orders = 0
        batch.save()

        # --- Simulate single call to Alipay for the entire batch ---
        self.update_state(state='PROGRESS', meta={'batch_id': batch_id, 'status': 'Submitting batch to Alipay...'})
        alipay_batch_submission_response = alipay_service.initiate_batch_payment_to_alipay(batch)

        if not alipay_batch_submission_response["success"]:
            batch.status = 'FAILED' # Batch submission itself failed
            batch.error_message = alipay_batch_submission_response.get("error_message", "Alipay batch submission failed.")
            batch.completed_at = timezone.now()
            batch.save()
            logger.error(f"[Task ID: {self.request.id}] Alipay batch submission failed for batch {batch.batch_uid}: {batch.error_message}")
            # Update all orders in batch to FAILED if the batch submission fails critically
            batch.orders.update(status='FAILED', error_message="Batch submission to Alipay failed.")
            return f"Alipay batch submission failed for {batch.batch_uid}."
        
        # Store Alipay's batch number if provided by the (mocked) service
        if alipay_batch_submission_response.get("alipay_batch_no"):
            batch.alipay_batch_no = alipay_batch_submission_response["alipay_batch_no"]
            batch.save(update_fields=['alipay_batch_no'])
        
        logger.info(f"[Task ID: {self.request.id}] Batch {batch.batch_uid} submitted to Alipay. Response: {alipay_batch_submission_response.get('message')}")
        self.update_state(state='PROGRESS', meta={'batch_id': batch_id, 'status': 'Alipay batch submitted. Simulating per-order processing if needed.'})

        # --- Simulate processing individual orders within the batch ---
        # This part simulates if Alipay's batch submission doesn't immediately give per-order results,
        # OR if we need to make per-order calls regardless (less typical for a true batch API).
        # For a true batch API where results are async, this loop might not exist,
        # and all updates would come via handle_alipay_notification_task.
        # For this simulation, we'll process each order as if we got immediate results or are making individual calls.

        orders_to_process = batch.orders.filter(status__in=['PENDING', 'PROCESSING']) # Orders not yet finalized

        for order in orders_to_process:
            logger.info(f"[Task ID: {self.request.id}] Processing order {order.order_uid} within batch {batch.batch_uid}")
            order.status = 'PROCESSING' # Mark as being processed
            order.save(update_fields=['status'])

            # Simulate individual payment call for the order
            payment_response = alipay_service.initiate_payment_for_order(order, payment_batch=batch)
            
            transaction_status = 'PENDING' # Default transaction status
            
            if payment_response["success"]:
                order.status = 'SUCCESS'
                order.alipay_trade_no = payment_response.get("alipay_trade_no")
                order.error_message = None # Clear previous errors
                batch.successful_orders += 1
                transaction_status = 'SUCCESS'
                logger.info(f"[Task ID: {self.request.id}] Order {order.order_uid} processed: SUCCESS")
            else:
                order.status = 'FAILED'
                order.error_message = payment_response.get("error_message", "Payment failed")
                batch.failed_orders += 1
                transaction_status = 'FAILED'
                logger.warning(f"[Task ID: {self.request.id}] Order {order.order_uid} processed: FAILED - {order.error_message}")
            
            order.save()
            batch.processed_orders += 1

            # Create PaymentTransaction log
            PaymentTransaction.objects.create(
                order=order,
                payment_batch=batch,
                transaction_uid=uuid.uuid4(), # Generate new UID for this transaction log
                alipay_trade_no=order.alipay_trade_no if order.status == 'SUCCESS' else payment_response.get('alipay_trade_no'),
                amount=order.amount,
                currency=order.currency,
                status=transaction_status,
                request_payload={'batch_id': batch_id, 'order_id': order.id}, # Mock request
                response_payload=payment_response,
                error_code=payment_response.get("error_code"),
                error_message=payment_response.get("error_message") if transaction_status == 'FAILED' else None
            )

        # Finalize batch status
        if batch.failed_orders == 0 and batch.successful_orders == batch.total_orders:
            batch.status = 'COMPLETED'
        elif batch.successful_orders > 0 or batch.failed_orders > 0 : # Some processing happened
             if batch.processed_orders == batch.total_orders: # All orders attempted
                if batch.successful_orders == batch.total_orders:
                     batch.status = 'COMPLETED'
                elif batch.failed_orders == batch.total_orders:
                    batch.status = 'FAILED'
                else: # Mixed results
                    batch.status = 'PARTIALLY_COMPLETED'
             else: # Not all orders attempted (should not happen with current loop logic)
                batch.status = 'PARTIALLY_COMPLETED' # Or some other intermediate status
        elif batch.processed_orders == 0 : # No orders were processed (e.g. all filtered out initially)
             batch.status = 'FAILED' # Or a more specific status like 'NO_PROCESSABLE_ORDERS'
        else: # Fallback, should ideally not be reached if logic is sound
            batch.status = 'FAILED'


        batch.completed_at = timezone.now()
        batch.save()

    logger.info(f"[Task ID: {self.request.id}] Batch {batch.batch_uid} processing finished. Status: {batch.status}. "
                f"Successful: {batch.successful_orders}, Failed: {batch.failed_orders}, Processed: {batch.processed_orders}")
    
    final_message = (f"Batch {batch.batch_uid} processing complete. "
                     f"Status: {batch.status}, Success: {batch.successful_orders}/{batch.total_orders}.")
    self.update_state(state='SUCCESS' if batch.status == 'COMPLETED' or batch.status == 'PARTIALLY_COMPLETED' else 'FAILURE', 
                      meta={'batch_id': batch_id, 'result': final_message, 'status': batch.status})
    return final_message


@shared_task(bind=True, base=BaseTaskWithRetry)
def handle_alipay_notification_task(self, notification_data: dict, batch_id: int = None, order_id: int = None):
    """
    Celery task to process asynchronous notifications from Alipay.
    This task calls the alipay_service to handle the actual processing and DB updates.
    """
    logger.info(f"[Task ID: {self.request.id}] Handling Alipay notification. Data: {notification_data}. Batch ID: {batch_id}, Order ID: {order_id}")
    self.update_state(state='PROGRESS', meta={'status': 'Processing notification'})

    try:
        processing_result = alipay_service.verify_and_process_notification(notification_data)
        
        if processing_result.get("processed"):
            logger.info(f"[Task ID: {self.request.id}] Alipay notification processed successfully. Result: {processing_result}")
            self.update_state(state='SUCCESS', meta={'result': processing_result})
            return f"Notification processed. Updates: Orders - {processing_result.get('updated_orders', 0)}, Batches - {processing_result.get('updated_batches', 0)}"
        else:
            logger.error(f"[Task ID: {self.request.id}] Failed to process Alipay notification. Reason: {processing_result.get('reason')}")
            # This will trigger a retry due to BaseTaskWithRetry if an exception was not raised by the service
            # For controlled non-retry, the service should not raise an exception but return a clear "processed: False, no_retry_reason: ..."
            # For now, we assume any "processed: False" might be retriable.
            raise Exception(f"Notification processing failed: {processing_result.get('reason', 'Unknown reason')}")

    except Exception as e:
        logger.exception(f"[Task ID: {self.request.id}] Exception during Alipay notification processing: {e}")
        raise # Re-raise for Celery to handle retry as per BaseTaskWithRetry


@shared_task(name="example.health_check") # Keep for testing Celery worker
def health_check_task():
    now = timezone.now().isoformat()
    logger.info(f"Celery health check task executed at {now}")
    return f"Celery is healthy at {now}!"
