from django.urls import path

from .builder_views import GroupBuilderView, GroupBuilderItemsView, GroupBuilderCreateView

urlpatterns = [
    path('',           GroupBuilderView.as_view(),       name='shipment-group-builder'),
    path('api/items/', GroupBuilderItemsView.as_view(),  name='builder-api-items'),
    path('api/create/', GroupBuilderCreateView.as_view(), name='builder-api-create'),
]
