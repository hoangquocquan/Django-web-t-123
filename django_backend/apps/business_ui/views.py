"""Django views cho giao dien business van hanh hang ngay.

Module nay chi doc/ghi qua cac service va model Django da migrate. Muc tieu la
cho nguoi dung thu nghiem Sales, CRM va AI Sales tren trinh duyet ma khong can
dung Postman hay goi API thu cong.
"""

from __future__ import annotations

from decimal import Decimal
from functools import wraps

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.services.crm_platform_service import CrmPlatformService
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.document_intelligence import DocumentIntelligenceService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation
from apps.sales.services.sales_platform_service import SalesPlatformService

ADMIN_TOKEN_SESSION_KEY = "foundation_admin_token"
PIPELINE_COLUMNS = [
    "new",
    "contacted",
    "meeting",
    "quotation",
    "negotiation",
    "won",
    "lost",
]

# Kanban chỉ hiển thị các lead mới cập nhật gần đây để trang không phình to
# khi dữ liệu thực tế tăng lên hàng nghìn bản ghi.
PIPELINE_COLUMN_LIMIT = 25
BUSINESS_NAVIGATION = [
    {
        "key": "dashboard",
        "label": "Dashboard",
        "url": "/business/",
        "module": "dashboard",
    },
    {
        "key": "leads",
        "label": "Lead Pipeline",
        "url": "/business/leads/",
        "module": "sales",
    },
    {
        "key": "customers",
        "label": "CRM Customers",
        "url": "/business/customers/",
        "module": "crm",
    },
    {
        "key": "quotations",
        "label": "Quotations",
        "url": "/business/quotations/",
        "module": "sales",
    },
    {
        "key": "ai-sales",
        "label": "AI Sales",
        "url": "/business/ai-sales/",
        "module": "ai_sales",
    },
    {
        "key": "documents",
        "label": "AI Documents",
        "url": "/business/documents/",
        "module": "knowledge",
    },
]


def _current_user(request):
    """Lay user dang dang nhap tu session CMS admin.

    Business UI dung chung token voi `/admin/login/` de nguoi hoc khong phai
    dang nhap nhieu lan. Neu token het han, nguoi dung duoc dua ve trang login.
    """
    raw_token = request.session.get(ADMIN_TOKEN_SESSION_KEY, "")
    if not raw_token:
        raise PermissionDenied("Business UI requires admin login.")
    return FoundationAuthService().authenticate_token(raw_token)


def business_permission(module, action="read"):
    """Protect one Business UI view with its real module permission."""

    def decorator(view_function):
        @wraps(view_function)
        def wrapped(request, *args, **kwargs):
            if not request.session.get(ADMIN_TOKEN_SESSION_KEY):
                return redirect("admin_ui:login")
            user = _current_user(request)
            FoundationPermissionService().require_permission(user, module, action)
            request.business_user = user
            return view_function(request, *args, **kwargs)

        return wrapped

    return decorator


def _business_context(request, active, module, extra=None):
    """Tao context chung cho moi template business."""
    user = getattr(request, "business_user", None) or _current_user(request)
    permission_service = FoundationPermissionService()
    permission_service.require_permission(user, module, "read")
    context = {
        "admin_user": user,
        "active": active,
        "navigation": [
            item
            for item in BUSINESS_NAVIGATION
            if permission_service.has_permission(user, item["module"], "read")
        ],
        "can_write": permission_service.has_permission(user, module, "write"),
        "can_approve_sales": permission_service.has_permission(
            user, "sales", "approve"
        ),
    }
    context.update(extra or {})
    return context


def _render_business(request, template, active, module, context=None):
    """Render an already authorized Business UI page."""
    return render(
        request, template, _business_context(request, active, module, context)
    )


def _sales_metrics():
    """Tinh cac chi so sales de hien tren dashboard."""
    total_leads = SalesLead.objects.count()
    won_leads = SalesLead.objects.filter(status="won").count()
    open_opportunities = SalesOpportunity.objects.exclude(status__in=["won", "lost"])
    pipeline_value = sum((item.value for item in open_opportunities), Decimal(0))
    revenue_forecast = sum(
        (
            item.value * Decimal(item.probability) / Decimal(100)
            for item in open_opportunities
        ),
        Decimal(0),
    )
    conversion_rate = round((won_leads / total_leads) * 100, 1) if total_leads else 0
    return {
        "lead_count": total_leads,
        "pipeline_value": pipeline_value,
        "conversion_rate": conversion_rate,
        "revenue_forecast": revenue_forecast,
        "performance": [
            {"status": status, "count": SalesLead.objects.filter(status=status).count()}
            for status in PIPELINE_COLUMNS
        ],
    }


@business_permission("dashboard")
def dashboard(request):
    """Hien thi dashboard Sales/CRM tong quan."""
    context = {
        "metrics": _sales_metrics(),
        "recent_leads": SalesLead.objects.select_related("owner").order_by(
            "-updated_at", "-id"
        )[:6],
        "recent_quotations": SalesQuotation.objects.select_related("customer").order_by(
            "-updated_at", "-id"
        )[:6],
    }
    return _render_business(
        request, "business_ui/dashboard.html", "dashboard", "dashboard", context
    )


@business_permission("sales")
def lead_pipeline(request):
    """Hien thi pipeline Kanban gom cac lead theo trang thai."""
    columns = [
        {
            "status": status,
            "label": dict(SalesLead.STATUS_CHOICES).get(status, status.title()),
            "leads": SalesLead.objects.select_related("owner")
            .filter(status=status)
            .order_by("-updated_at", "-id")[:PIPELINE_COLUMN_LIMIT],
            "total": SalesLead.objects.filter(status=status).count(),
        }
        for status in PIPELINE_COLUMNS
    ]
    context = {
        "columns": columns,
        "owners": FoundationUser.objects.filter(is_active=True).order_by("full_name"),
        "pipeline_column_limit": PIPELINE_COLUMN_LIMIT,
    }
    return _render_business(
        request, "business_ui/leads.html", "leads", "sales", context
    )


@business_permission("crm")
def customers(request):
    """Hien thi danh sach khach hang CRM."""
    customer_rows = CrmPlatformService().list_customers()
    return _render_business(
        request,
        "business_ui/customers.html",
        "customers",
        "crm",
        {"customers": customer_rows},
    )


@business_permission("crm")
def customer_detail(request, customer_id):
    """Hien thi ho so, timeline, interaction, note va task cua mot khach hang."""
    context = CrmPlatformService().get_customer_context(customer_id)
    context["owners"] = FoundationUser.objects.filter(is_active=True).order_by(
        "full_name"
    )
    return _render_business(
        request, "business_ui/customer_detail.html", "customers", "crm", context
    )


@business_permission("sales")
def quotations(request):
    """Hien thi danh sach bao gia va trang thai phe duyet."""
    rows = (
        SalesQuotation.objects.select_related("customer", "opportunity", "created_by")
        .prefetch_related("lines")
        .all()
    )
    context = {
        "quotations": rows,
        "opportunities": SalesOpportunity.objects.select_related("customer").all(),
        "customers": BusinessCustomer.objects.order_by("company_name", "contact_name"),
        "products": BusinessProduct.objects.filter(status="published").order_by("name"),
    }
    return _render_business(
        request, "business_ui/quotations.html", "quotations", "sales", context
    )


@business_permission("sales")
def quotation_detail(request, quotation_id):
    """Hien thi chi tiet mot bao gia."""
    quotation = get_object_or_404(
        SalesQuotation.objects.select_related(
            "customer", "opportunity", "created_by"
        ).prefetch_related("lines"),
        id=quotation_id,
    )
    return _render_business(
        request,
        "business_ui/quotation_detail.html",
        "quotations",
        "sales",
        {"quotation": quotation},
    )


@require_http_methods(["GET", "POST"])
@business_permission("ai_sales")
def ai_sales_assistant(request):
    """Giao dien chat/hop lenh AI Sales chi tao goi y, khong tu dong gui email."""
    result = None
    error = ""
    if request.method == "POST":
        try:
            user = request.business_user
            FoundationPermissionService().require_permission(user, "ai_sales", "write")
            action = request.POST.get("action", "weekly_recommendation")
            payload = {
                "company": request.POST.get("company", ""),
                "contact_person": request.POST.get("contact_person", ""),
                "email": request.POST.get("email", ""),
                "industry": request.POST.get("industry", ""),
                "notes": request.POST.get("notes", ""),
                "purpose": request.POST.get("purpose", "follow_up"),
                "product_interest": request.POST.get(
                    "product_interest", "gia cong CNC chinh xac"
                ),
            }
            if request.POST.get("lead_id"):
                payload["lead_id"] = int(request.POST["lead_id"])
            if request.POST.get("customer_id"):
                payload["customer_id"] = int(request.POST["customer_id"])
            result = SalesAssistantService().handle(action, payload, user=user)
        except (
            PermissionDenied,
            ValidationError,
            ValueError,
            BusinessCustomer.DoesNotExist,
            SalesLead.DoesNotExist,
        ) as exc:
            error = str(exc)

    context = {
        "result": result,
        "error": error,
        "leads": SalesLead.objects.order_by("-updated_at", "-id")[:20],
        "customers": BusinessCustomer.objects.order_by("-updated_at", "-id")[:20],
    }
    return _render_business(
        request, "business_ui/ai_sales.html", "ai-sales", "ai_sales", context
    )


@require_http_methods(["GET", "POST"])
@business_permission("knowledge")
def document_intelligence(request):
    """Upload/search tai lieu de bo sung tri thuc cho AI Knowledge Assistant."""
    result = None
    answer = None
    error = ""
    service = DocumentIntelligenceService()
    if request.method == "POST":
        try:
            user = request.business_user
            FoundationPermissionService().require_permission(user, "knowledge", "write")
            if request.POST.get("mode") == "search":
                answer = service.answer_with_sources(
                    request.POST.get("question", ""), user=user
                )
            else:
                uploaded_file = request.FILES.get("document")
                if not uploaded_file:
                    raise ValidationError("Document file is required.")
                result = service.ingest_uploaded_document(
                    uploaded_file,
                    title=request.POST.get("title", ""),
                    created_by_email=user.email,
                    permission_level=request.POST.get("permission_level", "internal"),
                ).to_dict()
        except (PermissionDenied, ValidationError, ValueError) as exc:
            error = str(exc)

    context = {
        "documents": KnowledgeDocument.objects.select_related("category").order_by(
            "-updated_at", "-id"
        )[:20],
        "result": result,
        "answer": answer,
        "error": error,
    }
    return _render_business(
        request, "business_ui/documents.html", "documents", "knowledge", context
    )


def _bad_request(exc):
    """Return a compact validation response without exposing a traceback."""
    return HttpResponseBadRequest(str(exc))


@require_POST
@business_permission("sales", "write")
def lead_create(request):
    """Create a lead from a Business UI contact form."""
    try:
        company = request.POST.get("company", "").strip()
        contact_person = request.POST.get("contact_person", "").strip()
        if not company or not contact_person:
            raise ValidationError("Company and contact person are required.")
        SalesPlatformService().create_lead(
            {
                "lead_source": request.POST.get("lead_source", "business_ui"),
                "company": company,
                "contact_person": contact_person,
                "email": request.POST.get("email", ""),
                "phone": request.POST.get("phone", ""),
                "industry": request.POST.get("industry", ""),
                "priority": request.POST.get("priority", "medium"),
                "notes": request.POST.get("notes", ""),
            },
            owner=request.business_user,
        )
    except (ValidationError, ValueError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:lead-pipeline")


@require_POST
@business_permission("sales", "write")
def lead_transition(request, lead_id):
    """Move a lead to a selected pipeline state and audit the change."""
    try:
        SalesPlatformService().advance_lead(
            lead_id,
            request.POST.get("status", ""),
            actor=request.business_user.email,
        )
    except (SalesLead.DoesNotExist, ValidationError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:lead-pipeline")


@require_POST
@business_permission("sales", "write")
def lead_assign(request, lead_id):
    """Assign a lead to an active Foundation user."""
    try:
        owner = FoundationUser.objects.get(
            id=int(request.POST.get("owner_id", "0")), is_active=True
        )
        SalesPlatformService().assign_lead(
            lead_id, owner, actor=request.business_user.email
        )
    except (
        FoundationUser.DoesNotExist,
        SalesLead.DoesNotExist,
        TypeError,
        ValueError,
    ) as exc:
        return _bad_request(exc)
    return redirect("business_ui:lead-pipeline")


@require_POST
@business_permission("sales", "write")
def opportunity_create(request, lead_id):
    """Create an opportunity linked to a lead and optional customer."""
    try:
        SalesPlatformService().create_opportunity(
            {
                "lead_id": lead_id,
                "customer_id": request.POST.get("customer_id") or None,
                "title": request.POST.get("title", "").strip(),
                "value": request.POST.get("value", "0"),
                "probability": request.POST.get("probability", "10"),
                "expected_close_date": request.POST.get("expected_close_date", ""),
                "status": "open",
                "notes": request.POST.get("notes", ""),
            },
            owner=request.business_user,
        )
    except (ValidationError, ValueError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:lead-pipeline")


@require_POST
@business_permission("sales", "write")
def follow_up_create(request, lead_id):
    """Create an owned follow-up for a sales lead."""
    try:
        SalesPlatformService().create_follow_up(
            {
                "lead_id": lead_id,
                "title": request.POST.get("title", "").strip(),
                "due_date": request.POST.get("due_date", ""),
                "note": request.POST.get("note", ""),
            },
            owner=request.business_user,
        )
    except (ValidationError, ValueError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:lead-pipeline")


@require_POST
@business_permission("sales", "write")
def quotation_create(request):
    """Create a draft quotation with one validated line from the UI."""
    try:
        description = request.POST.get("description", "").strip()
        if not description:
            raise ValidationError("Quotation description is required.")
        SalesPlatformService().create_quotation(
            {
                "opportunity_id": request.POST.get("opportunity_id") or None,
                "customer_id": request.POST.get("customer_id") or None,
                "status": "draft",
                "approval_status": "pending",
                "lines": [
                    {
                        "product_id": request.POST.get("product_id") or None,
                        "description": description,
                        "quantity": request.POST.get("quantity", "1"),
                        "unit_price": request.POST.get("unit_price", "0"),
                        "discount": request.POST.get("discount", "0"),
                    }
                ],
            },
            user=request.business_user,
        )
    except (ValidationError, ValueError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:quotations")


@require_POST
@business_permission("crm", "write")
def customer_interaction_create(request, customer_id):
    """Add a CRM interaction and timeline event."""
    try:
        subject = request.POST.get("subject", "").strip()
        if not subject:
            raise ValidationError("Interaction subject is required.")
        CrmPlatformService().add_interaction(
            customer_id,
            {
                "interaction_type": request.POST.get("interaction_type", "note"),
                "subject": subject,
                "content": request.POST.get("content", ""),
                "occurred_at": request.POST.get("occurred_at", ""),
            },
            actor=request.business_user.email,
        )
    except (BusinessCustomer.DoesNotExist, ValidationError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:customer-detail", customer_id=customer_id)


@require_POST
@business_permission("crm", "write")
def customer_note_create(request, customer_id):
    """Add an auditable CRM note."""
    try:
        note = request.POST.get("note", "").strip()
        if not note:
            raise ValidationError("Note is required.")
        CrmPlatformService().add_note(
            customer_id, note, actor=request.business_user.email
        )
    except (BusinessCustomer.DoesNotExist, ValidationError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:customer-detail", customer_id=customer_id)


@require_POST
@business_permission("crm", "write")
def customer_task_create(request, customer_id):
    """Create an assigned CRM follow-up task."""
    try:
        title = request.POST.get("title", "").strip()
        if not title:
            raise ValidationError("Task title is required.")
        owner_id = request.POST.get("owner_id")
        owner = (
            FoundationUser.objects.filter(id=owner_id, is_active=True).first()
            if owner_id
            else request.business_user
        )
        CrmPlatformService().create_task(
            customer_id,
            {
                "title": title,
                "due_date": request.POST.get("due_date", ""),
                "status": "open",
            },
            owner=owner,
        )
    except (BusinessCustomer.DoesNotExist, ValidationError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:customer-detail", customer_id=customer_id)


@require_POST
@business_permission("sales", "approve")
def quotation_approve(request, quotation_id):
    """Approve a quotation only through the dedicated human permission."""
    try:
        SalesPlatformService().approve_quotation(
            quotation_id, actor=request.business_user.email
        )
    except (SalesQuotation.DoesNotExist, ValidationError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:quotation-detail", quotation_id=quotation_id)


@require_POST
@business_permission("sales", "write")
def quotation_handoff(request, quotation_id):
    """Create an order handoff only after quotation approval."""
    try:
        SalesPlatformService().handoff_quotation(
            quotation_id, actor=request.business_user.email
        )
    except (SalesQuotation.DoesNotExist, ValidationError) as exc:
        return _bad_request(exc)
    return redirect("business_ui:quotation-detail", quotation_id=quotation_id)
