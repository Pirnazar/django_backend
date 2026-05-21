from rest_framework.routers import DefaultRouter
from .views import (
    ItemViewSet, ItemExpenseViewSet, ItemPhotoViewSet,
    AttachmentViewSet, BoxViewSet,
)

router = DefaultRouter()
router.register(r'expenses', ItemExpenseViewSet, basename='expenses')
router.register(r'photos', ItemPhotoViewSet, basename='photos')
router.register(r'attachments', AttachmentViewSet, basename='attachments')
router.register(r'boxes', BoxViewSet, basename='boxes')
router.register(r'', ItemViewSet, basename='items')

urlpatterns = router.urls
