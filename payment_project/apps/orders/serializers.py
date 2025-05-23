from rest_framework import serializers
from .models import Order, PaymentBatch
from apps.users.serializers import UserDisplaySerializer # For read-only user display
from apps.users.models import User # Required for queryset in PrimaryKeyRelatedField if needed

class OrderSerializer(serializers.ModelSerializer):
    user = UserDisplaySerializer(read_only=True)
    # user_id = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.all(), write_only=True, source='user'
    # ) # Use this if you want to pass user_id for write operations

    class Meta:
        model = Order
        fields = [
            'id', 'order_uid', 'user', 'amount', 'currency', 'status', 
            'product_description', 'payment_batch', 'alipay_trade_no', 
            'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_uid', 'status', 'payment_batch', 
            'alipay_trade_no', 'error_message', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        # The user will be set in the view based on request.user
        return super().create(validated_data)

class PaymentBatchCreateSerializer(serializers.Serializer): # Not a ModelSerializer
    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="A list of Order IDs to be included in the batch(es)."
    )
    # created_by_user_id will be set from request.user in the view

    def validate_order_ids(self, order_ids):
        # Further validation (e.g., checking if orders exist, belong to user, are PENDING)
        # will be done in the view or service layer.
        if not order_ids:
            raise serializers.ValidationError("order_ids list cannot be empty.")
        
        # Check for duplicates
        if len(order_ids) != len(set(order_ids)):
            raise serializers.ValidationError("Duplicate order_ids are not allowed.")
            
        return order_ids

class PaymentBatchSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True) # Nested orders for display
    created_by_user = UserDisplaySerializer(read_only=True)

    class Meta:
        model = PaymentBatch
        fields = [
            'id', 'batch_uid', 'status', 'total_amount', 'total_orders',
            'processed_orders', 'successful_orders', 'failed_orders',
            'alipay_batch_no', 'created_by_user', 'created_at', 'updated_at',
            'processing_started_at', 'completed_at', 'orders'
        ]
        read_only_fields = [
            'id', 'batch_uid', 'status', 'total_amount', 'total_orders',
            'processed_orders', 'successful_orders', 'failed_orders',
            'alipay_batch_no', 'created_at', 'updated_at',
            'processing_started_at', 'completed_at', 'orders'
        ]

    # If creating batches directly via this serializer (not recommended for complex logic),
    # you'd need a create method here. But we'll use PaymentBatchCreateSerializer for creation.
