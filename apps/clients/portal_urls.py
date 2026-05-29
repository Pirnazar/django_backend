"""Client-facing mobile portal URLs, mounted at /api/v1/client/."""
from django.urls import path

from .portal_views import (
    ClientProfileView,
    AvailableServicesView,
    CargoServicesView,
)

urlpatterns = [
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path('services/', AvailableServicesView.as_view(), name='client-services'),
    path('cargos/<int:cargo_id>/services/', CargoServicesView.as_view(), name='client-cargo-services'),
]
