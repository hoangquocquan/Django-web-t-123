"""Service layer cho Customers.

Service là nơi gom logic đọc dữ liệu, lọc, phân trang và đổi model thành JSON.
Nhờ vậy view chỉ lo nhận request/trả response, còn câu query nằm tập trung ở đây.
"""

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import ContactRequest, Customer


def filter_customers(keyword="", sort="newest"):
    """Lọc danh sách khách hàng theo từ khóa và kiểu sắp xếp."""
    queryset = Customer.objects.all()
    keyword = str(keyword or "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(company_name__icontains=keyword)
            | Q(contact_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(phone__icontains=keyword)
            | Q(country__icontains=keyword)
        )

    sort_map = {
        "oldest": "id",
        "company": "company_name",
        "contact": "contact_name",
    }
    return queryset.order_by(sort_map.get(sort, "-id"), "-id")


def filter_contact_requests(keyword="", status="", sort="newest"):
    """Lọc danh sách liên hệ theo từ khóa và trạng thái xử lý."""
    queryset = ContactRequest.objects.all()
    keyword = str(keyword or "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword)
            | Q(contact__icontains=keyword)
            | Q(company__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(phone__icontains=keyword)
            | Q(interested_product__icontains=keyword)
            | Q(message__icontains=keyword)
        )
    if status:
        queryset = queryset.filter(status=status)

    sort_map = {
        "oldest": "id",
        "unread": "is_read",
        "status": "status",
    }
    return queryset.order_by(sort_map.get(sort, "-id"), "-id")


def paginate_queryset(queryset, page=1, per_page=10):
    """Phân trang queryset bằng Paginator của Django."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page)


def get_customer_detail(customer_id):
    """Lấy chi tiết một khách hàng kèm ghi chú chăm sóc."""
    return get_object_or_404(Customer.objects.prefetch_related("notes"), id=customer_id)


def get_contact_request_detail(contact_id):
    """Lấy chi tiết một liên hệ khách gửi từ website."""
    return get_object_or_404(ContactRequest, id=contact_id)


def customer_to_dict(customer):
    """Đổi Customer model thành dict để trả JSON API."""
    return {
        "id": customer.id,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "country": customer.country,
        "created_at": customer.created_at,
    }


def customer_detail_to_dict(customer):
    """Đổi chi tiết Customer thành dict có cả danh sách ghi chú."""
    data = customer_to_dict(customer)
    data["notes"] = [
        {
            "id": note.id,
            "note": note.note,
            "created_by": note.created_by,
            "created_at": note.created_at,
        }
        for note in customer.notes.all()
    ]
    return data


def contact_request_to_dict(contact):
    """Đổi ContactRequest model thành dict để API trả dữ liệu rõ ràng."""
    return {
        "id": contact.id,
        "name": contact.name,
        "contact": contact.contact,
        "company": contact.company,
        "phone": contact.phone,
        "email": contact.email,
        "country": contact.country,
        "interested_product": contact.interested_product,
        "attachment_url": contact.attachment_url,
        "message": contact.message,
        "status": contact.status,
        "is_read": contact.is_read,
        "note": contact.note,
        "created_at": contact.created_at,
    }
