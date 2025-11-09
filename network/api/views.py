from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from network.models import Product, Unit

from .permissions import IsActiveStaff
from .serializers import ProductSerializer, UnitSerializer


class UnitViewSet(ModelViewSet):
    queryset = Unit.objects.select_related("supplier").prefetch_related("products")
    serializer_class = UnitSerializer
    permission_classes = [IsActiveStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country"]
    search_fields = ["name", "city", "country", "email"]
    ordering_fields = ["name", "city", "country", "created_at"]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsActiveStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["released_at"]
    search_fields = ["name", "model"]
    ordering_fields = ["name", "model", "released_at"]
