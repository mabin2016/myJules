from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, PaymentBatchViewSet, AlipayNotifyView

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'batches', PaymentBatchViewSet, basename='paymentbatch')

urlpatterns = [
    path('', include(router.urls)),
    # URL for Alipay Asynchronous Notification
    # This should match the callback URL configured in your Alipay merchant account.
    path('alipay-callback/', AlipayNotifyView.as_view(), name='alipay-callback'),
]
