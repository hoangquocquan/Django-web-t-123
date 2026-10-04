"""Strict Admin and anonymous serializers for managed Capability content."""

from rest_framework import serializers

from apps.business_core.models import Capability


class CapabilityAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capability
        fields = (
            "id",
            "title",
            "slug",
            "short_description",
            "description",
            "image",
            "technology_type",
            "process_category",
            "display_order",
            "is_active",
            "status",
            "published_at",
            "seo_title",
            "seo_description",
        )
        read_only_fields = ("id", "published_at")


class PublicCapabilitySerializer(serializers.Serializer):
    """Allowlist the complete anonymous Capability contract."""

    id = serializers.IntegerField()
    slug = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    image = serializers.SerializerMethodField()
    technology_type = serializers.CharField()
    process_category = serializers.CharField()

    def get_image(self, capability):
        return capability.image or None


