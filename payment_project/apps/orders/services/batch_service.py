from django.db import transaction
from django.utils import timezone
from apps.orders.models import Order, PaymentBatch
from apps.users.models import User # Assuming your custom User model

MAX_ORDERS_PER_BATCH = 2000 # As per requirement

@transaction.atomic
def create_payment_batches_for_orders(user: User, order_ids: list[int]) -> list[PaymentBatch]:
    """
    Creates payment batches for a given list of order IDs.

    Args:
        user: The user requesting the batch creation.
        order_ids: A list of primary key IDs for Orders.

    Returns:
        A list of created PaymentBatch objects.

    Raises:
        ValueError: If orders are invalid (not found, not belonging to user, wrong status, or already in a batch).
        # Consider using custom exceptions for more granular error handling.
    """
    if not order_ids:
        raise ValueError("Order IDs list cannot be empty.")

    # Fetch orders and validate them
    orders_to_batch = Order.objects.filter(
        id__in=order_ids,
        user=user,
        status=Order.STATUS_CHOICES[0][0],  # 'PENDING'
        payment_batch__isnull=True
    ).select_for_update() # Lock rows to prevent race conditions if this is called concurrently

    if len(orders_to_batch) != len(set(order_ids)): # Check if all requested orders were valid and fetched
        # Find missing/invalid orders for a more detailed error
        fetched_order_ids = {o.id for o in orders_to_batch}
        invalid_ids = set(order_ids) - fetched_order_ids
        # Could query these invalid_ids to give specific reasons, e.g.,
        # Order.objects.filter(id__in=invalid_ids, user=user) to see if status or batch was the issue.
        raise ValueError(f"Some orders are invalid, already batched, not pending, or do not belong to you. Invalid/unbatched IDs: {invalid_ids}")

    if not orders_to_batch:
        raise ValueError("No valid orders found to batch.")

    created_batches = []
    
    # Split orders into chunks of MAX_ORDERS_PER_BATCH
    for i in range(0, len(orders_to_batch), MAX_ORDERS_PER_BATCH):
        order_chunk = list(orders_to_batch[i : i + MAX_ORDERS_PER_BATCH]) # Slicing a queryset executes it
        
        if not order_chunk:
            continue

        total_amount_chunk = sum(order.amount for order in order_chunk)
        
        # Create a new PaymentBatch
        batch = PaymentBatch.objects.create(
            created_by_user=user,
            total_amount=total_amount_chunk,
            total_orders=len(order_chunk),
            status='PENDING_PROCESSING' # Initial status
        )
        
        # Associate orders with this batch
        order_ids_in_chunk = [order.id for order in order_chunk]
        Order.objects.filter(id__in=order_ids_in_chunk).update(
            payment_batch=batch,
            status='PROCESSING' # Or keep PENDING until batch processing starts
                                 # For now, let's assume adding to batch means it's ready for processing by batch.
                                 # The task asked for orders to be in 'PENDING' state for batching.
                                 # Let's say once batched, the order itself is 'PROCESSING' (or 'BATCHED')
                                 # For simplicity, let's use 'PROCESSING' from the Order status choices.
                                 # If 'BATCHED' was a status, it would be better.
                                 # Let's assume 'PROCESSING' means it's part of an active batch.
        )
        
        # Refresh batch from DB to get updated order associations if needed, though not strictly necessary here
        # batch.refresh_from_db() 
        created_batches.append(batch)
        
    return created_batches
