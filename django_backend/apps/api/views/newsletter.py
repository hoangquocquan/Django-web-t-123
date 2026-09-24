"""Django-owned newsletter API views."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.serializers.newsletter import (
    NewsletterSubscribeSerializer,
    newsletter_subscriber_to_dict,
)
from apps.api.views.helpers import paginated_ok
from apps.newsletter.services import NewsletterService


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def subscribers(request):
    """List subscribers or create a Django-owned subscription."""
    service = NewsletterService()
    if request.method == "GET":
        return paginated_ok(request, service.list_subscribers(), newsletter_subscriber_to_dict)

    serializer = NewsletterSubscribeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    subscriber, created = service.subscribe(
        email=serializer.validated_data["email"],
        source=serializer.validated_data.get("source", "website"),
    )
    return Response(
        {
            "success": True,
            "created": created,
            "data": newsletter_subscriber_to_dict(subscriber),
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )
