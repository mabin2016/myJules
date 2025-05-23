import random
import uuid
import logging
from django.utils import timezone
from apps.orders.models import Order, PaymentBatch
from apps.transactions.models import PaymentTransaction # For logging transactions if needed here

logger = logging.getLogger(__name__)

def generate_mock_alipay_trade_no():
    return f"ALIPAY_TRADE_NO_{uuid.uuid4().hex[:16].upper()}"

def generate_mock_alipay_batch_no():
    return f"ALIPAY_BATCH_NO_{uuid.uuid4().hex[:10].upper()}"

def initiate_payment_for_order(order: Order, payment_batch: PaymentBatch = None):
    """
    Simulates calling Alipay API for an individual order.
    This function DOES NOT change DB state directly. It returns data for the Celery task.
    """
    logger.info(f"Simulating Alipay payment initiation for order: {order.order_uid}")
    
    # Simulate success/failure
    # For more deterministic testing, you could base this on order.amount or an ID pattern
    if random.random() < 0.9: # 90% success rate
        mock_response = {
            "success": True,
            "alipay_trade_no": generate_mock_alipay_trade_no(),
            "order_uid": str(order.order_uid),
            "message": "Payment successful (simulated)."
        }
        logger.info(f"Order {order.order_uid} payment simulation: SUCCESS, Alipay Trade No: {mock_response['alipay_trade_no']}")
    else:
        error_code = random.choice(["SYSTEM_ERROR", "INVALID_PARAMETER", "INSUFFICIENT_FUNDS"])
        error_message = f"Simulated Alipay error: {error_code}"
        mock_response = {
            "success": False,
            "order_uid": str(order.order_uid),
            "error_code": error_code,
            "error_message": error_message,
            "message": "Payment failed (simulated)."
        }
        logger.warning(f"Order {order.order_uid} payment simulation: FAILED, Error: {error_code}")
        
    return mock_response

def initiate_batch_payment_to_alipay(payment_batch: PaymentBatch):
    """
    Simulates making a single call to Alipay for the entire payment_batch.
    Alipay's response might be a single acknowledgment for the batch.
    Individual order results might come via asynchronous notifications.
    """
    logger.info(f"Simulating Alipay batch payment submission for batch: {payment_batch.batch_uid}")
    
    # Simulate success/failure of batch submission itself
    if random.random() < 0.95: # 95% success rate for batch submission
        alipay_assigned_batch_no = generate_mock_alipay_batch_no()
        # payment_batch.alipay_batch_no = alipay_assigned_batch_no # Task should update the model
        # payment_batch.save(update_fields=['alipay_batch_no'])
        
        logger.info(f"Batch {payment_batch.batch_uid} submission to Alipay: SUCCESSFUL. Alipay Batch No: {alipay_assigned_batch_no}")
        return {
            "success": True,
            "alipay_batch_no": alipay_assigned_batch_no,
            "message": "Batch payment submitted to Alipay successfully (simulated). Waiting for async notifications for order details."
        }
    else:
        error_code = random.choice(["BATCH_REJECTED", "SYSTEM_BUSY"])
        logger.error(f"Batch {payment_batch.batch_uid} submission to Alipay: FAILED. Error: {error_code}")
        return {
            "success": False,
            "error_code": error_code,
            "error_message": f"Simulated Alipay batch submission error: {error_code}",
            "message": "Batch payment submission to Alipay failed (simulated)."
        }

def verify_and_process_notification(notification_data: dict):
    """
    Simulates verification and processing of an asynchronous notification from Alipay.
    This function will update the database based on the notification content.
    """
    logger.info(f"Received Alipay notification data: {notification_data}")

    # CRITICAL SECURITY TODO: Implement Alipay Signature Verification here!
    # For simulation, we assume the signature is valid.
    is_signature_valid = True # Simulate valid signature
    if not is_signature_valid:
        logger.error("Alipay notification signature verification failed. Discarding notification.")
        return {"processed": False, "reason": "Signature verification failed"}

    # --- Example Notification Processing Logic (Highly dependent on Alipay API & notification format) ---
    # This is a mock structure. Real Alipay notifications are more complex.
    # Common keys: 'notify_type', 'notify_id', 'notify_time', 'sign_type', 'sign',
    # 'trade_no' (Alipay's transaction ID for a single payment),
    # 'out_trade_no' (Our system's order ID),
    # 'trade_status' (e.g., TRADE_SUCCESS, TRADE_FINISHED, TRADE_CLOSED),
    # For batch payments: 'batch_no' (Alipay's batch transaction ID), 
    # 'out_batch_no' (Our system's batch UID), 'success_num', 'fail_num', 'result_details' (string or JSON string)

    alipay_trade_no = notification_data.get('trade_no') # For single order
    out_trade_no = notification_data.get('out_trade_no') # Our order_uid
    trade_status = notification_data.get('trade_status')

    alipay_batch_no_from_notif = notification_data.get('batch_no') # Alipay's batch ID
    out_batch_no = notification_data.get('out_batch_no') # Our batch_uid

    updated_orders_count = 0
    updated_batches_count = 0

    try:
        with transaction.atomic():
            if out_batch_no: # Likely a batch notification
                payment_batch = PaymentBatch.objects.filter(batch_uid=out_batch_no).first()
                if not payment_batch:
                    logger.warning(f"No PaymentBatch found for batch_uid: {out_batch_no} from notification.")
                    return {"processed": False, "reason": f"Batch UID {out_batch_no} not found."}
                
                payment_batch.alipay_notify_data = notification_data # Store raw notification
                if alipay_batch_no_from_notif and not payment_batch.alipay_batch_no:
                    payment_batch.alipay_batch_no = alipay_batch_no_from_notif

                # Example: Alipay might send a summary for the batch
                # And 'result_details' could be a list of individual order outcomes
                # This part is highly speculative without actual Alipay API docs for batch notifications
                success_details = notification_data.get('success_details', []) # [{ 'out_trade_no': 'id', 'status': 'SUCCESS'}, ...]
                failure_details = notification_data.get('failure_details', []) # [{ 'out_trade_no': 'id', 'status': 'FAIL', 'reason': '...'}, ...]

                if success_details or failure_details: # Detailed per-order status in batch notification
                    for detail in success_details:
                        order = Order.objects.filter(order_uid=detail.get('out_trade_no'), payment_batch=payment_batch).first()
                        if order and order.status == 'PROCESSING':
                            order.status = 'SUCCESS'
                            order.alipay_trade_no = detail.get('trade_no', generate_mock_alipay_trade_no())
                            order.save()
                            PaymentTransaction.objects.create(
                                order=order, payment_batch=payment_batch, amount=order.amount, currency=order.currency,
                                status='SUCCESS', alipay_trade_no=order.alipay_trade_no, response_payload=detail
                            )
                            updated_orders_count += 1
                    for detail in failure_details:
                        order = Order.objects.filter(order_uid=detail.get('out_trade_no'), payment_batch=payment_batch).first()
                        if order and order.status == 'PROCESSING':
                            order.status = 'FAILED'
                            order.error_message = detail.get('reason', 'Failed as per Alipay notification')
                            order.alipay_trade_no = detail.get('trade_no') # May or may not exist for failures
                            order.save()
                            PaymentTransaction.objects.create(
                                order=order, payment_batch=payment_batch, amount=order.amount, currency=order.currency,
                                status='FAILED', alipay_trade_no=order.alipay_trade_no, response_payload=detail,
                                error_message=order.error_message
                            )
                            updated_orders_count += 1
                    
                    # Recalculate batch stats based on detailed notifications
                    payment_batch.successful_orders = payment_batch.orders.filter(status='SUCCESS').count()
                    payment_batch.failed_orders = payment_batch.orders.filter(status='FAILED').count()
                    payment_batch.processed_orders = payment_batch.successful_orders + payment_batch.failed_orders

                    if payment_batch.processed_orders == payment_batch.total_orders:
                        if payment_batch.failed_orders == 0:
                            payment_batch.status = 'COMPLETED'
                        elif payment_batch.successful_orders > 0:
                            payment_batch.status = 'PARTIALLY_COMPLETED'
                        else:
                            payment_batch.status = 'FAILED'
                        payment_batch.completed_at = timezone.now()
                    else:
                        payment_batch.status = 'PROCESSING' # Still processing if not all orders accounted for

                elif trade_status: # A single status for the entire batch (less common for detailed results)
                    if trade_status in ['TRADE_SUCCESS', 'TRADE_FINISHED', 'SUCCESS']: # Adapt based on Alipay actual values
                        payment_batch.status = 'COMPLETED'
                        payment_batch.successful_orders = payment_batch.total_orders
                        payment_batch.failed_orders = 0
                        payment_batch.processed_orders = payment_batch.total_orders
                        payment_batch.completed_at = timezone.now()
                        # Update all orders in batch - this is a simplification
                        for order in payment_batch.orders.filter(status='PROCESSING'):
                            order.status = 'SUCCESS'
                            order.alipay_trade_no = generate_mock_alipay_trade_no() # Assign a generic one if not provided per order
                            order.save()
                            PaymentTransaction.objects.create(
                                order=order, payment_batch=payment_batch, amount=order.amount, currency=order.currency,
                                status='SUCCESS', alipay_trade_no=order.alipay_trade_no, response_payload=notification_data
                            )
                            updated_orders_count +=1
                    elif trade_status in ['TRADE_CLOSED', 'FAIL']:
                        payment_batch.status = 'FAILED'
                        payment_batch.failed_orders = payment_batch.total_orders
                        payment_batch.successful_orders = 0
                        payment_batch.processed_orders = payment_batch.total_orders
                        payment_batch.completed_at = timezone.now()
                        for order in payment_batch.orders.filter(status='PROCESSING'):
                            order.status = 'FAILED'
                            order.error_message = "Batch failed as per Alipay notification"
                            order.save()
                            PaymentTransaction.objects.create(
                                order=order, payment_batch=payment_batch, amount=order.amount, currency=order.currency,
                                status='FAILED', response_payload=notification_data, error_message=order.error_message
                            )
                            updated_orders_count += 1
                
                payment_batch.save()
                updated_batches_count += 1
                logger.info(f"PaymentBatch {payment_batch.batch_uid} updated from notification. Orders updated: {updated_orders_count}")

            elif out_trade_no: # Likely a single order notification
                order = Order.objects.filter(order_uid=out_trade_no).first()
                if not order:
                    logger.warning(f"No Order found for order_uid: {out_trade_no} from notification.")
                    return {"processed": False, "reason": f"Order UID {out_trade_no} not found."}

                # order.alipay_notify_data = notification_data # If you add such a field
                original_status = order.status
                
                if trade_status in ['TRADE_SUCCESS', 'TRADE_FINISHED']:
                    order.status = 'SUCCESS'
                elif trade_status == 'TRADE_CLOSED':
                    order.status = 'FAILED'
                # Add more specific trade statuses as needed
                
                order.alipay_trade_no = alipay_trade_no or order.alipay_trade_no # Update if new one provided
                order.save()
                
                PaymentTransaction.objects.create(
                    order=order, payment_batch=order.payment_batch, amount=order.amount, currency=order.currency,
                    status=order.status, alipay_trade_no=order.alipay_trade_no, response_payload=notification_data,
                    error_message=notification_data.get('error_message') if order.status == 'FAILED' else None
                )
                updated_orders_count += 1
                logger.info(f"Order {order.order_uid} updated from notification (Status: {original_status} -> {order.status}).")
            
            else:
                logger.warning("Alipay notification does not contain identifiable batch or order ID (out_batch_no or out_trade_no).")
                return {"processed": False, "reason": "Missing identifiers in notification."}

    except Exception as e:
        logger.exception(f"Error processing Alipay notification: {e}. Data: {notification_data}")
        return {"processed": False, "reason": f"Internal server error: {str(e)}"}
        
    return {"processed": True, "updated_orders": updated_orders_count, "updated_batches": updated_batches_count}
