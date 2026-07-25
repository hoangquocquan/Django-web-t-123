import http.client
import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace


# File test này dùng unittest có sẵn của Python.
# Mục tiêu là kiểm tra tự động các lớp quan trọng:
# service/repository, controller/cache, transaction và endpoint API.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
TEST_DATABASE_PATH = Path(tempfile.mkdtemp(prefix="mecprecision-test-")) / "mecprecision_test.sqlite"

# Thiết lập môi trường test trước khi import code backend.
# Nhờ vậy service/repository sẽ dùng database tạm, không đụng database thật.
os.environ["MEC_ENV"] = "test"
os.environ["MEC_DEBUG"] = "true"
os.environ["MEC_DATABASE_PATH"] = str(TEST_DATABASE_PATH)
sys.path.insert(0, str(BACKEND_ROOT))

from app import MecPrecisionHandler  # noqa: E402
from auth.passwords import verify_password  # noqa: E402
from auth.sessions import create_admin_session, delete_admin_sessions_for_user, list_admin_sessions  # noqa: E402
from cache.redis_cache import get_json, is_cache_enabled, set_json  # noqa: E402
from controllers.api_controller import get_product_response, list_products_response  # noqa: E402
from database.connection import get_connection, transaction  # noqa: E402
from database.migrations import ensure_cms_tables  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402
from repositories import auth_repository  # noqa: E402
from services.activity_service import get_recent_activity_logs, log_admin_activity  # noqa: E402
import services.ai_service as ai_service  # noqa: E402
from services.auth_service import list_auth_email_outbox, request_password_reset, reset_password_with_token, set_account_active  # noqa: E402
from services.cms_service import (  # noqa: E402
    get_active_banners,
    get_newsletter_csv_rows,
    get_public_page_by_slug,
    save_banner,
    save_newsletter,
    save_page,
)
from services.developer_service import create_database_backup, get_health_status, get_system_info  # noqa: E402
from services.event_service import get_recent_events, publish_event  # noqa: E402
from services.dashboard_service import get_dashboard_stats, track_page_visit  # noqa: E402
from services.media_service import create_folder, delete_media, list_media, rename_media, save_media_file  # noqa: E402
from services.notification_service import get_recent_notifications  # noqa: E402
from services.products_service import create_product, get_products, normalize_product_payload  # noqa: E402
from services.queue_service import get_queue_summary, process_pending_jobs  # noqa: E402
from services.security_service import make_captcha_challenge, verify_captcha, make_csrf_token, verify_csrf_token  # noqa: E402
from services.users_service import save_user  # noqa: E402
from utils.exceptions import AppError  # noqa: E402
from utils.uploads import save_uploaded_file  # noqa: E402


def init_test_database():
    """Tạo database test từ schema.sql và seed.sql."""
    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink()
    # schema.sql tạo bảng, seed.sql thêm dữ liệu mẫu cho test.
    schema_sql = (BACKEND_ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    seed_sql = (BACKEND_ROOT / "database" / "seed.sql").read_text(encoding="utf-8")
    with sqlite3.connect(TEST_DATABASE_PATH) as connection:
        connection.executescript(schema_sql)
        connection.executescript(seed_sql)
        connection.commit()
    ensure_cms_tables()


def setUpModule():
    """Chạy một lần trước toàn bộ test trong file này."""
    init_test_database()


class ServiceRepositoryTest(unittest.TestCase):
    """Unit test cho service và repository."""

    def test_get_products_reads_from_repository(self):
        # Kiểm tra service get_products đọc được dữ liệu từ repository/database.
        products = get_products()

        self.assertGreaterEqual(len(products), 3)
        self.assertIn("name", products[0])
        self.assertIn("category", products[0])

    def test_normalize_product_payload_validates_required_fields(self):
        # Nếu thiếu dữ liệu bắt buộc, service phải báo ValueError.
        with self.assertRaises(ValueError):
            normalize_product_payload({"category_id": 1, "name": ""})

    def test_create_user_requires_password_and_valid_email(self):
        # Khi tạo user mới, backend cần báo lỗi rõ nếu thiếu mật khẩu hoặc email sai.
        with self.assertRaises(ValueError):
            save_user({"full_name": "Missing Password", "email": "missing@example.com", "role": "viewer"})
        with self.assertRaises(ValueError):
            save_user({"full_name": "Bad Email", "email": "bad-email", "password": "secret123", "role": "viewer"})

    def test_create_product_writes_to_database(self):
        # Kiểm tra tạo sản phẩm thật vào database test.
        product = create_product(
            {
                "category_id": 1,
                "name": "Sản phẩm unit test",
                "slug": "san-pham-unit-test",
                "short_description": "Mô tả ngắn",
                "description": "Mô tả chi tiết",
                "main_image": "https://example.com/unit-test.jpg",
                "is_featured": False,
            }
        )

        self.assertEqual(product["name"], "Sản phẩm unit test")

    def test_transaction_rolls_back_when_error_happens(self):
        # Tạo bảng phụ chỉ phục vụ test rollback.
        with get_connection() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS transaction_test (id INTEGER PRIMARY KEY, name TEXT)")
            connection.commit()

        with self.assertRaises(RuntimeError):
            with transaction() as connection:
                connection.execute("INSERT INTO transaction_test (name) VALUES (?)", ("rollback",))
                # Cố tình gây lỗi sau khi INSERT để transaction phải rollback.
                raise RuntimeError("Lỗi giả lập để kiểm tra rollback")

        with get_connection() as connection:
            count = connection.execute("SELECT COUNT(*) FROM transaction_test WHERE name = ?", ("rollback",)).fetchone()[0]

        self.assertEqual(count, 0)


class ControllerCacheTest(unittest.TestCase):
    """Unit test cho controller và cache layer."""

    def test_controller_returns_data_and_status(self):
        # Controller phải trả về tuple (data, status).
        data, status = list_products_response()

        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)

    def test_controller_raises_app_error_when_product_missing(self):
        # Khi không tìm thấy sản phẩm, controller ném AppError để exception handler xử lý.
        with self.assertRaises(AppError) as context:
            get_product_response(999999)

        self.assertEqual(context.exception.status, 404)
        self.assertEqual(context.exception.code, "PRODUCT_NOT_FOUND")

    def test_redis_cache_is_optional_in_test_environment(self):
        # Môi trường test không bật Redis, nên các hàm cache phải trả None an toàn.
        self.assertFalse(is_cache_enabled())
        self.assertIsNone(get_json("missing"))
        self.assertIsNone(set_json("missing", {"ok": True}, ttl_seconds=1))


class DashboardFeatureTest(unittest.TestCase):
    """Unit test cho dashboard và biểu đồ lượt truy cập."""

    def test_dashboard_has_counts_and_chart_ranges(self):
        track_page_visit("/", "127.0.0.1", "UnitTest")
        stats = get_dashboard_stats()

        self.assertIn("products", stats["counts"])
        self.assertIn("visits", stats["counts"])
        self.assertEqual(len(stats["charts"]["7_days"]), 7)
        self.assertEqual(len(stats["charts"]["30_days"]), 30)
        self.assertEqual(len(stats["charts"]["12_months"]), 12)


class MediaManagerTest(unittest.TestCase):
    """Unit test cho Media Manager."""

    def test_uploaded_file_object_does_not_need_bool_conversion(self):
        # cgi.FieldStorage sẽ lỗi nếu code kiểm tra kiểu `if not file_item`.
        class BoolBlockingUpload:
            filename = ""

            def __bool__(self):
                raise TypeError("Cannot be converted to bool.")

        self.assertEqual(save_uploaded_file(BoolBlockingUpload(), "avatars"), "")
        with self.assertRaises(ValueError):
            save_media_file(BoolBlockingUpload(), "images")

    def test_media_folder_upload_search_rename_delete(self):
        folder = "unit-test-media"
        create_folder(folder)
        fake_file = SimpleNamespace(filename="Demo Image.png", file=BytesIO(b"fake image bytes"))

        uploaded_url = save_media_file(fake_file, folder)
        found_items = list_media(folder, "demo-image")
        renamed_url = rename_media(uploaded_url, "renamed-demo")
        deleted_url = delete_media(renamed_url)

        self.assertTrue(uploaded_url.startswith(f"/uploads/{folder}/"))
        self.assertGreaterEqual(len(found_items), 1)
        self.assertTrue(renamed_url.endswith(".png"))
        self.assertEqual(deleted_url, renamed_url)


class AdvancedCmsTest(unittest.TestCase):
    """Unit test cho các module CMS giai đoạn 2 và 3."""

    def test_dynamic_page_can_be_published_and_read_by_slug(self):
        # Tạo page giống About/Privacy trong CMS, sau đó đọc public bằng slug.
        save_page(
            {
                "title": "About Unit Test",
                "slug": "about-unit-test",
                "content": "Nội dung trang động",
                "seo_title": "About SEO",
                "seo_description": "Mô tả SEO",
                "status": "published",
                "sort_order": 1,
            }
        )
        page = get_public_page_by_slug("about-unit-test")

        self.assertEqual(page["title"], "About Unit Test")
        self.assertEqual(page["seo_title"], "About SEO")

    def test_banner_and_newsletter_are_saved_for_cms(self):
        # Banner published sẽ được trang chủ đọc qua get_active_banners.
        save_banner(
            {
                "title": "Banner Unit Test",
                "placement": "home_slider",
                "image_url": "https://example.com/banner.jpg",
                "link_url": "/san-pham",
                "content": "Banner từ CMS",
                "sort_order": 1,
                "status": "published",
            }
        )
        save_newsletter({"email": "cms-unit@example.com", "status": "subscribed"})

        banners = get_active_banners("home_slider")
        subscribers = get_newsletter_csv_rows()

        self.assertTrue(any(item["title"] == "Banner Unit Test" for item in banners))
        self.assertTrue(any(item["email"] == "cms-unit@example.com" for item in subscribers))


class AiServiceTest(unittest.TestCase):
    """Unit test cho AI Service dùng Ollama local."""

    def test_ai_requires_message(self):
        with self.assertRaises(ValueError):
            ai_service.ask_ai("", channel="test")

    def test_ai_fallback_is_saved_when_ollama_fails(self):
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: (_ for _ in ()).throw(ValueError("ollama offline"))
        try:
            result = ai_service.ask_ai("MecPrecision có gia công CNC không?", channel="test", model="unit-test-model")
        finally:
            ai_service.call_ollama = original_call_ollama

        history = ai_service.get_recent_ai_messages(5)

        self.assertEqual(result["status"], "fallback")
        self.assertIn("Ollama", result["answer"])
        self.assertTrue(any(item["model"] == "unit-test-model" for item in history))

    def test_ai_generates_product_content_fields(self):
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: json.dumps(
            {
                "description": "Mô tả AI cho sản phẩm CNC.",
                "seo_title": "SEO Trục CNC",
                "seo_description": "Mô tả SEO ngắn cho trục CNC.",
                "seo_keywords": "trục CNC, gia công CNC",
                "tags_text": "cnc, trục chính xác",
                "schema_json": "{\"@context\":\"https://schema.org\",\"@type\":\"Product\",\"name\":\"Trục CNC\"}",
            },
            ensure_ascii=False,
        )
        try:
            result = ai_service.generate_product_content(
                {
                    "name": "Trục CNC",
                    "category_name": "Trục",
                    "short_description": "Trục chính xác cao",
                },
                model="unit-test-model",
            )
        finally:
            ai_service.call_ollama = original_call_ollama

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["fields"]["seo_title"], "SEO Trục CNC")
        self.assertIn("trục CNC", result["fields"]["seo_keywords"])


    def test_ai_translates_text(self):
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: "Precision CNC shaft"
        try:
            result = ai_service.translate_text(
                "Trục CNC chính xác",
                "English",
                source_language="Vietnamese",
                model="unit-test-model",
            )
        finally:
            ai_service.call_ollama = original_call_ollama

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["answer"], "Precision CNC shaft")
        self.assertGreater(result["id"], 0)

    def test_developer_ai_answers_code_question(self):
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: "Kiểm tra route, service và log lỗi trước."
        try:
            result = ai_service.ask_developer_ai(
                "Vì sao route admin bị lỗi 500?",
                code_context="ValueError: demo",
                language="Python",
                model="unit-test-model",
            )
        finally:
            ai_service.call_ollama = original_call_ollama

        self.assertEqual(result["status"], "ok")
        self.assertIn("route", result["answer"])
        self.assertGreater(result["id"], 0)

    def test_ai_operations_can_summarize_contacts_and_dashboard(self):
        # Giả lập Ollama để kiểm tra luồng service AI vận hành mà không cần bật model thật.
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: "AI đã phân tích dữ liệu vận hành."
        try:
            contacts_result = ai_service.summarize_recent_contacts(limit=3, model="unit-test-model")
            dashboard_result = ai_service.generate_dashboard_insights(model="unit-test-model")
        finally:
            ai_service.call_ollama = original_call_ollama

        self.assertEqual(contacts_result["status"], "ok")
        self.assertEqual(dashboard_result["status"], "ok")
        self.assertIn("phân tích", contacts_result["answer"])
        self.assertIn("phân tích", dashboard_result["answer"])

    def test_ai_can_analyze_quote_and_search_content(self):
        # Quote/search đọc dữ liệu mẫu từ SQLite, sau đó đưa kết quả vào prompt cho AI.
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: "Kết quả phù hợp nhất là trục CNC chính xác."
        try:
            quote_result = ai_service.analyze_quote_request(1, model="unit-test-model")
            search_result = ai_service.smart_search_content("trục CNC", scope="all", model="unit-test-model")
        finally:
            ai_service.call_ollama = original_call_ollama

        self.assertEqual(quote_result["status"], "ok")
        self.assertEqual(search_result["status"], "ok")
        self.assertIn("trục CNC", search_result["answer"])

    def test_ai_can_read_uploaded_text_document(self):
        # Demo đọc tài liệu dùng TXT để test nhanh; PDF text cũng dùng chung hàm extract_text_from_uploaded_file().
        fake_file = SimpleNamespace(
            filename="catalogue.txt",
            file=BytesIO("Catalogue trục CNC chính xác, dung sai ±0.01mm.".encode("utf-8")),
        )
        original_call_ollama = ai_service.call_ollama
        ai_service.call_ollama = lambda prompt, model=None: "Tài liệu nói về trục CNC dung sai chính xác."
        try:
            result = ai_service.analyze_uploaded_document(fake_file, question="Tóm tắt tài liệu", model="unit-test-model")
        finally:
            ai_service.call_ollama = original_call_ollama

        self.assertEqual(result["status"], "ok")
        self.assertIn("trục CNC", result["answer"])


class SecurityDeveloperTest(unittest.TestCase):
    """Unit test cho Security và Developer tools."""

    def test_csrf_and_captcha_helpers(self):
        csrf_token = make_csrf_token("session-demo")
        captcha = make_captcha_challenge()

        self.assertTrue(verify_csrf_token("session-demo", csrf_token))
        self.assertFalse(verify_csrf_token("session-demo", "sai-token"))
        self.assertIn("token", captcha)

    def test_health_system_info_and_backup(self):
        health = get_health_status()
        system_info = get_system_info()
        backup_path = create_database_backup()

        self.assertEqual(health["status"], "ok")
        self.assertIn("python", system_info)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.name.endswith(".sqlite"))

    def test_event_queue_notification_and_email_flow(self):
        # Event mô phỏng một khách hàng gửi form liên hệ trên website.
        event_id = publish_event(
            "contact.created",
            "contact_request",
            "unit-test-contact",
            {"name": "Khách test", "contact": "khach-test@example.com"},
        )
        queue_before_worker = get_queue_summary()

        # Worker lấy job pending trong queue và xử lý thành notification/email.
        processed_jobs = process_pending_jobs(limit=10)
        events = get_recent_events(10)
        notifications = get_recent_notifications(10)
        emails = list_auth_email_outbox(10)

        self.assertGreater(event_id, 0)
        self.assertGreaterEqual(queue_before_worker["counts"].get("pending", 0), 2)
        self.assertTrue(any(item["event_name"] == "contact.created" for item in events))
        self.assertTrue(all(item["status"] == "succeeded" for item in processed_jobs))
        self.assertTrue(any(item["title"] == "Liên hệ mới" for item in notifications))
        self.assertTrue(any(item["subject"] == "MecPrecision - Có liên hệ mới" for item in emails))


class AuthenticationFeatureTest(unittest.TestCase):
    """Unit test cho các chức năng authentication mới."""

    def test_request_and_reset_password_by_email_token(self):
        reset_link = request_password_reset("admin@mecprecision.vn", "http://127.0.0.1:8000")
        token = reset_link.split("token=", 1)[1]

        reset_password_with_token(token, "new-password-123")
        admin = auth_repository.get_admin_by_email_any_status("admin@mecprecision.vn")

        self.assertTrue(verify_password("new-password-123", admin["password_hash"]))

    def test_lock_and_unlock_account(self):
        admin = auth_repository.get_admin_by_email_any_status("admin@mecprecision.vn")

        set_account_active(admin["id"], False)
        locked = auth_repository.get_admin_by_id(admin["id"])
        self.assertEqual(locked["is_active"], 0)

        set_account_active(admin["id"], True)
        unlocked = auth_repository.get_admin_by_id(admin["id"])
        self.assertEqual(unlocked["is_active"], 1)

    def test_multiple_sessions_can_be_listed(self):
        admin = auth_repository.get_admin_by_email_any_status("admin@mecprecision.vn")
        delete_admin_sessions_for_user(admin["id"])

        first_session = create_admin_session(admin, remote_addr="127.0.0.1", user_agent="Test Browser A")
        second_session = create_admin_session(admin, remote_addr="127.0.0.2", user_agent="Test Browser B")
        sessions = list_admin_sessions(admin["id"])

        self.assertEqual(len(sessions), 2)
        self.assertIn(first_session, {item["session_id"] for item in sessions})
        self.assertIn(second_session, {item["session_id"] for item in sessions})

    def test_user_avatar_and_activity_log(self):
        admin = auth_repository.get_admin_by_email_any_status("admin@mecprecision.vn")
        user = save_user(
            {
                "full_name": "Avatar Test",
                "email": "avatar-test@example.com",
                "password": "secret123",
                "role": "viewer",
                "is_active": "1",
                "avatar_url": "/uploads/avatars/demo.png",
            }
        )
        log_admin_activity(
            {"admin_id": admin["id"], "full_name": admin["full_name"], "email": admin["email"]},
            "user.create",
            "admin_user",
            user["id"],
            "Tạo user test có avatar",
            "127.0.0.1",
        )
        logs = get_recent_activity_logs(1)

        self.assertEqual(user["avatar_url"], "/uploads/avatars/demo.png")
        self.assertEqual(logs[0]["action"], "user.create")


class EndpointIntegrationTest(unittest.TestCase):
    """Integration test cho các endpoint quan trọng."""

    @classmethod
    def setUpClass(cls):
        # Bật server thật trên port ngẫu nhiên để test API giống trình duyệt gọi thật.
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MecPrecisionHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request_json(self, method, path, payload=None):
        # Helper này gửi HTTP request và parse JSON response cho các test endpoint.
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = response.read().decode("utf-8")
        connection.close()
        return response.status, json.loads(data)

    def test_openapi_endpoint_returns_schema(self):
        status, data = self.request_json("GET", "/api/openapi.json")

        self.assertEqual(status, 200)
        self.assertEqual(data["openapi"], "3.0.3")
        self.assertIn("/api/products", data["paths"])

    def test_products_endpoint_returns_products(self):
        status, data = self.request_json("GET", "/api/products")

        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 3)

    def test_contact_endpoint_returns_consistent_validation_error(self):
        status, data = self.request_json("POST", "/api/contact", {"name": "", "contact": ""})

        self.assertEqual(status, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "VALIDATION_ERROR")

    def test_unknown_api_returns_consistent_404_error(self):
        status, data = self.request_json("GET", "/api/khong-ton-tai")

        self.assertEqual(status, 404)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "API_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
