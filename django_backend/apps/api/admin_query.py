"""Allowlisted search, filtering, and ordering for Admin list endpoints."""

from django.db.models import Q

from apps.api.views.helpers import bad_request, pagination_from_request

GLOBAL_QUERY_PARAMETERS = frozenset({"limit", "offset", "search", "ordering"})
MAX_SEARCH_LENGTH = 200
MAX_FILTER_VALUE_LENGTH = 200


def apply_admin_query(
    request,
    queryset,
    *,
    search_fields=(),
    filters=None,
    ordering_fields=None,
):
    """Apply endpoint-defined query options without accepting client ORM paths."""
    filter_map = filters or {}
    allowed_parameters = GLOBAL_QUERY_PARAMETERS | frozenset(filter_map)
    unknown_parameters = sorted(set(request.query_params) - allowed_parameters)
    if unknown_parameters:
        return None, bad_request(
            "invalid_query_parameter",
            f"Unsupported query parameter: {unknown_parameters[0]}.",
        )

    _pagination, pagination_error = pagination_from_request(request)
    if pagination_error:
        return None, pagination_error

    search = request.query_params.get("search", "").strip()
    if len(search) > MAX_SEARCH_LENGTH:
        return None, bad_request(
            "invalid_search",
            f"`search` must be at most {MAX_SEARCH_LENGTH} characters.",
        )
    if search and search_fields:
        search_query = Q()
        for field_name in search_fields:
            search_query |= Q(**{f"{field_name}__icontains": search})
        queryset = queryset.filter(search_query)

    for parameter, query_filter in filter_map.items():
        value = request.query_params.get(parameter, "").strip()
        if not value:
            continue
        if len(value) > MAX_FILTER_VALUE_LENGTH:
            return None, bad_request(
                "invalid_filter",
                f"`{parameter}` must be at most {MAX_FILTER_VALUE_LENGTH} characters.",
            )
        try:
            if callable(query_filter):
                queryset = query_filter(queryset, value)
            else:
                queryset = queryset.filter(**{query_filter: value})
        except (TypeError, ValueError) as exc:
            return None, bad_request("invalid_filter", str(exc))

    ordering = request.query_params.get("ordering", "").strip()
    if ordering:
        descending = ordering.startswith("-")
        requested_field = ordering[1:] if descending else ordering
        orm_field = (ordering_fields or {}).get(requested_field)
        if not requested_field or not orm_field:
            return None, bad_request(
                "invalid_ordering",
                f"Unsupported ordering field: {requested_field or ordering}.",
            )
        queryset = queryset.order_by(f"-{orm_field}" if descending else orm_field)

    return queryset, None
