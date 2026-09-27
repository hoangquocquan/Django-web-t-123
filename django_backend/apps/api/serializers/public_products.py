"""Dedicated serializers for editorial and anonymous public product contracts."""

from rest_framework import serializers

from apps.business_core.models import BusinessProduct, PublicProductProjection


class PublicProductProjectionAdminSerializer(serializers.ModelSerializer):
    """Validate Admin projection content without reusing a master-data serializer."""

    source_product_id = serializers.PrimaryKeyRelatedField(
        source="source_product",
        queryset=BusinessProduct.objects.all(),
    )

    class Meta:
        model = PublicProductProjection
        fields = (
            "public_id",
            "source_product_id",
            "title",
            "slug",
            "public_description",
            "public_material",
            "public_specifications",
            "category",
            "main_image",
            "seo_title",
            "seo_description",
            "display_order",
            "publication_status",
            "published_at",
        )
        read_only_fields = ("public_id", "published_at")

    def validate_public_material(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be an object.")
        allowed = {"code", "name"}
        if set(value) - allowed:
            raise serializers.ValidationError("Only code and name are supported.")
        return value

    def validate_public_specifications(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list.")
        for item in value:
            if not isinstance(item, dict) or set(item) - {"label", "value"}:
                raise serializers.ValidationError(
                    "Each specification must contain only label and value."
                )
            if not str(item.get("label", "")).strip() or not str(
                item.get("value", "")
            ).strip():
                raise serializers.ValidationError("Label and value are required.")
        return value


class PublicProductSerializer(serializers.Serializer):
    """Allowlisted anonymous projection that never serializes BusinessProduct."""

    id = serializers.SerializerMethodField()
    slug = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(source="public_description")
    material = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    category = serializers.CharField()
    image = serializers.SerializerMethodField()
    seo = serializers.SerializerMethodField()

    def get_id(self, projection):
        return str(projection.public_id)

    def get_image(self, projection):
        if not projection.main_image:
            return None
        return {"url": projection.main_image, "alt": projection.title}

    def get_material(self, projection):
        material = projection.public_material
        if not isinstance(material, dict):
            return {}
        return {
            key: material[key]
            for key in ("code", "name")
            if isinstance(material.get(key), str)
        }

    def get_specifications(self, projection):
        specifications = projection.public_specifications
        if not isinstance(specifications, list):
            return []
        return [
            {"label": item["label"], "value": item["value"]}
            for item in specifications
            if isinstance(item, dict)
            and isinstance(item.get("label"), str)
            and isinstance(item.get("value"), str)
        ]

    def get_seo(self, projection):
        return {
            "title": projection.seo_title or None,
            "description": projection.seo_description or None,
        }


