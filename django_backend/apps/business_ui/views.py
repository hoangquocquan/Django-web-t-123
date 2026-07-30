"""Django views cho giao dien business van hanh hang ngay.

Module nay chi doc/ghi qua cac service va model Django da migrate. Muc tieu la
cho nguoi dung thu nghiem Sales, CRM va AI Sales tren trinh duyet ma khong can
dung Postman hay goi API thu cong.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.business_core.models import BusinessCustomer
from apps.crm.services.crm_platform_service import CrmPlatformService
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.document_intelligence import DocumentIntelligenceService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation


ADMIN_TOKEN_SESSION_KEY = "foundation_admin_token"
PIPELINE_COLUMNS = ["new", "contacted", "meeting", "quotation", "negotiation", "won", "lost"]


def _current_user(request):
    """Lay user dang dang nhap tu session CMS admin.

    Business UI dung chung token voi `/admin/login/` de nguoi hoc khong phai
    dang nhap nhieu lan. Neu token het han, nguoi dung duoc dua ve trang login.
    """
    raw_token = request.session.get(ADMIN_TOKEN_SESSION_KEY, "")
    if not raw_token:
        raise PermissionDenied("Business UI requires admin login.")
    return FoundationAuthService().authenticate_token(raw_token)


def _business_context(request, active, extra=None):
    """Tao context chung cho moi template business."""
    user = _current_user(request)
    FoundationPermissionService().require_permission(user, "dashboard", "read")
    context = {
        "admin_user": user,
        "active": active,
        "navigation": [
            {"key": "dashboard", "label": "Dashboard", "url": "/business/"},
            {"key": "leads", "label": "Lead Pipeline", "url": "/business/leads/"},
            {"key": "customers", "label": "CRM Customers", "url": "/business/customers/"},
            {"key": "quotations", "label": "Quotations", "url": "/business/quotations/"},
            {"key": "ai-sales", "label": "AI Sales", "url": "/business/ai-sales/"},
            {"key": "documents", "label": "AI Documents", "url": "/business/documents/"},
        ],
    }
    context.update(extra or {})
    return context


def _render_business(request, template, active, context=None):
    """Render business page hoac redirect login neu chua co session hop le."""
    try:
        return render(request, template, _business_context(request, active, context))
    except PermissionDenied:
        return redirect("admin_ui:login")


def _sales_metrics():
    """Tinh cac chi so sales de hien tren dashboard."""
    total_leads = SalesLead.objects.count()
    won_leads = SalesLead.objects.filter(status="won").count()
    open_opportunities = SalesOpportunity.objects.exclude(status__in=["won", "lost"])
    pipeline_value = sum((item.value for item in open_opportunities), Decimal("0"))
    revenue_forecast = sum((item.value * Decimal(item.probability) / Decimal("100") for item in open_opportunities), Decimal("0"))
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


def dashboard(request):
    """Hien thi dashboard Sales/CRM tong quan."""
    context = {
        "metrics": _sales_metrics(),
        "recent_leads": SalesLead.objects.select_related("owner").order_by("-updated_at", "-id")[:6],
        "recent_quotations": SalesQuotation.objects.select_related("customer").order_by("-updated_at", "-id")[:6],
    }
    return _render_business(request, "business_ui/dashboard.html", "dashboard", context)


def lead_pipeline(request):
    """Hien thi pipeline Kanban gom cac lead theo trang thai."""
    leads = SalesLead.objects.select_related("owner").all()
    columns = [
        {
            "status": status,
            "label": dict(SalesLead.STATUS_CHOICES).get(status, status.title()),
            "leads": [lead for lead in leads if lead.status == status],
        }
        for status in PIPELINE_COLUMNS
    ]
    return _render_business(request, "business_ui/leads.html", "leads", {"columns": columns})


def customers(request):
    """Hien thi danh sach khach hang CRM."""
    customer_rows = CrmPlatformService().list_customers()
    return _render_business(request, "business_ui/customers.html", "customers", {"customers": customer_rows})


def customer_detail(request, customer_id):
    """Hien thi ho so, timeline, interaction, note va task cua mot khach hang."""
    context = CrmPlatformService().get_customer_context(customer_id)
    return _render_business(request, "business_ui/customer_detail.html", "customers", context)


def quotations(request):
    """Hien thi danh sach bao gia va trang thai phe duyet."""
    rows = SalesQuotation.objects.select_related("customer", "opportunity", "created_by").prefetch_related("lines").all()
    return _render_business(request, "business_ui/quotations.html", "quotations", {"quotations": rows})


def quotation_detail(request, quotation_id):
    """Hien thi chi tiet mot bao gia."""
    quotation = get_object_or_404(
        SalesQuotation.objects.select_related("customer", "opportunity", "created_by").prefetch_related("lines"),
        id=quotation_id,
    )
    return _render_business(request, "business_ui/quotation_detail.html", "quotations", {"quotation": quotation})


@require_http_methods(["GET", "POST"])
def ai_sales_assistant(request):
    """Giao dien chat/hop lenh AI Sales chi tao goi y, khong tu dong gui email."""
    result = None
    error = ""
    if request.method == "POST":
        try:
            user = _current_user(request)
            action = request.POST.get("action", "weekly_recommendation")
            payload = {
                "company": request.POST.get("company", ""),
                "contact_person": request.POST.get("contact_person", ""),
                "email": request.POST.get("email", ""),
                "industry": request.POST.get("industry", ""),
                "notes": request.POST.get("notes", ""),
                "purpose": request.POST.get("purpose", "follow_up"),
                "product_interest": request.POST.get("product_interest", "gia cong CNC chinh xac"),
            }
            if request.POST.get("lead_id"):
                payload["lead_id"] = int(request.POST["lead_id"])
            if request.POST.get("customer_id"):
                payload["customer_id"] = int(request.POST["customer_id"])
            result = SalesAssistantService().handle(action, payload, user=user)
        except (PermissionDenied, ValidationError, ValueError, BusinessCustomer.DoesNotExist, SalesLead.DoesNotExist) as exc:
            error = str(exc)

    context = {
        "result": result,
        "error": error,
        "leads": SalesLead.objects.order_by("-updated_at", "-id")[:20],
        "customers": BusinessCustomer.objects.order_by("-updated_at", "-id")[:20],
    }
    return _render_business(request, "business_ui/ai_sales.html", "ai-sales", context)


@require_http_methods(["GET", "POST"])
def document_intelligence(request):
    """Upload/search tai lieu de bo sung tri thuc cho AI Knowledge Assistant."""
    result = None
    answer = None
    error = ""
    service = DocumentIntelligenceService()
    if request.method == "POST":
        try:
            user = _current_user(request)
            if request.POST.get("mode") == "search":
                answer = service.answer_with_sources(request.POST.get("question", ""), user=user)
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
        "documents": KnowledgeDocument.objects.select_related("category").order_by("-updated_at", "-id")[:20],
        "result": result,
        "answer": answer,
        "error": error,
    }
    return _render_business(request, "business_ui/documents.html", "documents", context)

