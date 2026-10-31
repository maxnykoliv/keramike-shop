import django_filters
from django.db.models import Q, QuerySet

from apps.catalog.models import Product, TileSpec


class ProductFilter(django_filters.FilterSet):
    ids = django_filters.BaseInFilter(field_name="id", help_text="Через кому: 1,2,3")
    kind = django_filters.MultipleChoiceFilter(choices=Product.Kind.choices)
    category = django_filters.CharFilter(method="filter_category")
    application = django_filters.ChoiceFilter(choices=TileSpec.Application.choices,
                                              method="filter_application")
    room = django_filters.ChoiceFilter(choices=TileSpec.Room.choices, method="filter_room")
    size = django_filters.CharFilter(method="filter_size", help_text="Наприклад 600x600")
    color = django_filters.CharFilter(field_name="tile_spec__color", lookup_expr="iexact")
    surface = django_filters.CharFilter(field_name="tile_spec__surface", lookup_expr="iexact")
    material = django_filters.ChoiceFilter(field_name="tile_spec__material",
                                           choices=TileSpec.Material.choices)
    manufacturer = django_filters.CharFilter(field_name="collection__manufacturer__slug")
    collection = django_filters.CharFilter(field_name="collection__slug")
    price_min = django_filters.NumberFilter(field_name="price_kop", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price_kop", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")
    ordering = django_filters.OrderingFilter(
        fields=(("price_kop", "price"), ("created_at", "new"), ("name", "name"))
    )

    class Meta:
        model = Product
        fields: list[str] = []

    def filter_category(self, qs: QuerySet, name: str, value: str) -> QuerySet:
        return qs.filter(Q(category__slug=value) | Q(category__parent__slug=value))

    def filter_application(self, qs: QuerySet, name: str, value: str) -> QuerySet:
        return qs.filter(tile_spec__applications__contains=[value])

    def filter_room(self, qs: QuerySet, name: str, value: str) -> QuerySet:
        return qs.filter(tile_spec__rooms__contains=[value])

    def filter_size(self, qs: QuerySet, name: str, value: str) -> QuerySet:
        try:
            a, b = (int(part) for part in value.lower().replace("×", "x").split("x"))
        except ValueError:
            return qs.none()
        return qs.filter(
            Q(tile_spec__width_mm=a, tile_spec__height_mm=b)
            | Q(tile_spec__width_mm=b, tile_spec__height_mm=a)
        )

    def filter_in_stock(self, qs: QuerySet, name: str, value: bool) -> QuerySet:
        if value:
            return qs.filter(stock_status=Product.StockStatus.IN_STOCK)
        return qs
