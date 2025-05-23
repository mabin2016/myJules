from rest_framework import serializers
from .models import PaymentTransaction
from apps.orders.serializers import OrderSerializer # For read-only nested display
from apps.users.serializers import UserDisplaySerializer # Potentially for user via order

class PaymentTransactionSerializer(serializers.ModelSerializer):
    # To provide more context, you might want to nest some order information.
    # However, be mindful of query complexity if OrderSerializer is deeply nested.
    # For simplicity, we can just show the order_id or a light representation.
    order_uid = serializers.UUIDField(source='order.order_uid', read_only=True)
    payment_batch_uid = serializers.UUIDField(source='payment_batch.batch_uid', read_only=True, allow_null=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'transaction_uid', 'order', 'order_uid', 'payment_batch', 'payment_batch_uid',
            'alipay_trade_no', 'amount', 'currency', 'status',
            'request_payload', 'response_payload', 'error_code', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_uid', 'order_uid', 'payment_batch_uid',
            'alipay_trade_no', 'amount', 'currency', 'status', # Typically status is set by system
            'request_payload', 'response_payload', 'error_code', 'error_message',
            'created_at', 'updated_at'
        ]
        # Exclude 'order' and 'payment_batch' (FK IDs) if you prefer only UIDs for representation
        # and use 'order_uid' and 'payment_batch_uid' above.
        # If you want to allow setting order/batch by ID during creation (if applicable):
        # 'order': serializers.PrimaryKeyRelatedField(queryset=Order.objects.all()),
        # 'payment_batch': serializers.PrimaryKeyRelatedField(queryset=PaymentBatch.objects.all(), allow_null=True),

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Remove raw FK IDs if UIDs are preferred for output
        representation.pop('order', None) 
        representation.pop('payment_batch', None)
        return representation
