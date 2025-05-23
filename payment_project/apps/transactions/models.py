import uuid
from django.db import models
from apps.orders.models import Order, PaymentBatch # Foreign keys to these models

class PaymentTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE, # If an order is deleted, its transactions are deleted
        null=False,
        related_name='payment_transactions'
    )
    payment_batch = models.ForeignKey(
        PaymentBatch,
        on_delete=models.SET_NULL, # If a batch is deleted, transaction might still be relevant to the order
        null=True,
        blank=True,
        related_name='payment_transactions'
    )
    
    transaction_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    alipay_trade_no = models.CharField(max_length=255, null=True, blank=True, db_index=True) # Alipay's ID for this attempt
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    currency = models.CharField(max_length=3, null=False) # E.g., CNY, USD
    
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'), # Payment attempt started
        ('SUCCESS', 'Success'),     # Payment successful
        ('FAILED', 'Failed'),       # Payment failed
        ('PENDING', 'Pending'),     # Payment pending confirmation (e.g. waiting for Alipay async notification)
    ]
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        null=False,
        db_index=True
    )
    
    request_payload = models.JSONField(null=True, blank=True)  # Data sent to Alipay
    response_payload = models.JSONField(null=True, blank=True) # Data received from Alipay (non-sensitive parts)
    
    error_code = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.transaction_uid} for Order {self.order.order_uid} - Status: {self.status}"

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['payment_batch']),
            models.Index(fields=['status']),
        ]
