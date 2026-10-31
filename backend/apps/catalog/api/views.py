from functools import wraps

from django.core.cache import cache
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog import selectors
from apps.catalog.api.filters import ProductFilter
from apps.catalog.api.serializers import ProductCardSerializer, ProductDetailSerializer
from apps.customers.selectors import is_master

CACHE_TIMEOUT = 300


def cached_get(view_method):
    """Caches catalog GET responses. The key includes a version that saving a product bumps."""

    @wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        key = f"catalog:v{selectors.catalog_cache_version()}:{request.get_full_path()}"
        data = cache.get(key)
        if data is None:
            response = view_method(self, request, *args, **kwargs)
            if response.status_code != 200:
                return response
            data = response.data
            cache.set(key, data, CACHE_TIMEOUT)
        return Response(data)

    return wrapper


class CategoryTreeView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT, description="Дерево: slug, name, children")
    @cached_get
    def get(self, request):
        return Response(selectors.category_tree())


class ProductListView(ListAPIView):
    serializer_class = ProductCardSerializer
    filterset_class = ProductFilter

    def get_queryset(self) -> QuerySet:
        return selectors.public_products()

    @cached_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class FacetsView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT, description="Ті самі фільтри, що й /products")
    @cached_get
    def get(self, request):
        qs = ProductFilter(request.GET, queryset=selectors.public_products()).qs
        return Response(selectors.facets(qs))


class ProductDetailView(APIView):
    @extend_schema(responses=ProductDetailSerializer)
    @cached_get
    def get(self, request, slug: str):
        product = selectors.get_public_product(slug)
        return Response(ProductDetailSerializer(product).data)


class SearchView(APIView):
    @extend_schema(parameters=[OpenApiParameter("q", str)],
                   responses=ProductCardSerializer(many=True))
    def get(self, request):
        query = request.GET.get("q", "")
        if len(query.strip()) < 2:
            return Response([])
        return Response(ProductCardSerializer(selectors.search_products(query), many=True).data)


class PersonalPricesView(APIView):
    """Prices for the current customer. The catalog is cached with retail prices for everyone,
    and the site overlays master prices using this request."""

    @extend_schema(
        request=inline_serializer("PricesRequest", {
            "ids": serializers.ListField(child=serializers.IntegerField(), max_length=200)}),
        responses=inline_serializer("PricesResponse", {
            "is_master": serializers.BooleanField(),
            "prices": serializers.DictField(child=serializers.IntegerField())}),
    )
    def post(self, request):
        ids = [int(i) for i in (request.data.get("ids") or [])[:200] if str(i).isdigit()]
        master = is_master(request)
        prices = selectors.personal_prices(ids, master=master)
        return Response({"is_master": master, "prices": {str(k): v for k, v in prices.items()}})
