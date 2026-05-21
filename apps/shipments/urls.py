from rest_framework.routers import DefaultRouter
from .views import ShipmentGroupViewSet

router = DefaultRouter()
router.register(r'', ShipmentGroupViewSet, basename='shipmentgroups')

urlpatterns = router.urls
