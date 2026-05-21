from rest_framework.routers import DefaultRouter
from .views import PriceRuleViewSet

router = DefaultRouter()
router.register(r'', PriceRuleViewSet, basename='pricerules')

urlpatterns = router.urls
