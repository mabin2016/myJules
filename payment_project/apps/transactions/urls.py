from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentTransactionViewSet

router = DefaultRouter()
router.register(r'transactions', PaymentTransactionViewSet, basename='paymenttransaction')
# Basename is 'paymenttransaction' to match the model name (lowercase) by convention,
# ensuring URL names like 'paymenttransaction-list' and 'paymenttransaction-detail'.

urlpatterns = [
    path('', include(router.urls)),
    # Add other transaction-related non-ViewSet URLs here if needed.
]
