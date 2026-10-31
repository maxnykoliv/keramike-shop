from typing import Any

from django.core.files.storage import default_storage
from rest_framework import serializers

from apps.catalog.models import Product, ProductImage
from apps.core.money import format_uah


def image_url(image: ProductImage, size: str = "md") -> str:
    key = image.variants.get(size)
    if key:
        return default_storage.url(key)
    return image.image.url if image.image else ""


class ImageSerializer(serializers.ModelSerializer):
    urls = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["kind", "alt", "urls"]

    def get_urls(self, obj: ProductImage) -> dict[str, str]:
        return {size: image_url(obj, size) for size in ("sm", "md", "lg")}


class ProductCardSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    m2_per_pack = serializers.SerializerMethodField()
    manufacturer = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "slug", "sku", "name", "kind", "unit", "price_kop", "old_price_kop",
                  "price_display", "stock_status", "image", "size", "m2_per_pack",
                  "manufacturer"]

    def get_price_display(self, obj: Product) -> str:
        return format_uah(obj.price_kop)

    def get_image(self, obj: Product) -> str | None:
        images = list(obj.images.all())
        return image_url(images[0]) if images else None

    def get_size(self, obj: Product) -> str | None:
        spec = getattr(obj, "tile_spec", None)
        return f"{spec.width_mm}x{spec.height_mm}" if spec else None

    def get_m2_per_pack(self, obj: Product) -> str | None:
        spec = getattr(obj, "tile_spec", None)
        return str(spec.effective_m2_per_pack) if spec else None

    def get_manufacturer(self, obj: Product) -> str | None:
        return obj.collection.manufacturer.name if obj.collection else None


class ProductDetailSerializer(ProductCardSerializer):
    images = ImageSerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    collection = serializers.SerializerMethodField()
    tile_spec = serializers.SerializerMethodField()
    material_spec = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()

    class Meta(ProductCardSerializer.Meta):
        fields = [*ProductCardSerializer.Meta.fields, "description", "seo_title",
                  "seo_description", "images", "category", "collection", "tile_spec",
                  "material_spec", "related"]

    def get_category(self, obj: Product) -> dict[str, str]:
        return {"slug": obj.category.slug, "name": obj.category.name}

    def get_collection(self, obj: Product) -> dict[str, str] | None:
        if not obj.collection:
            return None
        return {"slug": obj.collection.slug, "name": obj.collection.name}

    def get_tile_spec(self, obj: Product) -> dict[str, Any] | None:
        spec = getattr(obj, "tile_spec", None)
        if spec is None:
            return None
        return {
            "width_mm": spec.width_mm,
            "height_mm": spec.height_mm,
            "thickness_mm": spec.thickness_mm,
            "m2_per_pack": str(spec.effective_m2_per_pack),
            "pcs_per_pack": spec.pcs_per_pack,
            "pack_weight_kg": str(spec.pack_weight_kg) if spec.pack_weight_kg else None,
            "material": spec.material,
            "surface": spec.surface,
            "color": spec.color,
            "applications": spec.applications,
            "rooms": spec.rooms,
        }

    def get_material_spec(self, obj: Product) -> dict[str, Any] | None:
        spec = getattr(obj, "material_spec", None)
        if spec is None:
            return None
        return {"pack_size": str(spec.pack_size), "pack_unit": spec.pack_unit,
                "consumption_hint": spec.consumption_hint}

    def get_related(self, obj: Product) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = {"same_collection": [], "recommended": []}
        for relation in obj.relations.all():
            if relation.related.status != Product.Status.ACTIVE:
                continue
            groups[relation.type].append(ProductCardSerializer(relation.related).data)
        return groups
