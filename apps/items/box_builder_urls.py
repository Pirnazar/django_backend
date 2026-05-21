from django.urls import path

from .box_builder_views import (
    BoxBuilderView,
    BoxBuilderCreateView,
    BoxBuilderScanView,
    BoxBuilderRemoveView,
    BoxBuilderCloseView,
    BoxBuilderPrintedView,
)

urlpatterns = [
    path('',                            BoxBuilderView.as_view(),         name='box-builder'),
    path('api/create/',                 BoxBuilderCreateView.as_view(),   name='box-builder-create'),
    path('api/<int:box_id>/scan/',      BoxBuilderScanView.as_view(),     name='box-builder-scan'),
    path('api/<int:box_id>/remove/',    BoxBuilderRemoveView.as_view(),   name='box-builder-remove'),
    path('api/<int:box_id>/close/',     BoxBuilderCloseView.as_view(),    name='box-builder-close'),
    path('api/<int:box_id>/printed/',   BoxBuilderPrintedView.as_view(),  name='box-builder-printed'),
]
