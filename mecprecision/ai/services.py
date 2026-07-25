"""Service layer cho AI trong Django.

File này là nơi chuẩn bị prompt, gọi Ollama local, xử lý fallback và lưu lịch sử.
View/API chỉ gọi các hàm service, không tự viết logic AI trực tiếp.
"""

import hashlib
import json
import re
import urllib.error
import urllib.request

from django.conf import settings
from django.db.models import Q

from customers.models import ContactRequest
from news.models import NewsArticle
from products.models import Product
from quotation.models import QuoteRequest

from .models import AIConversation, AITranslationCache

AI_PROVIDER = "ollama"
OLLAMA_URL = getattr(settings, "OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = getattr(settings, "OLLAMA_MODEL", "llama3.1")
OLLAMA_TIMEOUT_SECONDS = int(getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 8))


def extract_json_object(text):
    """Tách JSON object đầu tiên từ câu trả lời AI."""
    raw_text = str(text or "").strip()
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(raw_text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def build_business_context():
    """Tạo tài liệu ngữ cảnh ngắn về doanh nghiệp để AI trả lời đúng phạm vi."""
    try:
        products = ", ".join(
            Product.objects.filter(status=Product.STATUS_PUBLISHED).order_by("sort_order", "id").values_list("name", flat=True)[:5]
        )
    except Exception:
        products = ""
    try:
        news_titles = ", ".join(
            NewsArticle.objects.filter(status=NewsArticle.STATUS_PUBLISHED).order_by("-published_at").values_list("title", flat=True)[:3]
        )
    except Exception:
        news_titles = ""

    products = products or "sản phẩm cơ khí chính xác, chi tiết CNC, đồ gá, fixture"
    news_titles = news_titles or "gia công CNC, kiểm tra chất lượng, tư vấn bản vẽ kỹ thuật"
    return (
        "Bạn là trợ lý AI của website MecPrecision VIETNAM. "
        "Trả lời bằng tiếng Việt có dấu, ngắn gọn, lịch sự, dễ hiểu. "
        "Website chuyên gia công cơ khí chính xác, CNC, đồ gá, fixture và báo giá theo bản vẽ. "
        f"Sản phẩm tiêu biểu: {products}. "
        f"Nội dung/tin tức tiêu biểu: {news_titles}. "
        "Nếu khách cần báo giá, hãy hỏi bản vẽ, vật liệu, số lượng, dung sai và deadline."
    )


def call_ollama(prompt, model=None):
    """Gọi Ollama local qua HTTP API `/api/generate`."""
    selected_model = model or OLLAMA_MODEL
    payload = {"model": selected_model, "prompt": prompt, "stream": False}
    request = urllib.request.Request(
        f"{OLLAMA_URL.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", "")).strip()


def save_ai_message(channel, user_message, assistant_message, model, status="ok", error=""):
    """Lưu một lượt hỏi đáp AI vào database."""
    return AIConversation.objects.create(
        channel=channel,
        user_message=user_message,
        assistant_message=assistant_message,
        model=model,
        provider=AI_PROVIDER,
        status=status,
        error=error,
    )


def run_ai_operation(channel, user_message, prompt, fallback_message, model=None):
    """Chạy một tác vụ AI có fallback để website không bị lỗi 500 khi Ollama tắt."""
    selected_model = model or OLLAMA_MODEL
    status = "ok"
    error = ""
    try:
        answer = call_ollama(prompt, selected_model)
        if not answer:
            raise ValueError("Ollama trả về nội dung rỗng.")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        status = "fallback"
        error = str(exc)
        answer = fallback_message

    record = save_ai_message(channel, user_message, answer, selected_model, status, error)
    return {
        "id": record.id,
        "answer": answer,
        "model": selected_model,
        "provider": AI_PROVIDER,
        "status": status,
        "error": error,
    }


def ask_ai(message, channel="public", model=None):
    """Chatbot AI: nhận câu hỏi của người dùng, ghép business context rồi gửi Ollama."""
    message = str(message or "").strip()
    if not message:
        raise ValueError("Vui lòng nhập câu hỏi cho AI.")
    prompt = f"{build_business_context()}\n\nCâu hỏi của người dùng:\n{message}\n\nTrả lời:"
    fallback = (
        "Hiện Ollama local chưa phản hồi, nên đây là câu trả lời demo. "
        "Để dùng AI thật, hãy chạy Ollama và tải model, ví dụ: `ollama run llama3.1`. "
        f"Câu hỏi của bạn là: {message}"
    )
    return run_ai_operation(channel, message, prompt, fallback, model)


def translate_text(source_text, target_language, source_language="", tone="", model=None):
    """Dịch nội dung bằng AI và lưu cache theo hash nội dung."""
    source_text = str(source_text or "").strip()
    target_language = str(target_language or "").strip()
    source_language = str(source_language or "").strip() or "Tự động nhận diện"
    tone = str(tone or "").strip() or "tự nhiên, chuyên nghiệp"
    if not source_text:
        raise ValueError("Vui lòng nhập nội dung cần dịch.")
    if not target_language:
        raise ValueError("Vui lòng nhập ngôn ngữ đích.")

    selected_model = model or OLLAMA_MODEL
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    cached = AITranslationCache.objects.filter(source_hash=source_hash, target_language=target_language, model=selected_model).first()
    if cached:
        return {
            "id": cached.id,
            "answer": cached.translated_text,
            "model": selected_model,
            "provider": cached.provider,
            "status": "cached",
            "error": "",
        }

    prompt = f"""
Bạn là AI dịch thuật cho website MecPrecision VIETNAM.
Giữ nguyên mã sản phẩm, số đo, đơn vị, tên riêng, URL và thuật ngữ CNC nếu cần.

Ngôn ngữ nguồn: {source_language}
Ngôn ngữ đích: {target_language}
Giọng văn: {tone}

Nội dung cần dịch:
{source_text}

Chỉ trả về bản dịch, không giải thích thêm.
"""
    fallback = f"[Demo dịch sang {target_language}] Ollama chưa phản hồi nên giữ nội dung gốc: {source_text}"
    result = run_ai_operation("translation", f"Dịch sang {target_language}: {source_text}", prompt, fallback, selected_model)
    AITranslationCache.objects.create(
        source_hash=source_hash,
        source_text=source_text,
        target_language=target_language,
        translated_text=result["answer"],
        provider=AI_PROVIDER,
        model=selected_model,
        status=result["status"],
        error=result["error"],
    )
    return result


def ask_developer_ai(question, code_context="", language="", model=None):
    """AI hỗ trợ Developer: giải thích code/log và gợi ý cách debug an toàn."""
    question = str(question or "").strip()
    code_context = str(code_context or "").strip()
    language = str(language or "").strip() or "Python/HTML/CSS/SQL"
    if not question:
        raise ValueError("Vui lòng nhập câu hỏi cho Developer AI.")
    prompt = f"""
Bạn là Developer AI trong CMS MecPrecision VIETNAM.
Trả lời bằng tiếng Việt có dấu, dễ hiểu cho người chưa chuyên lập trình.
Ưu tiên cấu trúc: nguyên nhân, cách kiểm tra, cách sửa, ví dụ ngắn.

Ngôn ngữ/khu vực code: {language}
Câu hỏi:
{question}

Code hoặc log liên quan:
{code_context}
"""
    fallback = f"Ollama chưa phản hồi. Demo Developer AI: hãy kiểm tra log, route, service và database liên quan tới câu hỏi: {question}"
    return run_ai_operation("developer_code", question, prompt, fallback, model)


def summarize_recent_contacts(limit=8, model=None):
    """AI tóm tắt các liên hệ mới để admin biết việc nào cần ưu tiên."""
    contacts = list(
        ContactRequest.objects.order_by("-id").values(
            "id", "name", "company", "phone", "email", "country", "interested_product", "message", "status", "is_read", "created_at"
        )[: int(limit or 8)]
    )
    if not contacts:
        return run_ai_operation("contacts_summary", "Tóm tắt liên hệ mới", "Không có liên hệ mới.", "Hiện chưa có liên hệ mới để tóm tắt.", model)
    prompt = f"""
{build_business_context()}

Bạn là trợ lý vận hành CMS. Hãy tóm tắt liên hệ mới thật gọn theo Markdown:
### Tổng quan
### Cần ưu tiên
### Thiếu thông tin cần hỏi
### Việc cần làm tiếp theo

Dữ liệu liên hệ JSON:
{json.dumps(contacts, ensure_ascii=False, default=str)}
"""
    fallback = (
        "### Tổng quan\n"
        f"- Ollama chưa phản hồi. Có {len(contacts)} liên hệ gần nhất cần kiểm tra.\n\n"
        "### Cần ưu tiên\n"
        "- Ưu tiên liên hệ chưa đọc, có sản phẩm quan tâm và có email/điện thoại.\n\n"
        "### Thiếu thông tin cần hỏi\n"
        "- Kiểm tra bản vẽ, số lượng, vật liệu, dung sai và deadline nếu khách chưa ghi rõ.\n\n"
        "### Việc cần làm tiếp theo\n"
        "- Sales/kỹ thuật liên hệ lại khách và cập nhật trạng thái trong CMS."
    )
    return run_ai_operation("contacts_summary", "Tóm tắt liên hệ mới", prompt, fallback, model)


def analyze_quote_request(quote_id=0, model=None):
    """AI phân tích yêu cầu báo giá: đủ/thiếu thông tin, rủi ro và bước tiếp theo."""
    quote_id = int(quote_id or 0)
    queryset = QuoteRequest.objects.select_related("customer").prefetch_related("items", "files").order_by("-id")
    quote = queryset.filter(id=quote_id).first() if quote_id else queryset.first()
    if not quote:
        raise ValueError("Chưa có yêu cầu báo giá để phân tích.")
    quote_data = {
        "id": quote.id,
        "project_name": quote.project_name,
        "message": quote.message,
        "status": quote.status,
        "customer": {
            "company_name": quote.customer.company_name,
            "contact_name": quote.customer.contact_name,
            "email": quote.customer.email,
            "phone": quote.customer.phone,
            "country": quote.customer.country,
        },
        "items": [
            {"drawing_code": item.drawing_code, "quantity": item.quantity, "tolerance": item.tolerance, "note": item.note}
            for item in quote.items.all()
        ],
        "files": [{"file_name": file.file_name, "file_url": file.file_url, "file_type": file.file_type} for file in quote.files.all()],
    }
    prompt = f"""
{build_business_context()}

Bạn là trợ lý báo giá cho website cơ khí chính xác.
Hãy phân tích yêu cầu báo giá theo: khách cần gì, thông tin đã đủ, thông tin thiếu, rủi ro, email phản hồi, trạng thái đề xuất.

Dữ liệu quote JSON:
{json.dumps(quote_data, ensure_ascii=False)}
"""
    fallback = f"Ollama chưa phản hồi. Demo phân tích quote #{quote.id}: kiểm tra bản vẽ, số lượng, vật liệu, dung sai, deadline và file STEP/DWG/PDF trước khi báo giá."
    return run_ai_operation("quote_analysis", f"Phân tích quote #{quote.id}", prompt, fallback, model)


def score_search_item(query, item, fields):
    """Tính điểm tìm kiếm đơn giản theo số lần keyword xuất hiện trong dữ liệu."""
    query_words = [word for word in re.split(r"\W+", query.lower()) if len(word) >= 2]
    haystack = " ".join(str(item.get(field, "")) for field in fields).lower()
    return sum(haystack.count(word) for word in query_words)


def smart_search_content(query, scope="all", model=None):
    """AI tìm kiếm thông minh trong sản phẩm và tin tức rồi tóm tắt kết quả phù hợp."""
    query = str(query or "").strip()
    scope = str(scope or "all").strip()
    if not query:
        raise ValueError("Vui lòng nhập từ khóa/câu hỏi cần tìm.")

    matches = []
    if scope in {"all", "products"}:
        products = Product.objects.select_related("category").filter(status=Product.STATUS_PUBLISHED)
        for product in products:
            item = {
                "type": "product",
                "id": product.id,
                "name": product.name,
                "description": product.short_description,
                "category": product.category.name,
                "tags_text": product.tags_text,
            }
            item["score"] = score_search_item(query, item, ["name", "description", "category", "tags_text"])
            if item["score"]:
                matches.append(item)
    if scope in {"all", "news"}:
        news_items = NewsArticle.objects.select_related("category").filter(status=NewsArticle.STATUS_PUBLISHED)
        for article in news_items:
            item = {
                "type": "news",
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "category": article.category.name,
            }
            item["score"] = score_search_item(query, item, ["title", "description", "category"])
            if item["score"]:
                matches.append(item)

    matches = sorted(matches, key=lambda item: item["score"], reverse=True)[:8]
    if not matches:
        fallback = f"Không tìm thấy kết quả rõ ràng cho: {query}."
        return run_ai_operation("smart_search", f"Tìm kiếm: {query}", fallback, fallback, model)

    prompt = f"{build_business_context()}\n\nAdmin tìm kiếm: {query}\nKết quả JSON:\n{json.dumps(matches, ensure_ascii=False)}\n\nHãy tóm tắt kết quả phù hợp nhất."
    fallback = f"Ollama chưa phản hồi. Tìm thấy {len(matches)} kết quả gần nhất cho '{query}'. Kết quả đầu tiên: {matches[0].get('name') or matches[0].get('title')}."
    return run_ai_operation("smart_search", f"Tìm kiếm: {query}", prompt, fallback, model)


def generate_dashboard_insights(model=None):
    """AI dashboard: trả lời câu 'Hôm nay website có gì cần chú ý?'."""
    stats = {
        "products": Product.objects.count(),
        "published_products": Product.objects.filter(status=Product.STATUS_PUBLISHED).count(),
        "news": NewsArticle.objects.count(),
        "new_contacts": ContactRequest.objects.filter(Q(status="new") | Q(is_read=False)).count(),
        "quotes_new": QuoteRequest.objects.filter(status__in=["new", "pending"]).count(),
        "ai_fallback": AIConversation.objects.filter(status="fallback").count(),
    }
    prompt = f"{build_business_context()}\n\nSố liệu dashboard JSON:\n{json.dumps(stats, ensure_ascii=False)}\n\nHôm nay website có gì cần chú ý?"
    fallback = f"Ollama chưa phản hồi. Demo dashboard: liên hệ mới/chưa đọc={stats['new_contacts']}, quote mới={stats['quotes_new']}, AI fallback={stats['ai_fallback']}."
    return run_ai_operation("dashboard_insights", "AI dashboard hôm nay", prompt, fallback, model)


def build_product_content_fallback(product):
    """Tạo nội dung sản phẩm cơ bản khi AI không trả JSON hợp lệ."""
    name = product["name"]
    category = product.get("category_name") or "cơ khí chính xác"
    short_description = product.get("short_description") or f"{name} dùng cho sản xuất công nghiệp."
    return {
        "description": (
            f"{name} thuộc nhóm {category}, phù hợp cho ứng dụng cần độ ổn định, độ chính xác "
            "và khả năng gia công theo bản vẽ kỹ thuật."
        ),
        "seo_title": f"{name} | Gia công cơ khí chính xác",
        "seo_description": short_description[:155],
        "seo_keywords": f"{name}, {category}, gia công CNC, cơ khí chính xác",
        "tags_text": f"{category}, cnc, cơ khí chính xác",
        "schema_json": json.dumps({"@context": "https://schema.org", "@type": "Product", "name": name, "description": short_description}, ensure_ascii=False),
    }


def normalize_product_ai_fields(product, data):
    """Chuẩn hóa field AI trả về để có thể điền vào form Products."""
    fallback = build_product_content_fallback(product)
    normalized = {}
    for key, fallback_value in fallback.items():
        value = str(data.get(key, "")).strip() if isinstance(data, dict) else ""
        normalized[key] = value or fallback_value
    normalized["seo_title"] = normalized["seo_title"][:80]
    normalized["seo_description"] = normalized["seo_description"][:180]
    try:
        json.loads(normalized["schema_json"])
    except json.JSONDecodeError:
        normalized["schema_json"] = fallback["schema_json"]
    return normalized


def generate_product_content(product_payload, model=None):
    """Dùng AI tạo mô tả sản phẩm và SEO cho form Admin Products."""
    name = str(product_payload.get("name", "")).strip()
    if not name:
        raise ValueError("Cần nhập tên sản phẩm trước khi dùng AI.")
    product = {
        "name": name,
        "category_name": str(product_payload.get("category_name", "")).strip(),
        "sku": str(product_payload.get("sku", "")).strip(),
        "short_description": str(product_payload.get("short_description", "")).strip(),
        "description": str(product_payload.get("description", "")).strip(),
        "tags_text": str(product_payload.get("tags_text", "")).strip(),
    }
    prompt = f"""
{build_business_context()}

Hãy tạo nội dung sản phẩm và SEO cho CMS. Chỉ trả về JSON hợp lệ với các key:
description, seo_title, seo_description, seo_keywords, tags_text, schema_json.

Thông tin sản phẩm JSON:
{json.dumps(product, ensure_ascii=False)}
"""
    selected_model = model or OLLAMA_MODEL
    status = "ok"
    error = ""
    try:
        raw_answer = call_ollama(prompt, selected_model)
        fields = normalize_product_ai_fields(product, extract_json_object(raw_answer))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        status = "fallback"
        error = str(exc)
        fields = build_product_content_fallback(product)
    record = save_ai_message("product_content", f"Tạo nội dung sản phẩm: {name}", json.dumps(fields, ensure_ascii=False), selected_model, status, error)
    return {"id": record.id, "fields": fields, "model": selected_model, "provider": AI_PROVIDER, "status": status, "error": error}


def get_recent_ai_messages(limit=20):
    """Lấy lịch sử hỏi đáp AI gần nhất."""
    return AIConversation.objects.order_by("-id")[: int(limit or 20)]


def get_ai_status():
    """Trả trạng thái cấu hình AI để hiển thị trong Admin/API."""
    return {"provider": AI_PROVIDER, "ollama_url": OLLAMA_URL, "model": OLLAMA_MODEL, "timeout_seconds": OLLAMA_TIMEOUT_SECONDS}
