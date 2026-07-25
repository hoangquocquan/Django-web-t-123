"""Service layer cho Quotation.

Service này giữ logic nghiệp vụ của báo giá:
- Lọc/phân trang danh sách báo giá.
- Tạo yêu cầu báo giá public bằng transaction.
- Chuyển model thành dict để trả API JSON.
"""

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from customers.models import Customer

from .models import QuoteFile, QuoteRequest, QuoteRequestItem


def filter_quotes(keyword="", status="", sort="newest"):
    """Lọc báo giá theo khách hàng, dự án, nội dung và trạng thái."""
    queryset = QuoteRequest.objects.select_related("customer").prefetch_related("items", "files")
    keyword = str(keyword or "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(project_name__icontains=keyword)
            | Q(message__icontains=keyword)
            | Q(status__icontains=keyword)
            | Q(customer__company_name__icontains=keyword)
            | Q(customer__contact_name__icontains=keyword)
            | Q(customer__email__icontains=keyword)
            | Q(customer__phone__icontains=keyword)
        )
    if status:
        queryset = queryset.filter(status=status)

    sort_map = {
        "oldest": "id",
        "status": "status",
        "project": "project_name",
    }
    return queryset.order_by(sort_map.get(sort, "-id"), "-id")


def paginate_quotes(queryset, page=1, per_page=10):
    """Phân trang danh sách báo giá."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page)


def get_quote_detail(quote_id):
    """Lấy chi tiết báo giá kèm khách hàng, item và file."""
    return get_object_or_404(
        QuoteRequest.objects.select_related("customer").prefetch_related("items", "files"),
        id=quote_id,
    )


def normalize_public_quote_payload(payload):
    """Chuẩn hóa dữ liệu form public trước khi lưu vào database."""
    contact_name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    product_name = str(payload.get("product", "")).strip()
    if not contact_name or not (email or phone) or not product_name:
        raise ValueError("Cần nhập tên, email/điện thoại và sản phẩm cần báo giá.")

    quantity_text = str(payload.get("quantity", 1) or 1).strip()
    try:
        quantity = max(1, int(quantity_text))
    except ValueError as exc:
        raise ValueError("Số lượng phải là số nguyên lớn hơn 0.") from exc

    return {
        "customer": {
            "company_name": str(payload.get("company", "")).strip(),
            "contact_name": contact_name,
            "email": email,
            "phone": phone,
            "country": str(payload.get("country", "Vietnam")).strip() or "Vietnam",
        },
        "quote": {
            "project_name": f"Báo giá {product_name}",
            "message": str(payload.get("note", "")).strip(),
        },
        "item": {
            "drawing_code": product_name,
            "quantity": quantity,
            "tolerance": str(payload.get("tolerance", "")).strip(),
            "note": f"Deadline: {payload.get('deadline', '')}. {payload.get('note', '')}".strip(),
        },
        "files": [
            {"file_name": "drawing_pdf", "file_url": str(payload.get("drawing_pdf", "")).strip(), "file_type": "pdf"},
            {"file_name": "step_file", "file_url": str(payload.get("step_file", "")).strip(), "file_type": "step"},
            {"file_name": "dwg_file", "file_url": str(payload.get("dwg_file", "")).strip(), "file_type": "dwg"},
        ],
    }


def create_public_quote_request(payload):
    """Tạo customer + quote + item + file trong một transaction an toàn."""
    data = normalize_public_quote_payload(payload)
    with transaction.atomic():
        customer = Customer.objects.create(**data["customer"])
        quote = QuoteRequest.objects.create(customer=customer, status=QuoteRequest.STATUS_NEW, **data["quote"])
        QuoteRequestItem.objects.create(quote_request=quote, **data["item"])
        for file_info in data["files"]:
            if file_info["file_url"]:
                QuoteFile.objects.create(quote_request=quote, **file_info)
    return get_quote_detail(quote.id)


def update_quote_workflow(quote_id, payload):
    """Cập nhật trạng thái xử lý báo giá trong CMS/Django Admin."""
    quote = get_quote_detail(quote_id)
    quote.status = str(payload.get("status", quote.status)).strip() or quote.status
    quote.assigned_to = payload.get("assigned_to") or None
    quote.internal_note = str(payload.get("internal_note", quote.internal_note or "")).strip()
    quote.quoted_at = payload.get("quoted_at") or quote.quoted_at
    quote.completed_at = payload.get("completed_at") or quote.completed_at
    quote.save(update_fields=["status", "assigned_to", "internal_note", "quoted_at", "completed_at"])
    return quote


def quote_to_dict(quote):
    """Đổi QuoteRequest model thành dict ngắn để trả JSON danh sách."""
    return {
        "id": quote.id,
        "project_name": quote.project_name,
        "message": quote.message,
        "status": quote.status,
        "assigned_to": quote.assigned_to,
        "customer": {
            "id": quote.customer.id,
            "company_name": quote.customer.company_name,
            "contact_name": quote.customer.contact_name,
            "email": quote.customer.email,
            "phone": quote.customer.phone,
            "country": quote.customer.country,
        },
        "created_at": quote.created_at,
    }


def quote_detail_to_dict(quote):
    """Đổi chi tiết báo giá thành dict có cả item và file đính kèm."""
    data = quote_to_dict(quote)
    data.update(
        {
            "internal_note": quote.internal_note,
            "quoted_at": quote.quoted_at,
            "completed_at": quote.completed_at,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "drawing_code": item.drawing_code,
                    "material_id": item.material_id,
                    "quantity": item.quantity,
                    "tolerance": item.tolerance,
                    "note": item.note,
                }
                for item in quote.items.all()
            ],
            "files": [
                {
                    "id": file.id,
                    "file_name": file.file_name,
                    "file_url": file.file_url,
                    "file_type": file.file_type,
                    "uploaded_at": file.uploaded_at,
                }
                for file in quote.files.all()
            ],
        }
    )
    return data
