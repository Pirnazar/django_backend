from rest_framework.routers import DefaultRouter
from .views import PaymentTransactionViewSet

router = DefaultRouter()
router.register(r'', PaymentTransactionViewSet, basename='payments')

urlpatterns = router.urls
