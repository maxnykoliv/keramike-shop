from decimal import Decimal

from rest_framework import serializers

from apps.calc.engine.types import Layout, Room, SurfaceKind


class OpeningSerializer(serializers.Serializer):
    width_m = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.1"))
    height_m = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.1"))
    count = serializers.IntegerField(min_value=1, max_value=20, default=1)


class ManualTileSerializer(serializers.Serializer):
    width_mm = serializers.IntegerField(min_value=10, max_value=3200)
    height_mm = serializers.IntegerField(min_value=10, max_value=3200)
    thickness_mm = serializers.IntegerField(min_value=3, max_value=40, default=8)
    price_kop_per_m2 = serializers.IntegerField(min_value=0)
    m2_per_pack = serializers.DecimalField(max_digits=7, decimal_places=3, required=False,
                                           min_value=Decimal("0.01"))
    pcs_per_pack = serializers.IntegerField(min_value=1, required=False)
    pack_weight_kg = serializers.DecimalField(max_digits=7, decimal_places=3, required=False)

    def validate(self, attrs):
        if not attrs.get("m2_per_pack") and not attrs.get("pcs_per_pack"):
            raise serializers.ValidationError("Вкажіть м² або кількість штук в упаковці")
        return attrs


class SurfaceSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=[k.value for k in SurfaceKind])
    product_id = serializers.IntegerField(required=False)
    tile = ManualTileSerializer(required=False)
    layout = serializers.ChoiceField(choices=[k.value for k in Layout], default="straight")
    joint_mm = serializers.DecimalField(max_digits=4, decimal_places=1, default=Decimal("2"),
                                        min_value=Decimal("0.5"), max_value=Decimal("20"))
    length_m = serializers.DecimalField(max_digits=6, decimal_places=3, required=False)
    width_m = serializers.DecimalField(max_digits=6, decimal_places=3, required=False)
    height_m = serializers.DecimalField(max_digits=6, decimal_places=3, required=False)
    area_m2 = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    openings = OpeningSerializer(many=True, required=False)

    def validate(self, attrs):
        if bool(attrs.get("product_id")) == bool(attrs.get("tile")):
            raise serializers.ValidationError("Оберіть плитку з каталогу або вкажіть її вручну")
        if attrs.get("area_m2") is None:
            needed = ["length_m", "width_m"]
            if attrs["kind"] == SurfaceKind.WALLS:
                needed.append("height_m")
            missing = [name for name in needed if attrs.get(name) is None]
            if missing:
                raise serializers.ValidationError(
                    {name: "Вкажіть розмір або готову площу" for name in missing}
                )
        return attrs


class IncludeSerializer(serializers.Serializer):
    glue = serializers.BooleanField(default=True)
    grout = serializers.BooleanField(default=True)
    primer = serializers.BooleanField(default=True)
    waterproofing = serializers.BooleanField(default=True)
    labor = serializers.BooleanField(default=True)


class CalcInputSerializer(serializers.Serializer):
    room = serializers.ChoiceField(choices=[r.value for r in Room], default="other")
    surfaces = SurfaceSerializer(many=True, min_length=1, max_length=10)  # type: ignore[call-arg]
    include = IncludeSerializer(required=False)

    def validate(self, attrs):
        attrs.setdefault("include", IncludeSerializer().to_internal_value({}))
        return attrs


class EstimateCreateSerializer(CalcInputSerializer):
    # DRF removes declared fields from class attributes, so this does not shadow Field.source.
    source = serializers.ChoiceField(  # type: ignore[assignment]
        choices=["calculator", "product_card"], default="calculator"
    )
    title = serializers.CharField(max_length=120, required=False, default="", allow_blank=True)


# Response serializers exist only for the OpenAPI schema (the source of the frontend's TS types).
class SurfaceResultSerializer(serializers.Serializer):
    kind = serializers.CharField()
    area_m2 = serializers.CharField()
    area_with_waste_m2 = serializers.CharField()
    packs = serializers.IntegerField()


class LineResultSerializer(serializers.Serializer):
    kind = serializers.CharField()
    name = serializers.CharField()
    product_id = serializers.IntegerField(allow_null=True)
    quantity = serializers.CharField()
    unit = serializers.CharField()
    quantity_base = serializers.CharField()
    base_unit = serializers.CharField()
    total_kop = serializers.IntegerField()
    weight_kg = serializers.CharField()
    surface_index = serializers.IntegerField(allow_null=True)


class WarningSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    surface_index = serializers.IntegerField(allow_null=True)


class CalcResultSerializer(serializers.Serializer):
    settings_version = serializers.IntegerField()
    surfaces = SurfaceResultSerializer(many=True)
    lines = LineResultSerializer(many=True)
    total_kop = serializers.IntegerField()
    weight_kg = serializers.CharField()
    warnings = WarningSerializer(many=True)


class EstimateCreatedSerializer(serializers.Serializer):
    code = serializers.CharField()
    result = CalcResultSerializer()


class EstimateDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    created_at = serializers.DateTimeField()
    input = serializers.JSONField()
    result = CalcResultSerializer()
    current = CalcResultSerializer(allow_null=True)
    changed = serializers.BooleanField()


class PdfStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ready", "rendering"])
    url = serializers.CharField(required=False)


class AccountEstimateSerializer(serializers.Serializer):
    code = serializers.CharField(source="public_code")
    title = serializers.CharField()
    total_kop = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    room = serializers.SerializerMethodField()

    def get_room(self, obj) -> str:
        return obj.input.get("room", "other")
