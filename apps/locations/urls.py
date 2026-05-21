from rest_framework.routers import DefaultRouter
from .views import DestinationViewSet, WarehouseViewSet

router = DefaultRouter()
router.register(r'destinations', DestinationViewSet, basename='destinations')
router.register(r'warehouses', WarehouseViewSet, basename='warehouses')

urlpatterns = router.urls
