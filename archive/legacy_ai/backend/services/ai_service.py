import json
import io
import re
import urllib.error
import urllib.request
from pathlib import Path

from config.settings import OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS, OLLAMA_URL
from database.connection import query_all, query_one
from repositories import ai_repository
from services.public_service import get_home_data, get_news


# File này là lớp Service của AI.
# Nhiệm vụ chính:
# 1. Chuẩn bị prompt/ngữ cảnh cho AI.
# 2. Gọi Ollama local qua HTTP.
# 3. Nếu Ollama lỗi thì trả câu trả lời fallback để website không bị sập.
# 4. Lưu lịch sử hỏi đáp vào database thông qua ai_repository.
AI_PROVIDER = "ollama"


def extract_json_object(text):
    """Tách JSON object đầu tiên từ câu trả lời AI."""
    # Ollama đôi khi trả thêm giải thích trước/sau JSON.
    # Hàm này cố gắng lấy phần nằm giữa dấu { ... } để parse.
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
    """Tạo ngữ cảnh ngắn về website để AI trả lời sát nội dung doanh nghiệp."""
    try:
        data = get_home_data()
        products = ", ".join(item["name"] for item in data.get("featured_products", [])[:5])
        capabilities = ", ".join(item["title"] for item in data.get("capabilities", [])[:5])
    except Exception:
        products = "sản phẩm cơ khí chính xác, chi tiết CNC, đồ gá, fixture"
        capabilities = "gia công CNC, kiểm tra chất lượng, tư vấn kỹ thuật"

    # Fallback dùng để demo an toàn.
    # Nếu không có fallback, khách/admin sẽ thấy lỗi 500 khi Ollama chưa chạy.
    return (
        "Bạn là trợ lý AI của website MecPrecision VIETNAM. "
        "Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu, lịch sự. "
        "Website chuyên gia công cơ khí chính xác, CNC, đồ gá, fixture và báo giá theo bản vẽ. "
        f"Sản phẩm tiêu biểu: {products}. "
        f"Năng lực tiêu biểu: {capabilities}. "
        "Nếu câu hỏi cần báo giá, hãy hướng dẫn khách gửi bản vẽ, vật liệu, số lượng, dung sai và deadline."
    )


def call_ollama(prompt, model=None):
    """Gọi Ollama local qua HTTP API /api/generate."""
    model = model or OLLAMA_MODEL
    # Ollama API cần JSON gồm model, prompt và stream.
    # stream=False nghĩa là chờ Ollama trả xong một câu trả lời đầy đủ rồi mới gửi về web.
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    # Request này gọi tới http://127.0.0.1:11434/api/generate nếu dùng cấu hình mặc định.
    request = urllib.request.Request(
        f"{OLLAMA_URL.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Timeout giúp web không bị treo quá lâu nếu Ollama bị tắt hoặc model phản hồi chậm.
    with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", "")).strip()


def fallback_answer(message):
    """Câu trả lời dự phòng khi máy chưa bật Ollama hoặc chưa có model."""
    return (
        "Hiện Ollama local chưa phản hồi, nên đây là câu trả lời demo. "
        "Để dùng AI thật, hãy chạy Ollama trên máy và tải model, ví dụ: "
        "`ollama run llama3:latest`. "
        f"Câu hỏi của bạn là: {message}"
    )


def fallback_translation(source_text, target_language):
    """Trả kết quả dịch demo khi Ollama chưa phản hồi."""
    # Đây là fallback an toàn: web vẫn hiển thị được kết quả thay vì lỗi 500.
    # Khi Ollama chạy thật, hàm translate_text() sẽ dùng câu trả lời từ model.
    return (
        f"[Demo dịch sang {target_language}] "
        f"Ollama chưa phản hồi nên hệ thống giữ nguyên nội dung gốc: {source_text}"
    )


def fallback_developer_answer(question):
    """Trả câu trả lời demo cho Developer AI khi Ollama chưa phản hồi."""
    # Developer AI chỉ là trợ lý gợi ý, không tự sửa code nếu admin chưa yêu cầu rõ.
    return (
        "Hiện Ollama local chưa phản hồi, nên đây là câu trả lời demo. "
        "Bạn có thể hỏi Developer AI về luồng code, lỗi Python, SQL, API, Docker hoặc cách đọc log. "
        f"Câu hỏi của bạn là: {question}"
    )


def ask_ai(message, channel="public", model=None):
    """Nhận câu hỏi, gọi AI, lưu lịch sử và trả kết quả cho API/Admin."""
    # Chuẩn hóa câu hỏi từ form/API để tránh lưu khoảng trắng thừa.
    message = str(message or "").strip()
    if not message:
        raise ValueError("Vui lòng nhập câu hỏi cho AI.")

    selected_model = model or OLLAMA_MODEL
    full_prompt = f"{build_business_context()}\n\nCâu hỏi của người dùng:\n{message}\n\nTrả lời:"
    # full_prompt là nội dung cuối cùng gửi cho Ollama:
    # ngữ cảnh doanh nghiệp + câu hỏi của người dùng + yêu cầu trả lời.
    status = "ok"
    error = ""

    try:
        # Nếu Ollama chạy tốt, answer là câu trả lời thật từ model local.
        answer = call_ollama(full_prompt, selected_model)
        if not answer:
            raise ValueError("Ollama trả về nội dung rỗng.")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        # Nếu Ollama lỗi, không ném lỗi ra ngoài.
        # Ta ghi status=fallback để admin biết đây không phải câu trả lời AI thật.
        status = "fallback"
        error = str(exc)
        answer = fallback_answer(message)

    # Mọi lượt hỏi đều được lưu lại để Admin AI xem lịch sử và debug.
    message_id = ai_repository.insert_ai_message(
        {
            "channel": channel,
            "user_message": message,
            "assistant_message": answer,
            "model": selected_model,
            "provider": AI_PROVIDER,
            "status": status,
            "error": error,
        }
    )
    return {
        "id": message_id,
        "answer": answer,
        "model": selected_model,
        "provider": AI_PROVIDER,
        "status": status,
        "error": error,
    }


def translate_text(source_text, target_language, source_language="", tone="", model=None):
    """Dịch nội dung sang ngôn ngữ khác bằng Ollama và lưu lịch sử vào database."""
    # source_text là nội dung admin muốn dịch, ví dụ mô tả sản phẩm hoặc đoạn tin tức.
    source_text = str(source_text or "").strip()
    target_language = str(target_language or "").strip()
    source_language = str(source_language or "").strip() or "Tự động nhận diện"
    tone = str(tone or "").strip() or "tự nhiên, chuyên nghiệp"
    if not source_text:
        raise ValueError("Vui lòng nhập nội dung cần dịch.")
    if not target_language:
        raise ValueError("Vui lòng nhập ngôn ngữ đích.")

    selected_model = model or OLLAMA_MODEL
    prompt = f"""
Bạn là AI dịch thuật cho website MecPrecision VIETNAM.
Hãy dịch nội dung kỹ thuật/cơ khí chính xác, giữ nguyên mã sản phẩm, số đo, đơn vị, tên riêng, URL và thuật ngữ CNC nếu cần.

Ngôn ngữ nguồn: {source_language}
Ngôn ngữ đích: {target_language}
Giọng văn: {tone}

Nội dung cần dịch:
{source_text}

Chỉ trả về bản dịch, không giải thích thêm.
"""
    status = "ok"
    error = ""
    try:
        translated_text = call_ollama(prompt, selected_model)
        if not translated_text:
            raise ValueError("Ollama trả về bản dịch rỗng.")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        status = "fallback"
        error = str(exc)
        translated_text = fallback_translation(source_text, target_language)

    message_id = ai_repository.insert_ai_message(
        {
            "channel": "translation",
            "user_message": f"Dịch sang {target_language}: {source_text}",
            "assistant_message": translated_text,
            "model": selected_model,
            "provider": AI_PROVIDER,
            "status": status,
            "error": error,
        }
    )
    return {
        "id": message_id,
        "answer": translated_text,
        "model": selected_model,
        "provider": AI_PROVIDER,
        "status": status,
        "error": error,
    }


def ask_developer_ai(question, code_context="", language="", model=None):
    """Trợ lý AI cho khu vực Developer: giải thích code, gợi ý debug và viết ví dụ."""
    # Hàm này chỉ tạo câu trả lời/gợi ý. Nó không tự ghi file, không chạy lệnh nguy hiểm.
    question = str(question or "").strip()
    code_context = str(code_context or "").strip()
    language = str(language or "").strip() or "Python/HTML/CSS/SQL"
    if not question:
        raise ValueError("Vui lòng nhập câu hỏi cho Developer AI.")

    selected_model = model or OLLAMA_MODEL
    prompt = f"""
Bạn là Developer AI trong CMS MecPrecision VIETNAM.
Trả lời bằng tiếng Việt có dấu, dễ hiểu cho người chưa chuyên lập trình.
Ưu tiên giải thích theo cấu trúc: nguyên nhân, cách kiểm tra, cách sửa, ví dụ ngắn.
Không đề xuất xóa dữ liệu, reset database, hoặc chạy lệnh nguy hiểm nếu không cảnh báo rõ.

Ngôn ngữ/khu vực code: {language}
Câu hỏi của admin:
{question}

Code hoặc log liên quan nếu có:
{code_context}

Trả lời:
"""
    status = "ok"
    error = ""
    try:
        answer = call_ollama(prompt, selected_model)
        if not answer:
            raise ValueError("Ollama trả về câu trả lời rỗng.")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        status = "fallback"
        error = str(exc)
        answer = fallback_developer_answer(question)

    message_id = ai_repository.insert_ai_message(
        {
            "channel": "developer_code",
            "user_message": question,
            "assistant_message": answer,
            "model": selected_model,
            "provider": AI_PROVIDER,
            "status": status,
            "error": error,
        }
    )
    return {
        "id": message_id,
        "answer": answer,
        "model": selected_model,
        "provider": AI_PROVIDER,
        "status": status,
        "error": error,
    }


def run_ai_operation(channel, user_message, prompt, fallback_message, model=None):
    """Chạy một tác vụ AI vận hành, có fallback và lưu lịch sử chung."""
    # Đây là helper dùng lại cho các module vận hành: liên hệ, báo giá, dashboard, tìm kiếm...
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

    message_id = ai_repository.insert_ai_message(
        {
            "channel": channel,
            "user_message": user_message,
            "assistant_message": answer,
            "model": selected_model,
            "provider": AI_PROVIDER,
            "status": status,
            "error": error,
        }
    )
    return {
        "id": message_id,
        "answer": answer,
        "model": selected_model,
        "provider": AI_PROVIDER,
        "status": status,
        "error": error,
    }


def summarize_recent_contacts(limit=8, model=None):
    """AI tóm tắt các liên hệ mới để admin biết khách nào cần xử lý trước."""
    contacts = query_all(
        """
        SELECT id, name, company, phone, email, country, interested_product, message, status, is_read, created_at
        FROM contact_requests
        ORDER BY id DESC
        LIMIT ?
        """,
        (int(limit or 8),),
    )
    if not contacts:
        return run_ai_operation(
            "contacts_summary",
            "Tóm tắt liên hệ mới",
            "Không có liên hệ mới.",
            "Hiện chưa có liên hệ mới để tóm tắt.",
            model,
        )

    # Khuôn mới cho phần "AI tóm tắt liên hệ mới".
    # Mục tiêu là bắt AI trả lời ngắn, có tiêu đề và bullet rõ ràng để Admin đọc nhanh.
    prompt = f"""
{build_business_context()}

Bạn là trợ lý vận hành CMS. Hãy tóm tắt các liên hệ mới thật gọn, dễ đọc cho admin không chuyên kỹ thuật.

Chỉ trả về đúng định dạng Markdown dưới đây, không viết đoạn văn dài, không thêm phần mở đầu:

### Tổng quan
- Có bao nhiêu liên hệ, tình trạng chung ra sao.

### Cần ưu tiên
- #ID - Tên/Công ty - lý do cần xử lý trước.

### Thiếu thông tin cần hỏi
- Nêu rõ khách nào thiếu email, điện thoại, sản phẩm quan tâm, file/bản vẽ hoặc nội dung yêu cầu.

### Việc cần làm tiếp theo
- Việc 1 cho nhân viên sales/kỹ thuật.
- Việc 2 nếu cần.

Quy tắc trình bày:
- Mỗi bullet chỉ 1 dòng.
- Tối đa 3 bullet cho mỗi mục.
- Nếu không có dữ liệu cho một mục, ghi: Không có.
- Ưu tiên tiếng Việt rõ ràng, ngắn gọn.

Dữ liệu liên hệ JSON:
{json.dumps(contacts, ensure_ascii=False)}
"""
    fallback = (
        "### Tổng quan\n"
        f"- Ollama chưa phản hồi, đây là bản demo gọn. Có {len(contacts)} liên hệ gần nhất cần kiểm tra.\n\n"
        "### Cần ưu tiên\n"
        "- Ưu tiên liên hệ chưa đọc, có sản phẩm quan tâm và có đủ email/điện thoại.\n\n"
        "### Thiếu thông tin cần hỏi\n"
        "- Kiểm tra lại bản vẽ/file đính kèm, số lượng, vật liệu, dung sai và deadline nếu khách chưa ghi rõ.\n\n"
        "### Việc cần làm tiếp theo\n"
        "- Sales gọi hoặc email xác nhận nhu cầu.\n"
        "- Kỹ thuật xem nội dung yêu cầu trước khi chuyển sang báo giá."
    )
    return run_ai_operation("contacts_summary", "Tóm tắt liên hệ mới", prompt, fallback, model)

    prompt = f"""
{build_business_context()}

Bạn là trợ lý vận hành CMS. Hãy tóm tắt các liên hệ mới dưới dạng:
1. Tổng quan ngắn.
2. Liên hệ cần ưu tiên.
3. Thiếu thông tin gì cần hỏi thêm.
4. Gợi ý hành động tiếp theo cho nhân viên.

Dữ liệu liên hệ JSON:
{json.dumps(contacts, ensure_ascii=False)}
"""
    fallback = (
        "Ollama chưa phản hồi. Demo tóm tắt: có "
        f"{len(contacts)} liên hệ gần nhất. Hãy ưu tiên các liên hệ chưa đọc, có sản phẩm quan tâm và có số điện thoại/email rõ ràng."
    )
    return run_ai_operation("contacts_summary", "Tóm tắt liên hệ mới", prompt, fallback, model)


def get_latest_quote_id():
    """Lấy quote mới nhất khi admin không nhập quote_id."""
    row = query_one("SELECT id FROM quote_requests ORDER BY id DESC LIMIT 1")
    return row["id"] if row else 0


def get_quote_detail_for_ai(quote_id):
    """Gom quote, customer, item và file liên quan thành một dict cho AI phân tích."""
    quote = query_one(
        """
        SELECT quote_requests.*, customers.company_name, customers.contact_name, customers.email, customers.phone, customers.country
        FROM quote_requests
        JOIN customers ON customers.id = quote_requests.customer_id
        WHERE quote_requests.id = ?
        """,
        (quote_id,),
    )
    if not quote:
        return None
    items = query_all("SELECT drawing_code, quantity, tolerance, note FROM quote_request_items WHERE quote_request_id = ?", (quote_id,))
    files = query_all("SELECT file_name, file_url, file_type FROM quote_files WHERE quote_request_id = ?", (quote_id,))
    quote["items"] = items
    quote["files"] = files
    return quote


def analyze_quote_request(quote_id=0, model=None):
    """AI phân tích yêu cầu báo giá: đủ/thiếu thông tin, độ ưu tiên, bước tiếp theo."""
    quote_id = int(quote_id or 0) or get_latest_quote_id()
    if not quote_id:
        raise ValueError("Chưa có yêu cầu báo giá để phân tích.")
    quote = get_quote_detail_for_ai(quote_id)
    if not quote:
        raise ValueError(f"Không tìm thấy yêu cầu báo giá #{quote_id}.")

    prompt = f"""
{build_business_context()}

Bạn là trợ lý báo giá cho website cơ khí chính xác.
Hãy phân tích yêu cầu báo giá này theo cấu trúc:
1. Khách hàng cần gì.
2. Thông tin đã đủ.
3. Thông tin còn thiếu cần hỏi thêm.
4. Rủi ro kỹ thuật hoặc thương mại.
5. Gợi ý email phản hồi khách.
6. Trạng thái đề xuất: pending / processing / needs_more_info / ready_to_quote.

Dữ liệu quote JSON:
{json.dumps(quote, ensure_ascii=False)}
"""
    fallback = (
        f"Ollama chưa phản hồi. Demo phân tích quote #{quote_id}: kiểm tra bản vẽ, số lượng, vật liệu, dung sai, deadline và file STEP/DWG/PDF trước khi báo giá."
    )
    return run_ai_operation("quote_analysis", f"Phân tích quote #{quote_id}", prompt, fallback, model)


def extract_text_from_uploaded_file(file_item, max_chars=12000):
    """Đọc text từ file upload để AI có thể tóm tắt catalogue/PDF."""
    if file_item is None or not getattr(file_item, "filename", ""):
        raise ValueError("Vui lòng upload file catalogue/PDF/tài liệu.")

    file_name = Path(file_item.filename).name
    raw_data = file_item.file.read()
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw_data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            # Fallback rất cơ bản: chỉ lấy text nếu PDF có text thô, không đọc được PDF scan ảnh.
            decoded = raw_data.decode("latin-1", errors="ignore")
            parts = re.findall(r"\(([^()]{3,})\)", decoded)
            text = "\n".join(parts)
    else:
        text = raw_data.decode("utf-8", errors="ignore")

    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise ValueError("Không đọc được chữ trong file. Nếu là PDF scan ảnh, cần OCR nâng cao.")
    return file_name, text[:max_chars]


def analyze_uploaded_document(file_item, question="", model=None):
    """AI đọc catalogue/PDF/tài liệu upload và trả lời câu hỏi vận hành."""
    file_name, document_text = extract_text_from_uploaded_file(file_item)
    question = str(question or "").strip() or "Tóm tắt nội dung tài liệu và chỉ ra thông tin kỹ thuật quan trọng."
    prompt = f"""
{build_business_context()}

Bạn là AI đọc tài liệu kỹ thuật/cataloque cho CMS.
Hãy trả lời bằng tiếng Việt, tập trung vào thông tin sản phẩm, vật liệu, thông số, ứng dụng, điểm cần lưu ý.

Tên file: {file_name}
Câu hỏi của admin: {question}

Nội dung trích xuất:
{document_text}
"""
    fallback = f"Ollama chưa phản hồi. Demo đọc file {file_name}: hệ thống đã trích xuất được {len(document_text)} ký tự, hãy kiểm tra lại nội dung file hoặc bật Ollama để AI tóm tắt."
    return run_ai_operation("document_reader", f"Đọc tài liệu {file_name}: {question}", prompt, fallback, model)


def score_search_item(query, item, fields):
    """Tính điểm tìm kiếm đơn giản theo số lần keyword xuất hiện."""
    query_words = [word for word in re.split(r"\W+", query.lower()) if len(word) >= 2]
    haystack = " ".join(str(item.get(field, "")) for field in fields).lower()
    return sum(haystack.count(word) for word in query_words)


def smart_search_content(query, scope="all", model=None):
    """AI tìm kiếm thông minh trong sản phẩm/tin tức và tóm tắt kết quả phù hợp."""
    query = str(query or "").strip()
    scope = str(scope or "all").strip()
    if not query:
        raise ValueError("Vui lòng nhập từ khóa/câu hỏi cần tìm.")

    matches = []
    if scope in {"all", "products"}:
        products = query_all(
            """
            SELECT products.id, products.name, products.short_description, products.description, products.tags_text,
                   product_categories.name AS category
            FROM products
            JOIN product_categories ON product_categories.id = products.category_id
            WHERE products.status = 'published'
            """
        )
        for product in products:
            score = score_search_item(query, product, ["name", "short_description", "description", "tags_text", "category"])
            if score:
                product["type"] = "product"
                product["score"] = score
                matches.append(product)
    if scope in {"all", "news"}:
        news_items = get_news(limit=None)
        for item in news_items:
            score = score_search_item(query, item, ["title", "description", "category"])
            if score:
                item["type"] = "news"
                item["score"] = score
                matches.append(item)

    matches = sorted(matches, key=lambda item: item["score"], reverse=True)[:8]
    if not matches:
        fallback = f"Không tìm thấy kết quả rõ ràng cho: {query}."
        return run_ai_operation("smart_search", f"Tìm kiếm: {query}", fallback, fallback, model)

    prompt = f"""
{build_business_context()}

Admin đang tìm kiếm: {query}
Phạm vi: {scope}

Hãy đọc danh sách kết quả và trả lời:
1. Kết quả phù hợp nhất.
2. Vì sao phù hợp.
3. Gợi ý sản phẩm/tin tức liên quan.
4. Nếu chưa đủ dữ liệu, cần bổ sung gì vào CMS.

Kết quả JSON:
{json.dumps(matches, ensure_ascii=False)}
"""
    fallback = f"Ollama chưa phản hồi. Tìm thấy {len(matches)} kết quả gần nhất cho '{query}'. Kết quả đầu tiên: {matches[0].get('name') or matches[0].get('title')}."
    return run_ai_operation("smart_search", f"Tìm kiếm: {query}", prompt, fallback, model)


def generate_dashboard_insights(model=None):
    """AI dashboard: nêu hôm nay website có gì cần chú ý."""
    stats = {
        "products": query_one("SELECT COUNT(*) AS total FROM products")["total"],
        "published_products": query_one("SELECT COUNT(*) AS total FROM products WHERE status = 'published'")["total"],
        "news": query_one("SELECT COUNT(*) AS total FROM news")["total"],
        "new_contacts": query_one("SELECT COUNT(*) AS total FROM contact_requests WHERE status = 'new' OR is_read = 0")["total"],
        "quotes_new": query_one("SELECT COUNT(*) AS total FROM quote_requests WHERE status IN ('new', 'pending')")["total"],
        "queue_failed": query_one("SELECT COUNT(*) AS total FROM job_queue WHERE status = 'failed'")["total"],
        "ai_fallback_today": query_one("SELECT COUNT(*) AS total FROM ai_conversations WHERE status = 'fallback' AND date(created_at) = date('now')")["total"],
    }
    contacts = query_all("SELECT id, name, company, interested_product, status, created_at FROM contact_requests ORDER BY id DESC LIMIT 5")
    quotes = query_all("SELECT id, project_name, status, created_at FROM quote_requests ORDER BY id DESC LIMIT 5")
    prompt = f"""
{build_business_context()}

Bạn là AI dashboard cho admin website.
Hãy trả lời câu hỏi: "Hôm nay website có gì cần chú ý?"
Trả lời theo nhóm: việc khẩn cấp, dữ liệu kinh doanh, lỗi hệ thống/AI, hành động đề xuất.

Số liệu:
{json.dumps(stats, ensure_ascii=False)}

Liên hệ gần nhất:
{json.dumps(contacts, ensure_ascii=False)}

Báo giá gần nhất:
{json.dumps(quotes, ensure_ascii=False)}
"""
    fallback = (
        f"Ollama chưa phản hồi. Demo dashboard: liên hệ mới/chưa đọc={stats['new_contacts']}, "
        f"quote mới={stats['quotes_new']}, job lỗi={stats['queue_failed']}, AI fallback hôm nay={stats['ai_fallback_today']}."
    )
    return run_ai_operation("dashboard_insights", "AI dashboard hôm nay", prompt, fallback, model)


def build_product_content_fallback(product):
    """Tạo nội dung sản phẩm cơ bản khi AI không trả JSON hợp lệ."""
    name = product["name"]
    category = product.get("category_name") or "cơ khí chính xác"
    short_description = product.get("short_description") or f"{name} dùng cho sản xuất công nghiệp."
    description = (
        f"{name} thuộc nhóm {category}, phù hợp cho các ứng dụng cần độ ổn định, "
        "độ chính xác và khả năng gia công theo bản vẽ kỹ thuật. "
        "Sản phẩm có thể được tùy chỉnh theo vật liệu, số lượng, dung sai và yêu cầu xử lý bề mặt của khách hàng."
    )
    return {
        "description": description,
        "seo_title": f"{name} | Gia công cơ khí chính xác",
        "seo_description": short_description[:155],
        "seo_keywords": f"{name}, {category}, gia công CNC, cơ khí chính xác",
        "tags_text": f"{category}, cnc, cơ khí chính xác",
        "schema_json": json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": name,
                "description": short_description,
            },
            ensure_ascii=False,
        ),
    }


def normalize_product_ai_fields(product, data):
    """Chuẩn hóa các field AI trả về để có thể điền thẳng vào form Products."""
    fallback = build_product_content_fallback(product)
    normalized = {}
    for key, fallback_value in fallback.items():
        value = str(data.get(key, "")).strip() if isinstance(data, dict) else ""
        normalized[key] = value or fallback_value

    # SEO title nên ngắn để dễ đọc trên Google.
    normalized["seo_title"] = normalized["seo_title"][:80]
    # SEO description nên vừa đủ dài, không lan man.
    normalized["seo_description"] = normalized["seo_description"][:180]
    # Nếu AI trả schema_json không phải JSON, dùng schema fallback cho an toàn.
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
    selected_model = model or OLLAMA_MODEL
    prompt = f"""
{build_business_context()}

Bạn hãy tạo nội dung sản phẩm và SEO cho CMS.
Chỉ trả về JSON hợp lệ, không viết giải thích bên ngoài JSON.

Thông tin sản phẩm:
- Tên: {product["name"]}
- Danh mục: {product["category_name"]}
- SKU: {product["sku"]}
- Mô tả ngắn hiện có: {product["short_description"]}
- Mô tả chi tiết hiện có: {product["description"]}
- Tag hiện có: {product["tags_text"]}

JSON cần có đúng các key:
{{
  "description": "mô tả chi tiết 2-3 đoạn, dễ hiểu, chuyên nghiệp",
  "seo_title": "tiêu đề SEO dưới 70 ký tự",
  "seo_description": "mô tả SEO dưới 160 ký tự",
  "seo_keywords": "5-8 từ khóa, phân tách bằng dấu phẩy",
  "tags_text": "4-6 tag, phân tách bằng dấu phẩy",
  "schema_json": "JSON-LD Product dạng chuỗi"
}}
"""
    status = "ok"
    error = ""
    raw_answer = ""
    try:
        raw_answer = call_ollama(prompt, selected_model)
        fields = normalize_product_ai_fields(product, extract_json_object(raw_answer))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        status = "fallback"
        error = str(exc)
        fields = build_product_content_fallback(product)

    message_id = ai_repository.insert_ai_message(
        {
            "channel": "product_content",
            "user_message": f"Tạo nội dung sản phẩm: {name}",
            "assistant_message": json.dumps(fields, ensure_ascii=False),
            "model": selected_model,
            "provider": AI_PROVIDER,
            "status": status,
            "error": error or ("" if raw_answer else "empty raw answer"),
        }
    )
    return {
        "id": message_id,
        "fields": fields,
        "model": selected_model,
        "provider": AI_PROVIDER,
        "status": status,
        "error": error,
    }


def get_recent_ai_messages(limit=20):
    """Lấy lịch sử hỏi đáp AI gần nhất."""
    return ai_repository.list_recent_ai_messages(limit)


def get_ai_status():
    """Trạng thái cấu hình AI để hiển thị trong Admin."""
    return {
        "provider": AI_PROVIDER,
        "ollama_url": OLLAMA_URL,
        "model": OLLAMA_MODEL,
        "timeout_seconds": OLLAMA_TIMEOUT_SECONDS,
    }
