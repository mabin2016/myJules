from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_uid', 
        'order_link', # Custom method to link to order admin
        'payment_batch_link', # Custom method to link to batch admin
        'amount', 
        'currency', 
        'status', 
        'alipay_trade_no',
        'created_at'
    )
    search_fields = ('transaction_uid', 'order__order_uid', 'payment_batch__batch_uid', 'alipay_trade_no')
    list_filter = ('status', 'currency', 'created_at')
    readonly_fields = (
        'transaction_uid', 
        'order', 
        'payment_batch', 
        'created_at', 
        'updated_at',
        'request_payload', # Should not be manually edited
        'response_payload' # Should not be manually edited
    )
    fieldsets = (
        (None, {
            'fields': ('transaction_uid', 'order', 'payment_batch', 'status')
        }),
        ('Transaction Details', {
            'fields': ('amount', 'currency', 'alipay_trade_no')
        }),
        ('Payloads & Errors', {
            'fields': ('request_payload', 'response_payload', 'error_code', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.order:
            link = reverse("admin:orders_order_change", args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', link, obj.order.order_uid)
        return "N/A"
    order_link.short_description = 'Order'

    def payment_batch_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.payment_batch:
            link = reverse("admin:orders_paymentbatch_change", args=[obj.payment_batch.id])
            return format_html('<a href="{}">{}</a>', link, obj.payment_batch.batch_uid)
        return "N/A"
    payment_batch_link.short_description = 'Payment Batch'

    def get_readonly_fields(self, request, obj=None):
        # Make status editable only if transaction is in a state that allows manual change
        if obj and obj.status in ['INITIATED', 'PENDING', 'FAILED']: # Example states
            return [f for f in self.readonly_fields if f != 'status']
        return self.readonly_fields
