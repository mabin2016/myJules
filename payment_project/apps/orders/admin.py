from django.contrib import admin
from .models import PaymentBatch, Order

@admin.register(PaymentBatch)
class PaymentBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_uid', 
        'status', 
        'total_amount', 
        'total_orders', 
        'processed_orders',
        'successful_orders',
        'failed_orders',
        'created_by_user', 
        'created_at', 
        'processing_started_at',
        'completed_at'
    )
    search_fields = ('batch_uid', 'alipay_batch_no', 'created_by_user__username')
    list_filter = ('status', 'created_at', 'processing_started_at', 'completed_at')
    readonly_fields = (
        'batch_uid', 
        'created_at', 
        'updated_at', 
        'processing_started_at', 
        'completed_at',
        'total_amount',
        'total_orders',
        'processed_orders',
        'successful_orders',
        'failed_orders',
        'alipay_notify_data' # Should generally not be edited manually
    )
    fieldsets = (
        (None, {
            'fields': ('batch_uid', 'status', 'created_by_user')
        }),
        ('Financials & Counts', {
            'fields': ('total_amount', 'total_orders', 'processed_orders', 'successful_orders', 'failed_orders')
        }),
        ('Alipay Details', {
            'fields': ('alipay_batch_no', 'alipay_notify_data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processing_started_at', 'completed_at')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Make status editable only if batch is in a state that allows manual change
        if obj and obj.status in ['PENDING_PROCESSING', 'FAILED']: # Example states
            return [f for f in self.readonly_fields if f != 'status']
        return self.readonly_fields

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_uid', 
        'user', 
        'amount', 
        'currency', 
        'status', 
        'payment_batch', 
        'created_at'
    )
    search_fields = ('order_uid', 'user__username', 'alipay_trade_no', 'payment_batch__batch_uid')
    list_filter = ('status', 'currency', 'created_at', 'payment_batch')
    readonly_fields = ('order_uid', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('order_uid', 'user', 'status', 'payment_batch')
        }),
        ('Order Details', {
            'fields': ('amount', 'currency', 'product_description')
        }),
        ('Alipay Details', {
            'fields': ('alipay_trade_no', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Make status editable only if order is in a state that allows manual change
        if obj and obj.status in ['PENDING', 'FAILED']: # Example states
            return [f for f in self.readonly_fields if f != 'status']
        return self.readonly_fields
