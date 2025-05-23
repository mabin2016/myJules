from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
# The basename is important if your ViewSet doesn't have a queryset or you want to override the URL name prefix.
# For ModelViewSet with a queryset, DRF can often infer it. Explicit is good.

urlpatterns = [
    path('', include(router.urls)),
    # You can add other user-related non-ViewSet URLs here if needed.
]
