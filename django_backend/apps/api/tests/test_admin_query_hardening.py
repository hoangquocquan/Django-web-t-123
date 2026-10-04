"""Security and compatibility tests for allowlisted admin list queries."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
    InventoryItem,
    InventoryWarehouse,
)
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.transaction_domain.models import (
    TransactionHistory,
    TransactionOrder,
    WorkflowApproval,
)

ENDPOINT_MODULES = {
    "/api/v1/admin/products/": "products",
    "/api/v1/admin/customers/": "customers",
    "/api/v1/admin/inventory/items/": "inventory",
    "/api/v1/admin/orders/": "orders",
    "/api/v1/admin/workflows/": "workflows",
    "/api/v1/admin/transactions/": "transactions",
}


def _headers_for(module, *, suffix=None):
    suffix = suffix or module
    permission, _created = FoundationPermission.objects.get_or_create(
        module=module,
        action="read",
        defaults={
            "code": f"admin-query:{module}:read",
            "description": "Focused admin query test permission",
        },
    )
    role = FoundationRole.objects.create(name=f"admin-query-{suffix}")
    role.permissions.add(permission)
    user = FoundationUser.objects.create(
        email=f"{suffix}@admin-query.example",
        full_name=f"Admin query {suffix}",
        password_hash="not-a-real-password",
        role=role,
    )
    raw_token = f"admin-query-{suffix}-token"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}, user


@pytest.fixture
def admin_query_context(db):
    headers = {}
    users = {}
    for module in ENDPOINT_MODULES.values():
        headers[module], users[module] = _headers_for(module)

    unrelated_headers, _user = _headers_for("dashboard", suffix="unrelated")

    material_steel = BusinessMaterial.objects.create(
        material_code="SUS304",
        name="Stainless Steel",
        created_by=users["products"],
    )
    material_aluminum = BusinessMaterial.objects.create(
        material_code="AL6061",
        name="Aluminum",
        created_by=users["products"],
    )
    product_alpha = BusinessProduct.objects.create(
        name="Alpha Bracket",
        slug="admin-query-alpha-bracket",
        sku="AQ-ALPHA",
        part_code="AQ-P-001",
        default_material=material_steel,
        status="published",
        is_active=True,
    )
    BusinessProduct.objects.create(
        name="Beta Plate",
        slug="admin-query-beta-plate",
        sku="AQ-BETA",
        part_code="AQ-P-002",
        default_material=material_aluminum,
        status="draft",
        is_active=False,
    )
    customer_alpha = BusinessCustomer.objects.create(
        company_name="Alpha Manufacturing",
        contact_name="Alice",
        status="active",
    )
    customer_beta = BusinessCustomer.objects.create(
        company_name="Beta Industries",
        contact_name="Bob",
        status="lead",
    )
    warehouse = InventoryWarehouse.objects.create(code="AQ-WH", name="Query Warehouse")
    InventoryItem.objects.create(
        product=product_alpha,
        warehouse=warehouse,
        quantity="10",
        reserved_quantity="2",
    )
    order_alpha = TransactionOrder.objects.create(
        order_number="AQ-ORDER-001",
        customer=customer_alpha,
        status="approved",
        workflow_status="CONFIRMED",
        ordered_at=timezone.now(),
    )
    TransactionOrder.objects.create(
        order_number="AQ-ORDER-002",
        customer=customer_beta,
        status="new",
        workflow_status="ON_HOLD",
        ordered_at=timezone.now() - timedelta(days=1),
    )
    WorkflowApproval.objects.create(
        order=order_alpha,
        requested_status="approved",
        decision="approved",
        requested_by="alice",
        note="Reviewed query fixture",
    )
    TransactionHistory.objects.create(
        order=order_alpha,
        entity_type="order",
        entity_id=str(order_alpha.pk),
        action="approved",
        actor="alice",
    )
    return {
        "headers": headers,
        "unrelated_headers": unrelated_headers,
        "warehouse": warehouse,
    }


@pytest.mark.django_db
@pytest.mark.parametrize("endpoint,module", ENDPOINT_MODULES.items())
def test_admin_list_requires_exact_module_read_permission(
    client, admin_query_context, endpoint, module
):
    assert client.get(endpoint).status_code == 403
    assert (
        client.get(endpoint, **admin_query_context["unrelated_headers"]).status_code
        == 403
    )
    assert (
        client.get(endpoint, **admin_query_context["headers"][module]).status_code
        == 200
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "parameter", ["password", "customer__email", "role__permissions", "foo"]
)
def test_unknown_query_parameters_and_orm_paths_are_rejected(
    client, admin_query_context, parameter
):
    response = client.get(
        "/api/v1/admin/products/",
        {parameter: "probe"},
        **admin_query_context["headers"]["products"],
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_query_parameter"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ordering", ["password", "role__permissions", "customer__email", "user__password"]
)
def test_arbitrary_ordering_paths_are_rejected(client, admin_query_context, ordering):
    response = client.get(
        "/api/v1/admin/products/",
        {"ordering": ordering},
        **admin_query_context["headers"]["products"],
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_ordering"


@pytest.mark.django_db
def test_product_query_is_allowlisted_and_preserves_response_shape(
    client, admin_query_context
):
    response = client.get(
        "/api/v1/admin/products/",
        {
            "search": "SUS304",
            "status": "published",
            "active": "true",
            "ordering": "-name",
        },
        **admin_query_context["headers"]["products"],
    )
    assert response.status_code == 200
    result = response.json()["data"]["results"]
    assert [item["name"] for item in result] == ["Alpha Bracket"]
    assert (
        not {
            "part_code",
            "unit",
            "default_material",
            "tolerance",
            "is_active",
            "archived_at",
        }
        & result[0].keys()
    )


@pytest.mark.django_db
def test_descending_order_and_offset_are_applied(client, admin_query_context):
    response = client.get(
        "/api/v1/admin/products/",
        {"ordering": "-name", "limit": "1", "offset": "1"},
        **admin_query_context["headers"]["products"],
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert data["count"] == 2
    assert [item["name"] for item in data["results"]] == ["Alpha Bracket"]


@pytest.mark.django_db
def test_each_admin_list_applies_only_documented_filters(client, admin_query_context):
    cases = (
        (
            "customers",
            "/api/v1/admin/customers/",
            {"search": "Alice", "status": "active"},
        ),
        (
            "inventory",
            "/api/v1/admin/inventory/items/",
            {"warehouse": "AQ-WH", "availability": "positive"},
        ),
        (
            "orders",
            "/api/v1/admin/orders/",
            {"search": "AQ-ORDER-001", "workflow_status": "confirmed"},
        ),
        (
            "workflows",
            "/api/v1/admin/workflows/",
            {"decision": "approved", "requested_status": "approved"},
        ),
        (
            "transactions",
            "/api/v1/admin/transactions/",
            {"entity_type": "order", "action": "approved"},
        ),
    )
    for module, endpoint, query in cases:
        response = client.get(endpoint, query, **admin_query_context["headers"][module])
        assert response.status_code == 200
        assert response.json()["data"]["count"] == 1

    inventory_result = client.get(
        "/api/v1/admin/inventory/items/",
        **admin_query_context["headers"]["inventory"],
    ).json()["data"]["results"][0]
    assert "available_quantity" not in inventory_result

    order_result = client.get(
        "/api/v1/admin/orders/", **admin_query_context["headers"]["orders"]
    ).json()["data"]["results"][0]
    assert (
        not {"workflow_status", "progress_percent", "expected_delivery_date"}
        & order_result.keys()
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("endpoint", "query", "code"),
    [
        ("/api/v1/admin/products/", {"active": "yes"}, "invalid_filter"),
        ("/api/v1/admin/inventory/items/", {"availability": "all"}, "invalid_filter"),
        ("/api/v1/admin/products/", {"search": "x" * 201}, "invalid_search"),
        ("/api/v1/admin/products/", {"limit": "many"}, "invalid_pagination"),
    ],
)
def test_invalid_admin_query_values_fail_closed(
    client, admin_query_context, endpoint, query, code
):
    module = ENDPOINT_MODULES[endpoint]
    response = client.get(endpoint, query, **admin_query_context["headers"][module])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == code


@pytest.mark.django_db
def test_admin_pagination_is_bounded(client, admin_query_context):
    response = client.get(
        "/api/v1/admin/products/",
        {"limit": "1000", "offset": "0"},
        **admin_query_context["headers"]["products"],
    )
    assert response.status_code == 200
    assert response.json()["data"]["limit"] == 100
