from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin custom pages must come BEFORE the admin catch-all
    path('admin/dashboard/', include('apps.dashboard.admin_urls')),
    path('admin/shipment-group-builder/', include('apps.shipments.builder_urls')),
    path('admin/', admin.site.urls),
    
    # OpenAPI endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # App endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/locations/', include('apps.locations.urls')),
    path('api/v1/clients/', include('apps.clients.urls')),
    path('api/v1/client/', include('apps.clients.portal_urls')),
    path('api/v1/pricing/', include('apps.pricing.urls')),
    path('api/v1/items/', include('apps.items.urls')),
    path('api/v1/shipments/', include('apps.shipments.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/devices/', include('apps.notifications.device_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
