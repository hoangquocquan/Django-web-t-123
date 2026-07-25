import sqlite3

from api.openapi import get_openapi_schema
from cache.redis_cache import delete_key, get_json, set_json
from services.contacts_service import save_contact
from services.event_service import publish_event
from services.products_service import (
    create_product,
    delete_product,
    get_product_by_id,
    get_product_categories,
    get_products,
    update_product,
)
from services.public_service import get_capabilities, get_home_data, get_news
from utils.exceptions import AppError


# Controller là lớp đứng giữa route HTTP trong app.py và service.
# app.py không nên chứa quá nhiều nghiệp vụ; app.py chỉ nên nhận request,
# sau đó gọi controller phù hợp. Controller sẽ gọi service/repository bên dưới.


def ok(data, status=200):
    """Chuẩn hóa giá trị controller trả về cho app.py."""
    # Mỗi hàm controller trả về tuple (data, status).
    # app.py chỉ cần lấy tuple này và gửi JSON response cho frontend.
    return data, status


def get_home_response():
    """Controller cho GET /api/home."""
    # Trang chủ được đọc nhiều, nên có thể cache bằng Redis khi bật cấu hình.
    cache_key = "api:home"
    cached = get_json(cache_key)
    if cached:
        # Nếu Redis đã có dữ liệu, trả luôn để giảm số lần đọc database.
        return ok(cached)

    # Nếu cache chưa có, đọc dữ liệu thật từ service rồi lưu vào Redis 60 giây.
    data = get_home_data()
    set_json(cache_key, data, ttl_seconds=60)
    return ok(data)


def list_products_response():
    """Controller cho GET /api/products."""
    return ok(get_products())


def get_product_response(product_id):
    """Controller cho GET /api/products/{id}."""
    product = get_product_by_id(product_id)
    if not product:
        # AppError sẽ được exception handler bắt và đổi thành JSON lỗi thống nhất.
        raise AppError("Không tìm thấy sản phẩm.", status=404, code="PRODUCT_NOT_FOUND")
    return ok(product)


def list_product_categories_response():
    """Controller cho GET /api/product-categories."""
    return ok(get_product_categories())


def list_capabilities_response():
    """Controller cho GET /api/capabilities."""
    return ok(get_capabilities())


def list_news_response():
    """Controller cho GET /api/news."""
    return ok(get_news())


def openapi_response():
    """Controller cho GET /api/openapi.json."""
    return ok(get_openapi_schema())


def create_contact_response(payload):
    """Controller cho POST /api/contact."""
    # save_contact nằm ở service, nơi kiểm tra dữ liệu và ghi database.
    contact_request = save_contact(payload)
    publish_event(
        "contact.created",
        "contact_request",
        contact_request["id"],
        {"name": contact_request["name"], "contact": contact_request["contact"]},
    )
    return ok(
        {
            "id": contact_request["id"],
            "message": "Đã lưu yêu cầu liên hệ vào database.",
        },
        status=201,
    )


def create_product_response(payload):
    """Controller cho POST /api/products."""
    try:
        product = create_product(payload)
    except sqlite3.IntegrityError as error:
        # Lỗi UNIQUE trong SQLite thường xảy ra khi slug bị trùng.
        raise AppError("Slug sản phẩm đã tồn tại. Hãy gửi slug khác.", status=409, code="DUPLICATE_PRODUCT_SLUG") from error

    # Khi dữ liệu sản phẩm thay đổi, xóa cache trang chủ để lần đọc sau lấy dữ liệu mới.
    delete_key("api:home")
    return ok({"message": "Đã tạo sản phẩm mới.", "product": product}, status=201)


def update_product_response(product_id, payload):
    """Controller cho PUT /api/products/{id}."""
    try:
        product = update_product(product_id, payload)
    except sqlite3.IntegrityError as error:
        raise AppError("Slug sản phẩm đã tồn tại. Hãy gửi slug khác.", status=409, code="DUPLICATE_PRODUCT_SLUG") from error

    if not product:
        raise AppError("Không tìm thấy sản phẩm để cập nhật.", status=404, code="PRODUCT_NOT_FOUND")

    # Sản phẩm nổi bật có thể xuất hiện ở trang chủ, nên cần xóa cache trang chủ.
    delete_key("api:home")
    return ok({"message": "Đã cập nhật sản phẩm.", "product": product})


def delete_product_response(product_id):
    """Controller cho DELETE /api/products/{id}."""
    try:
        product = delete_product(product_id)
    except sqlite3.IntegrityError as error:
        raise AppError(
            "Không thể xóa vì sản phẩm đang được dữ liệu khác tham chiếu.",
            status=409,
            code="DATABASE_CONSTRAINT_ERROR",
        ) from error

    if not product:
        raise AppError("Không tìm thấy sản phẩm để xóa.", status=404, code="PRODUCT_NOT_FOUND")

    # Sau khi xóa sản phẩm, cache trang chủ có thể đã cũ.
    delete_key("api:home")
    return ok({"message": "Đã xóa sản phẩm.", "product": product})
