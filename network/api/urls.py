from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, UnitViewSet

app_name = "network"

router = DefaultRouter()
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]
