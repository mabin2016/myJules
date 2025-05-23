import uuid
from django.db import models
from django.conf import settings # To reference the User model, especially if it's custom or default

# It's better to use settings.AUTH_USER_MODEL if you are using Django's auth system.
# Since apps.users.models.User is a direct translation of the schema and not Django's auth User,
# we will import it directly.
from apps.users.models import User


class PaymentBatch(models.Model):
    id = models.AutoField(primary_key=True)
    batch_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    STATUS_CHOICES = [
        ('PENDING_PROCESSING', 'Pending Processing'),
        ('PROCESSING', 'Processing'),
        ('PARTIALLY_COMPLETED', 'Partially Completed'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        default='PENDING_PROCESSING', 
        null=False
    )
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, null=False)
    total_orders = models.IntegerField(null=False)
    processed_orders = models.IntegerField(default=0, null=False)
    successful_orders = models.IntegerField(default=0, null=False)
    failed_orders = models.IntegerField(default=0, null=False)
    
    alipay_batch_no = models.CharField(max_length=255, null=True, blank=True, unique=True, db_index=True)
    alipay_notify_data = models.JSONField(null=True, blank=True) # Store raw notification
    
    created_by_user = models.ForeignKey(
        User, # Directly referencing the User model from apps.users.models
        on_delete=models.PROTECT, # Or SET_NULL if user deletion shouldn't block batches
        null=False,
        related_name='payment_batches'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Batch {self.batch_uid} - Status: {self.status}"

    class Meta:
        db_table = 'payment_batches'
        verbose_name = 'Payment Batch'
        verbose_name_plural = 'Payment Batches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    order_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    user = models.ForeignKey(
        User, # Directly referencing the User model
        on_delete=models.PROTECT, # Or SET_NULL
        null=False,
        related_name='orders'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    currency = models.CharField(max_length=3, default='CNY', null=False) # E.g., CNY, USD
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        default='PENDING', 
        null=False
    )
    
    product_description = models.TextField(null=True, blank=True)
    
    payment_batch = models.ForeignKey(
        PaymentBatch,
        on_delete=models.SET_NULL, # If batch is deleted, order might still exist
        null=True, 
        blank=True,
        related_name='orders',
        db_index=True
    )
    
    alipay_trade_no = models.CharField(max_length=255, null=True, blank=True, unique=True, db_index=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_uid} - Amount: {self.amount} {self.currency} - Status: {self.status}"

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]
