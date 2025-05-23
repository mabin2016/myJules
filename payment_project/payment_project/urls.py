"""
URL configuration for payment_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # API URL Namespaces
    # It's good practice to version your APIs
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/transactions/', include('apps.transactions.urls')),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), # Optional: for DRF browsable API login
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # In development, you might also serve media files if you have them
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
