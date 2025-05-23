from rest_framework import viewsets, permissions
from .models import PaymentTransaction
from .serializers import PaymentTransactionSerializer

class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Payment Transactions to be viewed.
    This is primarily for read-only access to transaction logs.
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated] # Or more specific permissions like IsAdminUser or custom

    def get_queryset(self):
        """
        This view should return a list of all transactions.
        Filtering by user might be complex as transactions are linked to orders.
        If non-admin users can see their transactions, it should be filtered based on
        orders they own.
        """
        user = self.request.user
        if user.is_staff: # Admins can see all transactions
            return PaymentTransaction.objects.all().select_related('order', 'payment_batch').order_by('-created_at')
        
        # Regular users can see transactions related to their orders
        return PaymentTransaction.objects.filter(order__user=user).select_related('order', 'payment_batch').order_by('-created_at')

    # No create, update, delete actions as this is ReadOnlyModelViewSet.
    # If creation of transactions via API was needed (e.g., manual logging, though unlikely),
    # this would need to be a ModelViewSet with appropriate permissions and logic.
