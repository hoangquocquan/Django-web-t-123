from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import cgi
import gzip
import urllib.error
import urllib.request
import json
import logging
import mimetypes
import re
import sqlite3
import csv
import io

from auth.passwords import (
    hash_password,
    password_hash_needs_upgrade,
    upgrade_admin_password_hash,
    verify_password,
)
from api.openapi import get_openapi_schema
from auth.permissions import has_admin_permission
from auth.sessions import (
    cleanup_expired_sessions,
    create_admin_session,
    delete_admin_session,
    delete_admin_session_for_user,
    get_admin_session,
    is_login_rate_limited,
    list_admin_sessions,
    record_login_attempt,
)
from controllers.api_controller import (
    create_contact_response,
    create_product_response,
    delete_product_response,
    get_home_response,
    get_product_response,
    list_capabilities_response,
    list_news_response,
    list_product_categories_response,
    list_products_response,
    openapi_response,
    update_product_response,
)
from config.settings import (
    DEBUG,
    ENVIRONMENT,
    FRONTEND_ROOT,
    HOST,
    OLLAMA_MODEL,
    PORT,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    UPLOAD_ROOT,
)
from database.migrations import ensure_cms_tables
from middleware.exception_handler import handle_request_exception
from middleware.security_headers import send_security_headers as apply_security_headers
from services.categories_service import (
    delete_category,
    get_category_record,
    get_paginated_categories,
    save_category,
)
from services.contacts_service import (
    delete_contact,
    get_contact_record,
    get_contacts_csv_rows,
    get_paginated_contacts,
    get_recent_contact_requests,
    save_contact,
)
from services.dashboard_service import get_dashboard_stats, track_page_visit
from services.media_service import (
    create_folder,
    delete_media,
    list_folders,
    list_media,
    rename_media,
    save_media_file,
)
from services.news_service import (
    delete_news,
    get_news_categories,
    get_news_record,
    get_paginated_news,
    save_news,
)
from services.products_service import (
    create_product,
    delete_product,
    get_product_categories,
    get_paginated_products,
    get_product_record,
    get_products,
    update_product,
)
from services.auth_service import (
    change_email,
    change_password,
    list_auth_email_outbox,
    request_password_reset,
    reset_password_with_token,
    set_account_active,
)
from services.activity_service import get_recent_activity_logs, log_admin_activity
from services.ai_service import (
    analyze_quote_request,
    analyze_uploaded_document,
    ask_ai,
    ask_developer_ai,
    generate_dashboard_insights,
    generate_product_content,
    get_ai_status,
    get_recent_ai_messages,
    smart_search_content,
    summarize_recent_contacts,
    translate_text,
)
from services.developer_service import (
    API_VERSION,
    clear_runtime_cache,
    create_database_backup,
    get_health_status,
    get_system_info,
    list_database_backups,
    read_recent_logs,
    run_migrations,
)
from services.event_service import get_recent_events, publish_event
from services.notification_service import get_recent_notifications
from services.queue_service import get_queue_summary, process_pending_jobs
from services.security_service import (
    get_session_ttl,
    inject_csrf_token,
    is_ip_allowed,
    make_captcha_challenge,
    set_two_factor_enabled,
    verify_captcha,
    verify_csrf_token,
    create_two_factor_challenge,
    verify_two_factor_challenge,
)
from services.cms_service import (
    add_customer_note,
    create_public_quote_request,
    delete_banner,
    delete_customer,
    delete_menu_item,
    delete_newsletter,
    delete_page,
    get_active_banners,
    get_admin_options,
    get_banner_record,
    get_customer_notes,
    get_customer_record,
    get_menu_items,
    get_menu_record,
    get_newsletter_csv_rows,
    get_newsletter_record,
    get_page_record,
    get_paginated_banners,
    get_paginated_customers,
    get_paginated_newsletter,
    get_paginated_pages,
    get_paginated_quotes,
    get_public_page_by_slug,
    get_quote_record,
    save_banner,
    save_customer,
    save_menu_item,
    save_newsletter,
    save_page,
    save_quote,
)
from services.public_service import get_capabilities, get_home_data, get_news
from services.settings_service import get_system_settings, save_system_settings
from services.localization_service import (
    build_language_url,
    get_language_meta,
    normalize_language,
    translate_public_html,
)
from services.users_service import (
    delete_user,
    get_admin_by_email,
    get_paginated_users,
    get_user_record,
    save_user,
)
from utils.logging_config import setup_logging
from utils.routing import parse_admin_item_path, parse_product_api_id
from utils.text import (
    build_query_string,
    get_page_offset,
    h,
    make_slug,
    parse_bool,
    parse_positive_int,
)
from utils.uploads import save_uploaded_file

LOGGER = logging.getLogger("mecprecision")


def format_ai_result_html(text):
    """Chuyển câu trả lời AI dạng text/Markdown đơn giản thành HTML dễ đọc trong Admin."""
    # Không render trực tiếp nội dung AI thành HTML để tránh rủi ro chèn mã lạ.
    # Từng dòng đều đi qua h() trước khi hiển thị.
    lines = str(text or "").splitlines()
    html_parts = []
    list_open = False

    def close_list():
        nonlocal list_open
        if list_open:
            html_parts.append("</ul>")
            list_open = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            close_list()
            continue

        heading_match = re.match(r"^(?:#{1,3}\s+|\d+\.\s+)(.+)$", line)
        if heading_match:
            close_list()
            title = heading_match.group(1).strip().strip("*: ")
            html_parts.append(f"<h3>{h(title)}</h3>")
            continue

        if line.startswith(("- ", "* ", "• ")):
            if not list_open:
                html_parts.append("<ul>")
                list_open = True
            html_parts.append(f"<li>{h(line[2:].strip())}</li>")
            continue

        close_list()
        html_parts.append(f"<p>{h(line)}</p>")

    close_list()
    return f'<div class="ai-result">{("".join(html_parts) or "<p>Chưa có nội dung.</p>")}</div>'


def get_public_menu_items(location):
    """Lấy menu published theo vị trí để header/footer đọc từ CMS."""
    return [
        item
        for item in get_menu_items()
        if item.get("location") == location and item.get("status") == "published" and not item.get("parent_id")
    ]


def localized_public_href(href, language):
    """Thêm tham số lang vào link public để giữ ngôn ngữ khi chuyển trang."""
    language = normalize_language(language)
    if language == "vi" or href.startswith("/admin") or href.startswith("http"):
        return href
    separator = "&" if "?" in href else "?"
    return f"{href}{separator}lang={language}"


def render_language_switcher(active_page, language):
    """Tạo cụm nút đổi ngôn ngữ VI / EN / JA trên header public."""
    page_paths = {
        "index": "/",
        "products": "/san-pham.html",
        "technology": "/cong-nghe.html",
        "news": "/tin-tuc.html",
        "api-aws": "/api-aws.html",
        "contact": "/lien-he.html",
    }
    current_path = page_paths.get(active_page, "/")
    language = normalize_language(language)
    items = [("vi", "VI"), ("en", "EN"), ("ja", "JA")]
    return "".join(
        f'<a data-language-switch="1" class="{"active" if code == language else ""}" href="{h(build_language_url(current_path, code))}" title="{h(get_language_meta(code)["label"])}">{label}</a>'
        for code, label in items
    )


def render_header(active_page, language="vi"):
    """Header dùng chung cho các trang động."""
    # active_page giúp menu hiện màu xanh ở trang hiện tại.
    language = normalize_language(language)
    settings = get_system_settings()
    links = [
        ("index", "Trang chủ", "/"),
        ("products", "Sản phẩm", "/san-pham.html"),
        ("technology", "Công nghệ", "/cong-nghe.html"),
        ("news", "Tin tức", "/tin-tuc.html"),
        ("api-aws", "API & AWS", "/api-aws.html"),
        ("contact", "Liên hệ", "/lien-he.html"),
        ("admin", "Đăng nhập", "/admin/login"),
    ]
    cms_links = get_public_menu_items("header")
    if cms_links:
        links = [(item["url"], item["label"], item["url"]) for item in cms_links]

    nav_links = "\n".join(
        # Tạo danh sách thẻ <a> từ mảng links ở trên.
        f'<a class="{"active" if key == active_page else ""}" href="{h(localized_public_href(href, language))}">{label}</a>'
        for key, label, href in links
    )

    # Nếu đang ở trang admin thì nút bên phải ghi Admin, còn trang thường ghi Đăng nhập.
    header_cta_href = "/admin" if active_page == "admin" else "/admin/login"
    header_cta_label = "Admin" if active_page == "admin" else "Đăng nhập"

    logo_html = (
        f'<img class="brand-logo" src="{h(settings["logo_url"])}" alt="{h(settings["company_name"])}" />'
        if settings.get("logo_url")
        else '<span class="brand-mark">M</span>'
    )
    return f"""
    <header class="site-header">
      <a class="brand" href="/" aria-label="{h(settings["company_name"])}">
        {logo_html}
        <span>{h(settings["company_name"])}</span>
      </a>
      <button class="menu-button" type="button" aria-label="Mở menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <nav class="main-nav" aria-label="Menu chính">
        {nav_links}
      </nav>
      <div class="language-switcher" aria-label="Language switcher">
        {render_language_switcher(active_page, language)}
      </div>
      <a class="header-cta" href="{header_cta_href}">{header_cta_label}</a>
    </header>
    """


def render_footer():
    """Footer dùng chung cho các trang động."""
    settings = get_system_settings()
    social_links = "".join(
        f'<a class="text-link" href="{h(url)}" target="_blank" rel="noreferrer">{h(label)}</a> '
        for label, url in [
            ("Facebook", settings.get("facebook_url")),
            ("LinkedIn", settings.get("linkedin_url")),
            ("YouTube", settings.get("youtube_url")),
        ]
        if url
    )
    return f"""
    <footer class="site-footer">
      <div class="container footer-grid">
        <div>
          <a class="brand footer-brand" href="/">
            <span class="brand-mark">M</span>
            <span>{h(settings["company_name"])}</span>
          </a>
          <p>Gia công cơ khí chính xác và giải pháp sản xuất cho doanh nghiệp công nghiệp.</p>
          <p>{social_links}</p>
        </div>
        <div>
          <h3>Liên hệ</h3>
          <p>Email: {h(settings["contact_email"])}</p>
          <p>Hotline: {h(settings["hotline"])}</p>
        </div>
        <div>
          <h3>Địa chỉ</h3>
          <p>{h(settings["address"])}</p>
        </div>
      </div>
      <p class="copyright">© 2026 {h(settings["company_name"])}. Dynamic website powered by SQLite.</p>
    </footer>
    """


def render_base(title, description, active_page, body, language="vi"):
    """Khung HTML chung. Nội dung từng trang được truyền vào biến body."""
    # Mọi trang đều dùng chung header, footer, CSS và JS.
    # Phần khác nhau của từng trang nằm trong biến body.
    language = normalize_language(language)
    settings = get_system_settings()
    favicon_html = f'<link rel="icon" href="{h(settings["favicon_url"])}" />' if settings.get("favicon_url") else ""
    analytics_html = ""
    if settings.get("google_analytics_id"):
        analytics_id = h(settings["google_analytics_id"])
        analytics_html = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={analytics_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{analytics_id}');
    </script>
        """
    html_output = f"""<!doctype html>
<html lang="{h(get_language_meta(language)["html_lang"])}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{h(title)}</title>
    <meta name="description" content="{h(description)}" />
    {favicon_html}
    <link rel="stylesheet" href="/css/styles.css" />
    {analytics_html}
  </head>
  <body>
    {render_header(active_page, language)}
    <main>
      {body}
    </main>
    {render_footer()}
    <script src="/js/app.js"></script>
  </body>
</html>"""
    return translate_public_html(html_output, language)


def render_api_docs_page():
    """Trang tài liệu API đơn giản đọc từ OpenAPI schema."""
    # Bản JSON chuẩn nằm ở /api/openapi.json.
    # Trang HTML này giúp xem nhanh endpoint mà không cần cài thêm thư viện.
    schema = get_openapi_schema()
    rows = []
    for path, methods in schema["paths"].items():
        for method, detail in methods.items():
            rows.append(
                f"""
                <tr>
                  <td><strong>{method.upper()}</strong></td>
                  <td><code>{h(path)}</code></td>
                  <td>{h(detail.get("summary", ""))}</td>
                </tr>
                """
            )
    body = f"""
      <section class="page-hero">
        <div class="container">
          <p class="eyebrow">OpenAPI</p>
          <h1>Tài liệu API</h1>
          <p>Danh sách endpoint quan trọng cho frontend hoặc đối tác tích hợp.</p>
          <a class="btn btn-primary" href="/api/openapi.json">Xem OpenAPI JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="container">
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead><tr><th>Method</th><th>Endpoint</th><th>Chức năng</th></tr></thead>
              <tbody>{''.join(rows)}</tbody>
            </table>
          </div>
        </div>
      </section>
    """
    return render_base("Tài liệu API", "OpenAPI documentation", "api-aws", body)


def product_cards(products):
    """Tạo HTML card sản phẩm từ dữ liệu database."""
    # Hàm này biến mỗi dòng dữ liệu sản phẩm thành một khối HTML <article>.
    return "\n".join(
        f"""
        <article class="product-card">
          <img src="{h(product["image"])}" alt="{h(product["name"])}" loading="lazy" />
          <div>
            <span class="tag">{h(product["category"])}</span>
            <h3>{h(product["name"])}</h3>
            <p>{h(product["description"])}</p>
          </div>
        </article>
        """
        for product in products
    )


def capability_cards(capabilities):
    """Tạo HTML card năng lực sản xuất từ dữ liệu database."""
    # enumerate(..., start=1) tạo số thứ tự nếu item không có icon.
    return "\n".join(
        f"""
        <article class="capability-card">
          <span>{h(item.get("icon") or str(index).zfill(2))}</span>
          <h3>{h(item["title"])}</h3>
          <p>{h(item["text"])}</p>
        </article>
        """
        for index, item in enumerate(capabilities, start=1)
    )


def news_cards(news_items):
    """Tạo HTML card tin tức từ dữ liệu database."""
    return "\n".join(
        f"""
        <article class="news-card">
          <img src="{h(item["image"])}" alt="{h(item["title"])}" loading="lazy" />
          <div>
            <span class="tag">{h(item["category"])}</span>
            <h3>{h(item["title"])}</h3>
            <p>{h(item["description"])}</p>
          </div>
        </article>
        """
        for item in news_items
    )


def banner_cards(banners, card_class="banner-card"):
    """Tạo HTML banner từ CMS Banner."""
    return "\n".join(
        f"""
        <article class="{card_class}">
          {f'<img src="{h(item["image_url"])}" alt="{h(item["title"])}" loading="lazy" />' if item.get("image_url") else ""}
          <div>
            <h3>{h(item["title"])}</h3>
            <p>{h(item.get("content", ""))}</p>
            {f'<a class="text-link" href="{h(item["link_url"])}">Xem thêm</a>' if item.get("link_url") else ""}
          </div>
        </article>
        """
        for item in banners
    )


def render_home_banner_sections():
    """Render slider và advertisement trên trang chủ từ bảng cms_banners."""
    sliders = get_active_banners("home_slider")
    advertisements = get_active_banners("advertisement")
    slider_html = ""
    advertisement_html = ""
    if sliders:
        slider_html = f"""
          <section class="section cms-banner-section">
            <div class="container">
              <div class="section-heading">
                <div>
                  <p class="eyebrow">Banner CMS</p>
                  <h2>Slider trang chủ</h2>
                </div>
              </div>
              <div class="cms-banner-grid">{banner_cards(sliders)}</div>
            </div>
          </section>
        """
    if advertisements:
        advertisement_html = f"""
          <section class="section cms-ad-section">
            <div class="container cms-ad-grid">{banner_cards(advertisements, "banner-card ad-card")}</div>
          </section>
        """
    return slider_html + advertisement_html


def render_home_page(language="vi"):
    """Render trang chủ động từ database."""
    # Đây là trang động: dữ liệu được lấy từ SQLite rồi chèn vào HTML trước khi trả cho trình duyệt.
    data = get_home_data()
    body = f"""
      <section class="hero">
        <div class="hero-bg" aria-hidden="true"></div>
        <div class="hero-overlay" aria-hidden="true"></div>
        <div class="container hero-content">
          <p class="eyebrow">Sản xuất cơ khí chính xác</p>
          <h1>Giải pháp cơ khí chính xác hàng đầu</h1>
          <p class="hero-text">
            Cung cấp linh kiện gia công CNC, cụm chi tiết chính xác và dịch vụ kỹ thuật cho
            các doanh nghiệp sản xuất tại Việt Nam.
          </p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="/san-pham.html">Xem sản phẩm</a>
            <a class="btn btn-ghost" href="/cong-nghe.html">Năng lực sản xuất</a>
          </div>
        </div>
        <div class="hero-stats" aria-label="Thông số nổi bật">
          <div><strong>ISO</strong><span>Quy trình kiểm soát</span></div>
          <div><strong>24h</strong><span>Phản hồi kỹ thuật</span></div>
          <div><strong>0.01</strong><span>Dung sai mm</span></div>
          <div><strong>{len(data["products"])}+</strong><span>Nhóm sản phẩm</span></div>
        </div>
      </section>

      {render_home_banner_sections()}

      <section class="section about-section">
        <div class="container split-layout">
          <div class="image-stack">
            <img class="about-image" src="https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=900&q=80" alt="Kỹ sư kiểm tra chi tiết cơ khí trong nhà máy" />
            <div class="floating-note">
              <strong>Chính xác - ổn định</strong>
              <span>Gia công theo bản vẽ và tiêu chuẩn riêng của từng khách hàng.</span>
            </div>
          </div>
          <div class="section-copy">
            <p class="eyebrow">Về MecPrecision Việt Nam</p>
            <h2>Đối tác sản xuất đáng tin cậy cho doanh nghiệp công nghiệp</h2>
            <p>Chúng tôi tập trung vào linh kiện cơ khí chính xác, quản lý chất lượng từng công đoạn và hỗ trợ kỹ thuật từ khi nhận bản vẽ đến khi giao hàng.</p>
            <ul class="check-list">
              <li>Gia công CNC, tiện, phay, mài và xử lý bề mặt.</li>
              <li>Đọc bản vẽ kỹ thuật, tư vấn vật liệu và tối ưu quy trình.</li>
              <li>Kiểm tra kích thước, đóng gói và truy xuất thông tin đơn hàng.</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="section products-section">
        <div class="container">
          <div class="section-heading">
            <div>
              <p class="eyebrow">Sản phẩm từ database</p>
              <h2>Linh kiện cơ khí chính xác</h2>
            </div>
            <a class="text-link" href="/san-pham.html">Xem trang sản phẩm</a>
          </div>
          <div class="product-grid" id="productGrid">{product_cards(data["products"])}</div>
        </div>
      </section>

      <section class="section technology-section">
        <div class="container">
          <div class="dark-panel">
            <div>
              <p class="eyebrow light">Công nghệ & năng lực sản xuất</p>
              <h2>Năng lực được render trực tiếp từ SQLite</h2>
              <p>Backend đọc bảng capabilities rồi tạo HTML động cho khu vực này.</p>
              <a class="btn btn-ghost" href="/cong-nghe.html">Tìm hiểu công nghệ</a>
            </div>
            <div class="capability-grid" id="capabilityGrid">{capability_cards(data["capabilities"])}</div>
          </div>
        </div>
      </section>

      <section class="section news-section">
        <div class="container">
          <div class="section-heading">
            <div>
              <p class="eyebrow">Tin tức mới nhất</p>
              <h2>Cập nhật từ nhà máy</h2>
            </div>
            <a class="text-link" href="/tin-tuc.html">Xem tất cả</a>
          </div>
          <div class="news-grid" id="newsGrid">{news_cards(data["news"])}</div>
        </div>
      </section>

      <section class="section contact-section">
        <div class="container contact-panel">
          <div>
            <p class="eyebrow light">Bạn cần gia công chi tiết?</p>
            <h2>Sẵn sàng cho dự án tiếp theo của bạn?</h2>
            <p>Gửi thông tin bản vẽ hoặc yêu cầu kỹ thuật để chúng tôi tư vấn phương án phù hợp.</p>
          </div>
          <a class="btn btn-primary" href="/lien-he.html">Đi đến trang liên hệ</a>
        </div>
      </section>
    """
    return render_base("Trang chủ - MecPrecision VIETNAM", "Trang chủ động đọc dữ liệu từ SQLite.", "index", body, language)


def render_dynamic_cms_page(page, language="vi"):
    """Render trang động được tạo trong CMS Pages."""
    # Nội dung người dùng nhập được escape để tránh HTML lạ gây lỗi giao diện hoặc script nguy hiểm.
    content_html = h(page.get("content", "")).replace("\n", "<br>")
    body = f"""
      <section class="page-hero">
        <div class="container">
          <p class="eyebrow">Trang động</p>
          <h1>{h(page["title"])}</h1>
          <p>{h(page.get("seo_description", ""))}</p>
        </div>
      </section>
      <section class="section">
        <div class="container dynamic-page-content">
          <div class="prose-content">{content_html}</div>
        </div>
      </section>
    """
    return render_base(page.get("seo_title") or page["title"], page.get("seo_description", ""), "page", body, language)



def render_products_page(language="vi"):
    """Render trang sản phẩm động."""
    products = get_products()
    body = f"""
      <section class="page-hero">
        <div class="container">
          <p class="eyebrow">Danh mục sản phẩm</p>
          <h1>Sản phẩm cơ khí chính xác</h1>
          <p>Trang này được backend render từ bảng products, product_categories và view product_overview.</p>
        </div>
      </section>
      <section class="section products-section">
        <div class="container">
          <div class="product-grid" id="productGrid">{product_cards(products)}</div>
        </div>
      </section>
    """
    return render_base("Sản phẩm - MecPrecision VIETNAM", "Danh sách sản phẩm động từ SQLite.", "products", body, language)


def render_technology_page(language="vi"):
    """Render trang công nghệ động."""
    capabilities = get_capabilities()
    body = f"""
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">Công nghệ sản xuất</p>
          <h1>Năng lực sản xuất & kiểm soát chất lượng</h1>
          <p>Dữ liệu năng lực bên dưới được đọc từ bảng capabilities.</p>
        </div>
      </section>
      <section class="section technology-section">
        <div class="container">
          <div class="dark-panel">
            <div>
              <p class="eyebrow light">Năng lực chính</p>
              <h2>Công nghệ đáp ứng yêu cầu khắt khe</h2>
              <p>Hệ thống máy móc, quy trình vận hành và kiểm tra giúp duy trì độ ổn định.</p>
            </div>
            <div class="capability-grid" id="capabilityGrid">{capability_cards(capabilities)}</div>
          </div>
        </div>
      </section>
    """
    return render_base("Công nghệ - MecPrecision VIETNAM", "Năng lực sản xuất động từ SQLite.", "technology", body, language)


def render_news_page(language="vi"):
    """Render trang tin tức động."""
    news_items = get_news()
    body = f"""
      <section class="page-hero">
        <div class="container">
          <p class="eyebrow">Tin tức</p>
          <h1>Cập nhật từ nhà máy</h1>
          <p>Các bài viết được backend đọc từ bảng news và news_categories.</p>
        </div>
      </section>
      <section class="section news-section">
        <div class="container">
          <div class="news-grid" id="newsGrid">{news_cards(news_items)}</div>
        </div>
      </section>
    """
    return render_base("Tin tức - MecPrecision VIETNAM", "Tin tức động từ SQLite.", "news", body, language)


def render_contact_page(language="vi"):
    """Render trang liên hệ. Form gửi về API để lưu vào SQLite."""
    body = """
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">Liên hệ</p>
          <h1>Gửi yêu cầu tư vấn hoặc báo giá</h1>
          <p>Form này gửi dữ liệu tới /api/contact và lưu vào bảng contact_requests.</p>
        </div>
      </section>
      <section class="section contact-section">
        <div class="container contact-panel">
          <div>
            <p class="eyebrow light">Bạn cần gia công chi tiết?</p>
            <h2>Sẵn sàng cho dự án tiếp theo của bạn?</h2>
            <p>Gửi thông tin bản vẽ hoặc yêu cầu kỹ thuật. Chúng tôi sẽ phản hồi phương án phù hợp.</p>
            <div class="contact-list">
              <p><strong>Email:</strong> sales@mecprecision.vn</p>
              <p><strong>Hotline:</strong> 0900 000 000</p>
              <p><strong>Địa chỉ:</strong> Khu công nghiệp, TP. Hồ Chí Minh, Việt Nam</p>
            </div>
          </div>
          <form class="contact-form" id="contactForm">
            <label>Họ tên<input type="text" name="name" placeholder="Nguyễn Văn A" required /></label>
            <label>Công ty<input type="text" name="company" placeholder="Công ty ABC" /></label>
            <label>Điện thoại<input type="tel" name="phone" placeholder="0900 000 000" /></label>
            <label>Email<input type="email" name="email" placeholder="email@congty.com" /></label>
            <label>Quốc gia<input type="text" name="country" placeholder="Vietnam" /></label>
            <label>Sản phẩm quan tâm<input type="text" name="interested_product" placeholder="Trục CNC, bánh răng..." /></label>
            <label>File đính kèm<input type="file" name="attachment_file" /></label>
            <label>Nội dung cần tư vấn<textarea name="message" rows="4" placeholder="Mô tả chi tiết, vật liệu, số lượng..."></textarea></label>
            <label>Captcha: 3 + 4 = ?<input type="text" name="captcha_answer" required /></label>
            <button class="btn btn-primary" type="submit">Gửi yêu cầu</button>
            <p class="form-message" id="formMessage" role="status"></p>
          </form>
        </div>
      </section>
    """
    return render_base("Liên hệ - MecPrecision VIETNAM", "Form liên hệ lưu vào SQLite.", "contact", body, language)


def get_api_aws_demo_data():
    """Tạo dữ liệu demo để frontend gọi API và hiểu cách web có thể đưa lên AWS."""
    # Hàm này không gọi AWS thật. Nó trả về mô hình triển khai để bạn học luồng API + AWS.
    stats = get_dashboard_stats()
    return {
        "api_demo": {
            "message": "Frontend đã gọi API /api/aws-demo thành công.",
            "source": "Dữ liệu này được tạo trong backend/app.py rồi trả về dạng JSON.",
            "database_stats": stats,
        },
        "aws_architecture": [
            {
                "service": "Amazon Route 53",
                "purpose": "Quản lý tên miền, ví dụ mecprecision.vn.",
            },
            {
                "service": "Amazon CloudFront",
                "purpose": "Tăng tốc tải web và cache file tĩnh như CSS, JS, ảnh.",
            },
            {
                "service": "Amazon EC2 hoặc AWS Elastic Beanstalk",
                "purpose": "Chạy backend Python app.py để xử lý route, API và login.",
            },
            {
                "service": "Amazon RDS",
                "purpose": "Thay SQLite bằng database server như PostgreSQL hoặc MySQL khi web lớn hơn.",
            },
            {
                "service": "Amazon S3",
                "purpose": "Lưu ảnh sản phẩm, bản vẽ, file báo giá hoặc tài liệu upload.",
            },
        ],
        "request_flow": [
            "Người dùng mở trình duyệt.",
            "Domain đi qua Route 53.",
            "CloudFront trả file tĩnh hoặc chuyển request về backend.",
            "Backend Python xử lý API.",
            "Backend đọc/ghi database.",
            "Kết quả trả về trình duyệt dạng HTML hoặc JSON.",
        ],
    }


def get_external_weather_data():
    """Gọi API bên ngoài Open-Meteo rồi chuẩn hóa dữ liệu trả về cho frontend."""
    # Đây là API ngoại thật, không phải dữ liệu tự tạo trong database.
    # Open-Meteo không cần API key nên phù hợp để demo local.
    external_url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=10.8231"
        "&longitude=106.6297"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        "&timezone=Asia%2FBangkok"
    )

    try:
        request = urllib.request.Request(
            external_url,
            headers={"User-Agent": "MecPrecisionLocalDemo/1.0"},
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            raw_body = response.read().decode("utf-8")
            external_data = json.loads(raw_body)

        current = external_data.get("current", {})
        return {
            "status": "success",
            "external_api": "Open-Meteo Forecast API",
            "external_url": external_url,
            "location": "TP. Hồ Chí Minh",
            "data": {
                "temperature_c": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "time": current.get("time"),
            },
            "explanation": "Backend local đã gọi API bên ngoài, sau đó trả JSON này về frontend.",
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        # Khi máy không có mạng hoặc API ngoài lỗi, backend vẫn trả JSON để frontend không bị hỏng.
        return {
            "status": "external_api_unavailable",
            "external_api": "Open-Meteo Forecast API",
            "external_url": external_url,
            "message": "Backend đã thử gọi API bên ngoài nhưng chưa nhận được dữ liệu.",
            "error": str(error),
            "fallback_data": {
                "location": "TP. Hồ Chí Minh",
                "note": "Dữ liệu dự phòng để giao diện vẫn hiển thị được khi mất mạng.",
            },
        }


def render_api_aws_demo_page(language="vi"):
    """Render trang demo cho chức năng API và mô hình triển khai AWS."""
    body = """
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">API & AWS demo</p>
          <h1>Demo web động gọi API và mô hình triển khai AWS</h1>
          <p>Trang này giúp bạn thấy frontend gọi API từ backend, sau đó hiểu web có thể triển khai lên AWS như thế nào.</p>
        </div>
      </section>

      <section class="section products-section">
        <div class="container api-demo-layout">
          <div class="api-demo-panel">
            <p class="eyebrow">Bước 1: Frontend gọi API</p>
            <h2>Gọi thử API từ trình duyệt</h2>
            <p>Khi bấm nút bên dưới, file frontend/js/app.js sẽ gọi endpoint /api/aws-demo trong backend/app.py.</p>
            <button class="btn btn-primary" type="button" id="apiAwsDemoButton">Gọi API demo</button>
          </div>
          <div class="api-demo-panel">
            <p class="eyebrow">Kết quả JSON</p>
            <pre class="api-output" id="apiAwsDemoOutput">Chưa gọi API.</pre>
          </div>
        </div>
      </section>

      <section class="section products-section">
        <div class="container api-demo-layout">
          <div class="api-demo-panel">
            <p class="eyebrow">Bước 1.5: API liên kết ngoại</p>
            <h2>Backend gọi API thời tiết bên ngoài</h2>
            <p>Nút này gọi backend local /api/external/weather. Sau đó backend mới gọi Open-Meteo ở internet và trả dữ liệu về web.</p>
            <button class="btn btn-primary" type="button" id="externalApiDemoButton">Gọi API ngoại</button>
          </div>
          <div class="api-demo-panel">
            <p class="eyebrow">Kết quả từ API ngoại</p>
            <pre class="api-output" id="externalApiDemoOutput">Chưa gọi API ngoại.</pre>
          </div>
        </div>
      </section>

      <section class="section technology-section">
        <div class="container">
          <div class="dark-panel aws-flow-panel">
            <div>
              <p class="eyebrow light">Bước 2: Khi đưa lên AWS</p>
              <h2>Luồng chạy đề xuất</h2>
              <p>Ở bản local, backend chạy trên máy bạn. Khi triển khai thật, backend có thể chạy trên EC2 hoặc Elastic Beanstalk, database chuyển sang RDS, ảnh/file chuyển sang S3.</p>
            </div>
            <div class="aws-flow-list">
              <article><span>01</span><strong>Route 53</strong><p>Tên miền trỏ vào hệ thống AWS.</p></article>
              <article><span>02</span><strong>CloudFront</strong><p>Tăng tốc và cache nội dung tĩnh.</p></article>
              <article><span>03</span><strong>EC2 / Beanstalk</strong><p>Chạy backend Python và API.</p></article>
              <article><span>04</span><strong>RDS</strong><p>Database production thay cho SQLite.</p></article>
              <article><span>05</span><strong>S3</strong><p>Lưu ảnh, file upload và tài liệu.</p></article>
            </div>
          </div>
        </div>
      </section>
    """
    return render_base("API & AWS demo - MecPrecision", "Demo API và mô hình triển khai AWS.", "api-aws", body, language)


def render_admin_login_page(error_message=""):
    """Render trang đăng nhập quản trị."""
    # error_message chỉ hiện khi người dùng nhập sai email hoặc mật khẩu.
    settings = get_system_settings()
    captcha = make_captcha_challenge() if settings.get("captcha_enabled") == "1" else None
    error_html = f'<p class="form-message error-message">{h(error_message)}</p>' if error_message else ""
    captcha_html = ""
    if captcha:
        captcha_html = f"""
            <input type="hidden" name="captcha_token" value="{h(captcha["token"])}" />
            <label>Captcha: {h(captcha["question"])}<input name="captcha_answer" required /></label>
        """
    body = f"""
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">Admin</p>
          <h1>Đăng nhập quản trị</h1>
          <p>Khu vực này dùng để quản lý dữ liệu website trong các bước nâng cấp tiếp theo.</p>
        </div>
      </section>
      <section class="section contact-section">
        <div class="container contact-panel admin-login-panel">
          <div>
            <p class="eyebrow light">Tài khoản demo</p>
            <h2>Quản trị MecPrecision</h2>
            <p>Email: admin@mecprecision.vn</p>
            <p>Mật khẩu: admin123</p>
          </div>
          <form class="contact-form" method="post" action="/admin/login">
            <label>Email<input type="email" name="email" placeholder="admin@mecprecision.vn" required /></label>
            <label>Mật khẩu<input type="password" name="password" placeholder="Nhập mật khẩu" required /></label>
            {captcha_html}
            <label class="checkbox-row"><input type="checkbox" name="remember_login" value="1" /> Ghi nhớ đăng nhập 30 ngày</label>
            <button class="btn btn-primary" type="submit">Đăng nhập</button>
            <a class="text-link" href="/admin/forgot-password">Quên mật khẩu?</a>
            {error_html}
          </form>
        </div>
      </section>
    """
    return render_base("Đăng nhập quản trị - MecPrecision", "Trang đăng nhập quản trị.", "admin", body)


def render_two_factor_page(challenge_id, error_message=""):
    """Render bước nhập mã 2FA sau khi login đúng mật khẩu."""
    error_html = f'<p class="form-message error-message">{h(error_message)}</p>' if error_message else ""
    body = f"""
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">2FA</p>
          <h1>Xác thực hai lớp</h1>
          <p>Mã 2FA demo đã được lưu trong Email outbox local.</p>
        </div>
      </section>
      <section class="section contact-section">
        <div class="container contact-panel admin-login-panel">
          <div>
            <p class="eyebrow light">Security</p>
            <h2>Nhập mã 6 số</h2>
            <p>Vào trang tài khoản sau khi đăng nhập để xem email outbox demo.</p>
          </div>
          <form class="contact-form" method="post" action="/admin/2fa">
            <input type="hidden" name="challenge_id" value="{h(challenge_id)}" />
            <label>Mã 2FA<input name="code" inputmode="numeric" required /></label>
            <button class="btn btn-primary" type="submit">Xác nhận</button>
            {error_html}
          </form>
        </div>
      </section>
      <section class="section">
        <div class="container contact-panel">
          <div>
            <p class="eyebrow light">Quote Request</p>
            <h2>Gửi yêu cầu báo giá kỹ thuật</h2>
            <p>Form này tạo customer, quote request, quote item và file tham chiếu để CMS xử lý theo workflow.</p>
          </div>
          <form class="contact-form" id="quoteForm">
            <label>Họ tên<input type="text" name="name" required /></label>
            <label>Công ty<input type="text" name="company" /></label>
            <label>Email<input type="email" name="email" /></label>
            <label>Điện thoại<input type="tel" name="phone" /></label>
            <label>Sản phẩm<input type="text" name="product" placeholder="Tên chi tiết / mã bản vẽ" required /></label>
            <label>Số lượng<input type="number" name="quantity" min="1" value="1" /></label>
            <label>Dung sai<input type="text" name="tolerance" placeholder="±0.01mm" /></label>
            <label>Bản vẽ PDF<input type="text" name="drawing_pdf" placeholder="URL hoặc tên file PDF" /></label>
            <label>STEP<input type="text" name="step_file" placeholder="URL hoặc tên file STEP" /></label>
            <label>DWG<input type="text" name="dwg_file" placeholder="URL hoặc tên file DWG" /></label>
            <label>Deadline<input type="date" name="deadline" /></label>
            <label>Ghi chú<textarea name="note" rows="4"></textarea></label>
            <button class="btn btn-primary" type="submit">Gửi yêu cầu báo giá</button>
            <p class="form-message" id="quoteMessage" role="status"></p>
          </form>
        </div>
      </section>
    """
    return render_base("Xác thực 2FA - MecPrecision", "Nhập mã xác thực hai lớp.", "admin", body)


def render_forgot_password_page(message="", error="", reset_link=""):
    """Render trang quên mật khẩu."""
    # Ở bản demo local chưa gửi email thật.
    # Link reset sẽ được lưu vào bảng auth_email_outbox và hiển thị luôn để bạn dễ test.
    message_html = render_admin_message(message, error)
    link_html = f'<p><a class="text-link" href="{h(reset_link)}">Mở link reset demo</a></p>' if reset_link else ""
    body = f"""
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">Authentication</p>
          <h1>Quên mật khẩu</h1>
          <p>Nhập email tài khoản quản trị để tạo link reset mật khẩu.</p>
        </div>
      </section>
      <section class="section contact-section">
        <div class="container contact-panel admin-login-panel">
          <div>
            <p class="eyebrow light">Reset bằng email</p>
            <h2>Email outbox local</h2>
            <p>Bản demo lưu email vào database thay vì gửi email thật.</p>
            {link_html}
          </div>
          <form class="contact-form" method="post" action="/admin/forgot-password">
            <label>Email<input type="email" name="email" placeholder="admin@mecprecision.vn" required /></label>
            <button class="btn btn-primary" type="submit">Gửi link reset</button>
            <a class="text-link" href="/admin/login">Quay lại đăng nhập</a>
            {message_html}
          </form>
        </div>
      </section>
    """
    return render_base("Quên mật khẩu - MecPrecision", "Tạo link reset mật khẩu.", "admin", body)


def render_reset_password_page(token="", message="", error=""):
    """Render trang đặt lại mật khẩu bằng token."""
    message_html = render_admin_message(message, error)
    body = f"""
      <section class="page-hero page-hero-dark">
        <div class="container">
          <p class="eyebrow light">Authentication</p>
          <h1>Đặt lại mật khẩu</h1>
          <p>Nhập mật khẩu mới cho tài khoản của bạn.</p>
        </div>
      </section>
      <section class="section contact-section">
        <div class="container contact-panel admin-login-panel">
          <div>
            <p class="eyebrow light">Reset token</p>
            <h2>Bảo mật token</h2>
            <p>Token chỉ dùng một lần và có thời hạn 30 phút.</p>
          </div>
          <form class="contact-form" method="post" action="/admin/reset-password">
            <input type="hidden" name="token" value="{h(token)}" />
            <label>Mật khẩu mới<input type="password" name="password" required /></label>
            <button class="btn btn-primary" type="submit">Đặt lại mật khẩu</button>
            <a class="text-link" href="/admin/login">Quay lại đăng nhập</a>
            {message_html}
          </form>
        </div>
      </section>
    """
    return render_base("Đặt lại mật khẩu - MecPrecision", "Reset password bằng email.", "admin", body)



def render_admin_nav(active_module):
    """Menu riêng cho khu vực Admin CMS."""
    modules = [
        ("dashboard", "Dashboard", "/admin"),
        ("products", "Sản phẩm", "/admin/products"),
        ("categories", "Danh mục", "/admin/categories"),
        ("news", "Tin tức", "/admin/news"),
        ("media", "Media", "/admin/media"),
        ("pages", "Pages", "/admin/pages"),
        ("menus", "Menu", "/admin/menus"),
        ("banners", "Banner", "/admin/banners"),
        ("contacts", "Liên hệ", "/admin/contacts"),
        ("quotes", "Báo giá", "/admin/quotes"),
        ("customers", "Khách hàng", "/admin/customers"),
        ("newsletter", "Newsletter", "/admin/newsletter"),
        ("users", "Người dùng", "/admin/users"),
        ("settings", "Cài đặt", "/admin/settings"),
        ("ai", "AI", "/admin/ai"),
        ("developer", "Developer", "/admin/developer"),
        ("account", "Tài khoản", "/admin/account"),
    ]
    return "\n".join(
        f'<a class="{"active" if key == active_module else ""}" href="{href}">{label}</a>'
        for key, label, href in modules
    )


def render_admin_shell(title, active_module, admin_user, content):
    """Bọc nội dung module trong khung Admin CMS dùng chung."""
    # CSRF token được chèn tự động vào form trong Admin để chống request giả mạo.
    content = inject_csrf_token(content, admin_user.get("session_id", ""))
    body = f"""
      <section class="page-hero">
        <div class="container">
          <p class="eyebrow">Admin CMS</p>
          <h1>{h(title)}</h1>
          <p>Xin chào, {h(admin_user["full_name"])}. Khu vực này dùng để quản trị dữ liệu website.</p>
          <a class="text-link" href="/admin/account">Tài khoản của tôi</a>
          <a class="text-link" href="/admin/logout">Đăng xuất</a>
        </div>
      </section>
      <section class="section admin-cms-section">
        <div class="container admin-cms-layout">
          <aside class="admin-sidebar">
            {render_admin_nav(active_module)}
          </aside>
          <div class="admin-content">
            {content}
          </div>
        </div>
      </section>
    """
    return render_base(f"{title} - Admin CMS", "Khu vực quản trị website.", "admin", body)


def render_admin_message(message="", error=""):
    """Hiển thị thông báo thành công hoặc lỗi trong CMS."""
    if error:
        return f'<p class="admin-alert admin-alert-error">{h(error)}</p>'
    if message:
        return f'<p class="admin-alert admin-alert-success">{h(message)}</p>'
    return ""


def render_admin_search(action, q):
    """Form tìm kiếm chung cho các module."""
    return f"""
      <form class="admin-toolbar" method="get" action="{h(action)}">
        <input type="search" name="q" value="{h(q)}" placeholder="Tìm kiếm..." />
        <button class="btn btn-primary" type="submit">Tìm</button>
      </form>
    """


def render_pagination(base_path, page, per_page, total, q="", extra_params=None):
    """Tạo link phân trang cho bảng CMS."""
    extra_params = extra_params or {}
    total_pages = max(1, (total + per_page - 1) // per_page)
    if total_pages <= 1:
        return ""

    links = []
    for number in range(1, total_pages + 1):
        query = build_query_string({**extra_params, "q": q, "page": number})
        links.append(
            f'<a class="{"active" if number == page else ""}" href="{base_path}?{query}">{number}</a>'
        )
    return f'<nav class="admin-pagination">{"".join(links)}</nav>'


def format_timestamp(timestamp_value):
    """Đổi timestamp giây sang chuỗi ngày giờ dễ đọc."""
    if not timestamp_value:
        return ""
    return datetime.fromtimestamp(int(timestamp_value)).strftime("%Y-%m-%d %H:%M:%S")


def render_category_options(selected_id=None):
    """Tạo option danh mục sản phẩm cho form sản phẩm."""
    return "\n".join(
        f'<option value="{item["id"]}" {"selected" if selected_id == item["id"] else ""}>{h(item["name"])}</option>'
        for item in get_product_categories()
    )


def render_news_category_options(selected_id=None):
    """Tạo option danh mục tin tức cho form tin tức."""
    return "\n".join(
        f'<option value="{item["id"]}" {"selected" if selected_id == item["id"] else ""}>{h(item["name"])}</option>'
        for item in get_news_categories()
    )


def render_admin_products_page(admin_user, params, form_product=None, message="", error=""):
    """Render module quản lý sản phẩm."""
    q = str(params.get("q", "")).strip()
    page = parse_positive_int(params.get("page"), 1)
    per_page = parse_positive_int(params.get("per_page"), 20)
    category_filter = parse_positive_int(params.get("category_id"), 0)
    status_filter = str(params.get("status", "")).strip()
    sort_filter = str(params.get("sort", "newest")).strip()
    products, total = get_paginated_products(q, page, per_page, category_filter, status_filter, sort_filter)
    form_product = form_product or {}
    product_id = form_product.get("id", "")
    image_value = form_product.get("main_image") or form_product.get("image") or ""
    filter_extra = {
        "category_id": category_filter or "",
        "status": status_filter,
        "sort": sort_filter,
        "per_page": per_page,
    }
    category_filter_options = '<option value="">Tất cả danh mục</option>' + render_category_options(category_filter)
    product_filter_html = f"""
      <form class="admin-filter-panel" method="get" action="/admin/products">
        <label>Tìm kiếm<input type="search" name="q" value="{h(q)}" placeholder="Tên, mã sản phẩm, mô tả..." /></label>
        <label>Danh mục<select name="category_id">{category_filter_options}</select></label>
        <label>Trạng thái<select name="status">
          <option value="" {"selected" if not status_filter else ""}>Tất cả</option>
          <option value="draft" {"selected" if status_filter == "draft" else ""}>Draft</option>
          <option value="published" {"selected" if status_filter == "published" else ""}>Published</option>
          <option value="archived" {"selected" if status_filter == "archived" else ""}>Archived</option>
        </select></label>
        <label>Sắp xếp<select name="sort">
          <option value="newest" {"selected" if sort_filter == "newest" else ""}>Mới nhất</option>
          <option value="oldest" {"selected" if sort_filter == "oldest" else ""}>Cũ nhất</option>
          <option value="name" {"selected" if sort_filter == "name" else ""}>Tên A-Z</option>
          <option value="price_desc" {"selected" if sort_filter == "price_desc" else ""}>Giá cao đến thấp</option>
          <option value="price_asc" {"selected" if sort_filter == "price_asc" else ""}>Giá thấp đến cao</option>
          <option value="sort_order" {"selected" if sort_filter == "sort_order" else ""}>Sort order</option>
        </select></label>
        <label>Số sản phẩm/trang<input type="number" name="per_page" min="5" max="100" value="{h(per_page)}" /></label>
        <button class="btn btn-primary" type="submit">Tìm</button>
      </form>
    """

    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><img class="admin-thumb" src="{h(item.get("thumbnail_url") or item["main_image"])}" alt="{h(item["name"])}" /></td>
          <td><strong>{h(item["name"])}</strong><br><span>{h(item.get("sku", ""))} · {h(item["category"])}</span></td>
          <td>{h(item["short_description"])}</td>
          <td>{h(item.get("price", 0))}</td>
          <td>{h(item.get("status", ""))}</td>
          <td>{h(item.get("sort_order", 0))}</td>
          <td>
            <a class="text-link" href="/admin/products/{item["id"]}/edit">Sửa</a>
            <form class="inline-delete-form" method="post" action="/admin/products/{item["id"]}/delete" data-confirm-delete>
              <button type="submit">Xóa</button>
            </form>
          </td>
        </tr>
        """
        for item in products
    ) or '<tr><td colspan="8">Không có sản phẩm.</td></tr>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" enctype="multipart/form-data" action="/admin/products/save">
          <input type="hidden" name="id" value="{h(product_id)}" />
          <h2>{'Sửa sản phẩm' if product_id else 'Thêm sản phẩm'}</h2>
          <label>Danh mục<select name="category_id" required>{render_category_options(form_product.get("category_id"))}</select></label>
          <label>Tên sản phẩm<input name="name" value="{h(form_product.get("name", ""))}" required /></label>
          <label>Slug<input name="slug" value="{h(form_product.get("slug", ""))}" placeholder="Tự tạo nếu để trống" /></label>
          <label>Mã sản phẩm / SKU<input name="sku" value="{h(form_product.get("sku", ""))}" /></label>
          <label>Giá<input type="number" step="0.01" name="price" value="{h(form_product.get("price", 0))}" /></label>
          <label>Mô tả ngắn<textarea name="short_description" rows="3" required>{h(form_product.get("short_description", ""))}</textarea></label>
          <label>Mô tả chi tiết<textarea name="description" rows="4" required>{h(form_product.get("description", ""))}</textarea></label>
          <label>Ảnh hiện tại / URL ảnh<input name="main_image" value="{h(image_value)}" data-image-preview-input /></label>
          <label>Thumbnail<input name="thumbnail_url" value="{h(form_product.get("thumbnail_url", ""))}" placeholder="Có thể để trống để dùng ảnh chính" /></label>
          <label>Gallery URLs<textarea name="gallery_urls" rows="3" placeholder="Mỗi dòng một URL ảnh">{h(form_product.get("gallery_urls", ""))}</textarea></label>
          <label>Tài liệu PDF<input name="pdf_url" value="{h(form_product.get("pdf_url", ""))}" placeholder="/uploads/docs/spec.pdf" /></label>
          <label>Video URL<input name="video_url" value="{h(form_product.get("video_url", ""))}" /></label>
          <label>Upload ảnh mới<input type="file" name="image_file" accept="image/*" data-image-preview-input /></label>
          <img class="image-preview" src="{h(image_value)}" alt="Xem trước ảnh" data-image-preview />
          <label>Tag<input name="tags_text" value="{h(form_product.get("tags_text", ""))}" placeholder="cnc, inox, linh kiện chính xác" /></label>
          <button class="btn btn-secondary" type="submit" formaction="/admin/products/ai-generate" formnovalidate>AI tạo nội dung & SEO</button>
          <p class="form-hint">AI chỉ điền gợi ý vào form, chưa lưu database. Kiểm tra lại rồi bấm Lưu sản phẩm.</p>
          <label>SEO title<input name="seo_title" value="{h(form_product.get("seo_title", ""))}" /></label>
          <label>SEO description<textarea name="seo_description" rows="2">{h(form_product.get("seo_description", ""))}</textarea></label>
          <label>SEO keyword<input name="seo_keywords" value="{h(form_product.get("seo_keywords", ""))}" /></label>
          <label>Canonical URL<input name="canonical_url" value="{h(form_product.get("canonical_url", ""))}" /></label>
          <label>OG Image<input name="og_image" value="{h(form_product.get("og_image", ""))}" /></label>
          <label>Robots<input name="robots" value="{h(form_product.get("robots", "index,follow"))}" /></label>
          <label>Schema.org JSON<textarea name="schema_json" rows="3">{h(form_product.get("schema_json", ""))}</textarea></label>
          <label>Related Products<input name="related_product_ids" value="{h(form_product.get("related_product_ids", ""))}" placeholder="Ví dụ: 1,3,5" /></label>
          <label>Thứ tự hiển thị<input type="number" name="sort_order" value="{h(form_product.get("sort_order", 0))}" /></label>
          <label>Ngày xuất bản<input name="published_at" value="{h(form_product.get("published_at", ""))}" placeholder="YYYY-MM-DD HH:MM:SS" /></label>
          <label>Status<select name="status">{render_status_options(form_product.get("status", "published"))}</select></label>
          <label class="checkbox-row"><input type="checkbox" name="is_featured" value="1" {"checked" if form_product.get("is_featured") else ""} /> Sản phẩm nổi bật</label>
          <button class="btn btn-primary" type="submit">Lưu sản phẩm</button>
          <button class="btn btn-secondary" type="submit" name="save_mode" value="draft">Lưu nháp</button>
        </form>
        <div>
          {product_filter_html}
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead><tr><th>ID</th><th>Ảnh</th><th>Sản phẩm</th><th>Mô tả</th><th>Giá</th><th>Status</th><th>Sort</th><th>Hành động</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
          {render_pagination('/admin/products', page, per_page, total, q, filter_extra)}
        </div>
      </div>
    """
    return render_admin_shell("Quản lý sản phẩm", "products", admin_user, content)


def render_admin_categories_page(admin_user, params, form_category=None, message="", error=""):
    """Render module quản lý danh mục sản phẩm."""
    q = str(params.get("q", "")).strip()
    page = parse_positive_int(params.get("page"), 1)
    per_page = 8
    categories, total = get_paginated_categories(q, page, per_page)
    form_category = form_category or {}
    category_id = form_category.get("id", "")
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><strong>{h(item["name"])}</strong><br><span>{h(item["slug"])}</span></td>
          <td>{h(item["description"])}</td>
          <td>{h(item["sort_order"])}</td>
          <td>
            <a class="text-link" href="/admin/categories/{item["id"]}/edit">Sửa</a>
            <form class="inline-delete-form" method="post" action="/admin/categories/{item["id"]}/delete" data-confirm-delete>
              <button type="submit">Xóa</button>
            </form>
          </td>
        </tr>
        """
        for item in categories
    ) or '<tr><td colspan="5">Không có danh mục.</td></tr>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/categories/save">
          <input type="hidden" name="id" value="{h(category_id)}" />
          <h2>{'Sửa danh mục' if category_id else 'Thêm danh mục'}</h2>
          <label>Tên danh mục<input name="name" value="{h(form_category.get("name", ""))}" required /></label>
          <label>Slug<input name="slug" value="{h(form_category.get("slug", ""))}" /></label>
          <label>Mô tả<textarea name="description" rows="4">{h(form_category.get("description", ""))}</textarea></label>
          <label>Thứ tự<input type="number" name="sort_order" value="{h(form_category.get("sort_order", 0))}" /></label>
          <button class="btn btn-primary" type="submit">Lưu danh mục</button>
        </form>
        <div>
          {render_admin_search('/admin/categories', q)}
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead><tr><th>ID</th><th>Danh mục</th><th>Mô tả</th><th>Thứ tự</th><th>Hành động</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
          {render_pagination('/admin/categories', page, per_page, total, q)}
        </div>
      </div>
    """
    return render_admin_shell("Quản lý danh mục", "categories", admin_user, content)


def render_admin_news_page(admin_user, params, form_news=None, message="", error=""):
    """Render module quản lý tin tức."""
    q = str(params.get("q", "")).strip()
    page = parse_positive_int(params.get("page"), 1)
    per_page = parse_positive_int(params.get("per_page"), 20)
    category_filter = parse_positive_int(params.get("category_id"), 0)
    status_filter = str(params.get("status", "")).strip()
    sort_filter = str(params.get("sort", "newest")).strip()
    news_items, total = get_paginated_news(q, page, per_page, category_filter, status_filter, sort_filter)
    form_news = form_news or {}
    news_id = form_news.get("id", "")
    image_value = form_news.get("image", "")
    filter_extra = {
        "category_id": category_filter or "",
        "status": status_filter,
        "sort": sort_filter,
        "per_page": per_page,
    }
    news_filter_html = f"""
      <form class="admin-filter-panel" method="get" action="/admin/news">
        <label>Tìm kiếm<input type="search" name="q" value="{h(q)}" placeholder="Tiêu đề, tag, mô tả..." /></label>
        <label>Category<select name="category_id"><option value="">Tất cả category</option>{render_news_category_options(category_filter)}</select></label>
        <label>Status<select name="status">
          <option value="" {"selected" if not status_filter else ""}>Tất cả</option>
          <option value="draft" {"selected" if status_filter == "draft" else ""}>Draft</option>
          <option value="published" {"selected" if status_filter == "published" else ""}>Published</option>
          <option value="archived" {"selected" if status_filter == "archived" else ""}>Archived</option>
        </select></label>
        <label>Sắp xếp<select name="sort">
          <option value="newest" {"selected" if sort_filter == "newest" else ""}>Mới nhất</option>
          <option value="oldest" {"selected" if sort_filter == "oldest" else ""}>Cũ nhất</option>
          <option value="title" {"selected" if sort_filter == "title" else ""}>Tiêu đề A-Z</option>
          <option value="featured" {"selected" if sort_filter == "featured" else ""}>Featured trước</option>
        </select></label>
        <label>Số bài/trang<input type="number" name="per_page" min="5" max="100" value="{h(per_page)}" /></label>
        <button class="btn btn-primary" type="submit">Tìm</button>
      </form>
    """
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><img class="admin-thumb" src="{h(item.get("thumbnail_url") or item["image"])}" alt="{h(item["title"])}" /></td>
          <td><strong>{h(item["title"])}</strong><br><span>{h(item["category"])}</span></td>
          <td>{h(item["description"])}</td>
          <td>{h(item.get("status", ""))}</td>
          <td>{h(item.get("author", ""))}</td>
          <td>
            <a class="text-link" href="/admin/news/{item["id"]}/edit">Sửa</a>
            <form class="inline-delete-form" method="post" action="/admin/news/{item["id"]}/delete" data-confirm-delete>
              <button type="submit">Xóa</button>
            </form>
          </td>
        </tr>
        """
        for item in news_items
    ) or '<tr><td colspan="7">Không có tin tức.</td></tr>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" enctype="multipart/form-data" action="/admin/news/save">
          <input type="hidden" name="id" value="{h(news_id)}" />
          <h2>{'Sửa tin tức' if news_id else 'Thêm tin tức'}</h2>
          <label>Danh mục tin<select name="category_id" required>{render_news_category_options(form_news.get("category_id"))}</select></label>
          <label>Tiêu đề<input name="title" value="{h(form_news.get("title", ""))}" required /></label>
          <label>Slug<input name="slug" value="{h(form_news.get("slug", ""))}" /></label>
          <label>Ảnh hiện tại / URL ảnh<input name="image" value="{h(image_value)}" data-image-preview-input /></label>
          <label>Thumbnail<input name="thumbnail_url" value="{h(form_news.get("thumbnail_url", ""))}" placeholder="Có thể để trống để dùng ảnh chính" /></label>
          <label>Upload ảnh mới<input type="file" name="image_file" accept="image/*" data-image-preview-input /></label>
          <img class="image-preview" src="{h(image_value)}" alt="Xem trước ảnh" data-image-preview />
          <label>Mô tả<textarea name="description" rows="3" required>{h(form_news.get("description", ""))}</textarea></label>
          <label>Nội dung<textarea name="content" rows="5">{h(form_news.get("content", ""))}</textarea></label>
          <label>Tag<input name="tags_text" value="{h(form_news.get("tags_text", ""))}" placeholder="tin công nghệ, cnc, nhà máy" /></label>
          <label>SEO title<input name="seo_title" value="{h(form_news.get("seo_title", ""))}" /></label>
          <label>SEO description<textarea name="seo_description" rows="2">{h(form_news.get("seo_description", ""))}</textarea></label>
          <label>Tác giả<input name="author" value="{h(form_news.get("author", ""))}" /></label>
          <label>Publish Date<input name="published_at" value="{h(form_news.get("published_at", ""))}" placeholder="YYYY-MM-DD HH:MM:SS" /></label>
          <label>Schedule Publish<input name="scheduled_at" value="{h(form_news.get("scheduled_at", ""))}" placeholder="YYYY-MM-DD HH:MM:SS" /></label>
          <label>Status<select name="status">{render_status_options(form_news.get("status", "published"))}</select></label>
          <label class="checkbox-row"><input type="checkbox" name="is_featured" value="1" {"checked" if form_news.get("is_featured") else ""} /> Tin nổi bật</label>
          <button class="btn btn-primary" type="submit">Lưu tin tức</button>
          <button class="btn btn-secondary" type="submit" name="save_mode" value="draft">Lưu nháp</button>
        </form>
        <div>
          {news_filter_html}
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead><tr><th>ID</th><th>Ảnh</th><th>Tin tức</th><th>Mô tả</th><th>Status</th><th>Tác giả</th><th>Hành động</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
          {render_pagination('/admin/news', page, per_page, total, q, filter_extra)}
        </div>
      </div>
    """
    return render_admin_shell("Quản lý tin tức", "news", admin_user, content)


def render_admin_media_page(admin_user, params, message="", error=""):
    """Render Media Manager giống WordPress ở mức local."""
    q = str(params.get("q", "")).strip()
    folder = str(params.get("folder", "")).strip()
    folders = list_folders()
    media_items = list_media(folder, q)
    folder_options = "\n".join(
        f'<option value="{h(item)}" {"selected" if item == folder else ""}>{"Uploads" if not item else h(item)}</option>'
        for item in folders
    )
    folder_links = "\n".join(
        f'<a class="{"active" if item == folder else ""}" href="/admin/media?{build_query_string({"folder": item, "q": q})}">{"Uploads" if not item else h(item)}</a>'
        for item in folders
    )
    cards = "\n".join(
        f"""
        <article class="media-card">
          <div class="media-preview">
            {f'<img src="{h(item["url"])}" alt="{h(item["name"])}" />' if item["is_image"] else f'<span>{h(item["content_type"])}</span>'}
          </div>
          <div class="media-card-body">
            <h3>{h(item["name"])}</h3>
            <p>{h(item["folder"])}</p>
            <p>{h(item["modified_at"])} · {h(round(item["size"] / 1024, 1))} KB</p>
            <div class="media-actions">
              <a class="text-link" href="{h(item["url"])}" target="_blank" rel="noreferrer">Preview</a>
              <button type="button" data-copy-url="{h(item["url"])}">Copy URL</button>
            </div>
            <form class="media-inline-form" method="post" action="/admin/media/rename">
              <input type="hidden" name="url" value="{h(item["url"])}" />
              <input name="new_name" value="{h(Path(item["name"]).stem)}" aria-label="Tên mới" />
              <button type="submit">Rename</button>
            </form>
            <form class="media-inline-form" method="post" action="/admin/media/delete" data-confirm-delete>
              <input type="hidden" name="url" value="{h(item["url"])}" />
              <button type="submit">Delete</button>
            </form>
          </div>
        </article>
        """
        for item in media_items
    ) or '<p class="admin-empty-state">Chưa có media phù hợp.</p>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="media-manager-layout">
        <aside class="media-folder-panel">
          <h2>Folder</h2>
          <nav>{folder_links}</nav>
          <form class="admin-form media-folder-form" method="post" action="/admin/media/folders/create">
            <label>Tạo folder mới<input name="folder" placeholder="images/products" required /></label>
            <button class="btn btn-primary" type="submit">Tạo folder</button>
          </form>
        </aside>
        <section class="media-main-panel">
          <div class="media-toolbar">
            <form class="admin-form media-upload-form" method="post" enctype="multipart/form-data" action="/admin/media/upload">
              <label>Folder<select name="folder">{folder_options}</select></label>
              <label>Upload file<input type="file" name="media_file" required /></label>
              <button class="btn btn-primary" type="submit">Upload</button>
            </form>
            <form class="admin-toolbar" method="get" action="/admin/media">
              <input type="hidden" name="folder" value="{h(folder)}" />
              <input type="search" name="q" value="{h(q)}" placeholder="Tìm media..." />
              <button class="btn btn-primary" type="submit">Tìm</button>
            </form>
          </div>
          <div class="media-grid">{cards}</div>
        </section>
      </div>
    """
    return render_admin_shell("Media Manager", "media", admin_user, content)


def render_status_options(selected="draft"):
    """Tạo option status dùng chung cho CMS."""
    return "\n".join(
        f'<option value="{status}" {"selected" if selected == status else ""}>{label}</option>'
        for status, label in [
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ]
    )


def render_admin_pages_page(admin_user, params, form_page=None, message="", error=""):
    """Render CMS tạo trang động."""
    q = str(params.get("q", "")).strip()
    page_number = parse_positive_int(params.get("page"), 1)
    pages, total = get_paginated_pages(q, page_number, 8)
    form_page = form_page or {"status": "draft", "sort_order": 0}
    page_id = form_page.get("id", "")
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><strong>{h(item["title"])}</strong><br><span>/{h(item["slug"])}</span></td>
          <td>{h(item["status"])}</td>
          <td>{h(item["sort_order"])}</td>
          <td>
            <a class="text-link" href="/admin/pages/{item["id"]}/edit">Sửa</a>
            <form class="inline-delete-form" method="post" action="/admin/pages/{item["id"]}/delete" data-confirm-delete><button type="submit">Xóa</button></form>
          </td>
        </tr>
        """
        for item in pages
    ) or '<tr><td colspan="5">Chưa có trang động.</td></tr>'
    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/pages/save">
          <input type="hidden" name="id" value="{h(page_id)}" />
          <h2>{'Sửa trang' if page_id else 'Tạo trang'}</h2>
          <label>Tiêu đề<input name="title" value="{h(form_page.get("title", ""))}" required /></label>
          <label>Slug<input name="slug" value="{h(form_page.get("slug", ""))}" placeholder="about, privacy..." /></label>
          <label>SEO title<input name="seo_title" value="{h(form_page.get("seo_title", ""))}" /></label>
          <label>SEO description<textarea name="seo_description" rows="2">{h(form_page.get("seo_description", ""))}</textarea></label>
          <label>Status<select name="status">{render_status_options(form_page.get("status", "draft"))}</select></label>
          <label>Sort order<input type="number" name="sort_order" value="{h(form_page.get("sort_order", 0))}" /></label>
          <label>Nội dung<textarea name="content" rows="8">{h(form_page.get("content", ""))}</textarea></label>
          <button class="btn btn-primary" type="submit">Lưu trang</button>
        </form>
        <div>
          {render_admin_search('/admin/pages', q)}
          <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Trang</th><th>Status</th><th>Sort</th><th>Hành động</th></tr></thead><tbody>{rows}</tbody></table></div>
          {render_pagination('/admin/pages', page_number, 8, total, q)}
        </div>
      </div>
    """
    return render_admin_shell("Pages", "pages", admin_user, content)


def render_admin_menus_page(admin_user, form_menu=None, message="", error=""):
    """Render Menu Builder: header/footer/sidebar, sort order và parent_id cho nested menu."""
    items = get_menu_items()
    form_menu = form_menu or {"location": "header", "status": "published", "sort_order": 0}
    parent_options = '<option value="">Không có menu cha</option>' + "\n".join(
        f'<option value="{item["id"]}" {"selected" if form_menu.get("parent_id") == item["id"] else ""}>{h(item["location"])} / {h(item["label"])}</option>'
        for item in items
        if item.get("id") != form_menu.get("id")
    )
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td>{h(item["location"])}</td>
          <td>{"— " if item["parent_id"] else ""}{h(item["label"])}</td>
          <td>{h(item["url"])}</td>
          <td>{h(item["sort_order"])}</td>
          <td>{h(item["status"])}</td>
          <td><a class="text-link" href="/admin/menus/{item["id"]}/edit">Sửa</a><form class="inline-delete-form" method="post" action="/admin/menus/{item["id"]}/delete" data-confirm-delete><button type="submit">Xóa</button></form></td>
        </tr>
        """
        for item in items
    ) or '<tr><td colspan="7">Chưa có menu.</td></tr>'
    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/menus/save">
          <input type="hidden" name="id" value="{h(form_menu.get("id", ""))}" />
          <h2>Menu Builder</h2>
          <label>Vị trí<select name="location">
            <option value="header" {"selected" if form_menu.get("location") == "header" else ""}>Header Menu</option>
            <option value="footer" {"selected" if form_menu.get("location") == "footer" else ""}>Footer Menu</option>
            <option value="sidebar" {"selected" if form_menu.get("location") == "sidebar" else ""}>Sidebar</option>
          </select></label>
          <label>Menu cha<select name="parent_id">{parent_options}</select></label>
          <label>Label<input name="label" value="{h(form_menu.get("label", ""))}" required /></label>
          <label>URL<input name="url" value="{h(form_menu.get("url", ""))}" required /></label>
          <label>Sort order<input type="number" name="sort_order" value="{h(form_menu.get("sort_order", 0))}" /></label>
          <label>Status<select name="status">{render_status_options(form_menu.get("status", "published"))}</select></label>
          <p class="form-hint">Drag & Drop bản local được mô phỏng bằng Sort order + Menu cha để tạo nested menu.</p>
          <button class="btn btn-primary" type="submit">Lưu menu</button>
        </form>
        <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Vị trí</th><th>Label</th><th>URL</th><th>Sort</th><th>Status</th><th>Hành động</th></tr></thead><tbody>{rows}</tbody></table></div>
      </div>
    """
    return render_admin_shell("Menu Builder", "menus", admin_user, content)


def render_admin_banners_page(admin_user, params, form_banner=None, message="", error=""):
    """Render Banner CMS: slider, popup, advertisement."""
    q = str(params.get("q", "")).strip()
    page_number = parse_positive_int(params.get("page"), 1)
    banners, total = get_paginated_banners(q, page_number, 8)
    form_banner = form_banner or {"placement": "home_slider", "status": "draft", "sort_order": 0}
    image_value = form_banner.get("image_url", "")
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td>{f'<img class="admin-thumb" src="{h(item["image_url"])}" alt="{h(item["title"])}" />' if item.get("image_url") else ""}</td>
          <td><strong>{h(item["title"])}</strong><br><span>{h(item["placement"])}</span></td>
          <td>{h(item["status"])}</td>
          <td>{h(item["sort_order"])}</td>
          <td><a class="text-link" href="/admin/banners/{item["id"]}/edit">Sửa</a><form class="inline-delete-form" method="post" action="/admin/banners/{item["id"]}/delete" data-confirm-delete><button type="submit">Xóa</button></form></td>
        </tr>
        """
        for item in banners
    ) or '<tr><td colspan="6">Chưa có banner.</td></tr>'
    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" enctype="multipart/form-data" action="/admin/banners/save">
          <input type="hidden" name="id" value="{h(form_banner.get("id", ""))}" />
          <h2>Banner</h2>
          <label>Tiêu đề<input name="title" value="{h(form_banner.get("title", ""))}" required /></label>
          <label>Placement<select name="placement">
            <option value="home_slider" {"selected" if form_banner.get("placement") == "home_slider" else ""}>Trang chủ / Slider</option>
            <option value="popup" {"selected" if form_banner.get("placement") == "popup" else ""}>Popup</option>
            <option value="advertisement" {"selected" if form_banner.get("placement") == "advertisement" else ""}>Advertisement</option>
          </select></label>
          <label>Ảnh / URL<input name="image_url" value="{h(image_value)}" data-image-preview-input /></label>
          <label>Upload ảnh<input type="file" name="image_file" accept="image/*" data-image-preview-input /></label>
          <img class="image-preview" src="{h(image_value)}" alt="Preview banner" data-image-preview />
          <label>Link URL<input name="link_url" value="{h(form_banner.get("link_url", ""))}" /></label>
          <label>Nội dung<textarea name="content" rows="3">{h(form_banner.get("content", ""))}</textarea></label>
          <label>Status<select name="status">{render_status_options(form_banner.get("status", "draft"))}</select></label>
          <label>Sort order<input type="number" name="sort_order" value="{h(form_banner.get("sort_order", 0))}" /></label>
          <label>Starts at<input name="starts_at" value="{h(form_banner.get("starts_at", ""))}" /></label>
          <label>Ends at<input name="ends_at" value="{h(form_banner.get("ends_at", ""))}" /></label>
          <button class="btn btn-primary" type="submit">Lưu banner</button>
        </form>
        <div>
          {render_admin_search('/admin/banners', q)}
          <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Ảnh</th><th>Banner</th><th>Status</th><th>Sort</th><th>Hành động</th></tr></thead><tbody>{rows}</tbody></table></div>
          {render_pagination('/admin/banners', page_number, 8, total, q)}
        </div>
      </div>
    """
    return render_admin_shell("Banner", "banners", admin_user, content)


def render_admin_contacts_page(admin_user, params, form_contact=None, message="", error=""):
    """Render module quản lý liên hệ."""
    q = str(params.get("q", "")).strip()
    page = parse_positive_int(params.get("page"), 1)
    per_page = 8
    contacts, total = get_paginated_contacts(q, page, per_page)
    form_contact = form_contact or {}
    contact_id = form_contact.get("id", "")
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><strong>{h(item["name"])}</strong><br><span>{h(item.get("company", ""))}</span></td>
          <td>{h(item.get("email") or item["contact"])}<br><span>{h(item.get("phone", ""))}</span></td>
          <td>{h(item.get("interested_product", ""))}<br><span>{h(item["message"])}</span></td>
          <td>{h(item["status"])}<br><span>{'Đã đọc' if item.get("is_read") else 'Chưa đọc'}</span></td>
          <td>
            <a class="text-link" href="/admin/contacts/{item["id"]}/edit">Sửa</a>
            <form class="inline-delete-form" method="post" action="/admin/contacts/{item["id"]}/delete" data-confirm-delete>
              <button type="submit">Xóa</button>
            </form>
          </td>
        </tr>
        """
        for item in contacts
    ) or '<tr><td colspan="6">Không có liên hệ.</td></tr>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/contacts/save">
          <input type="hidden" name="id" value="{h(contact_id)}" />
          <h2>{'Sửa liên hệ' if contact_id else 'Thêm liên hệ'}</h2>
          <label>Họ tên<input name="name" value="{h(form_contact.get("name", ""))}" required /></label>
          <label>Công ty<input name="company" value="{h(form_contact.get("company", ""))}" /></label>
          <label>Email<input name="email" value="{h(form_contact.get("email", ""))}" /></label>
          <label>Điện thoại<input name="phone" value="{h(form_contact.get("phone", ""))}" /></label>
          <label>Email / điện thoại tổng hợp<input name="contact" value="{h(form_contact.get("contact", ""))}" required /></label>
          <label>Quốc gia<input name="country" value="{h(form_contact.get("country", ""))}" /></label>
          <label>Sản phẩm quan tâm<input name="interested_product" value="{h(form_contact.get("interested_product", ""))}" /></label>
          <label>File đính kèm / URL<input name="attachment_url" value="{h(form_contact.get("attachment_url", ""))}" /></label>
          <label>Trạng thái<select name="status">
            <option value="new" {"selected" if form_contact.get("status", "new") == "new" else ""}>new</option>
            <option value="processing" {"selected" if form_contact.get("status") == "processing" else ""}>processing</option>
            <option value="done" {"selected" if form_contact.get("status") == "done" else ""}>done</option>
          </select></label>
          <label class="checkbox-row"><input type="checkbox" name="is_read" value="1" {"checked" if form_contact.get("is_read") else ""} /> Đã đọc</label>
          <label>Nội dung<textarea name="message" rows="5">{h(form_contact.get("message", ""))}</textarea></label>
          <label>Ghi chú nội bộ<textarea name="note" rows="4">{h(form_contact.get("note", ""))}</textarea></label>
          <button class="btn btn-primary" type="submit">Lưu liên hệ</button>
        </form>
        <div>
          <a class="text-link" href="/admin/contacts/export">Export CSV</a>
          {render_admin_search('/admin/contacts', q)}
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead><tr><th>ID</th><th>Khách hàng</th><th>Liên hệ</th><th>Nội dung</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
          {render_pagination('/admin/contacts', page, per_page, total, q)}
        </div>
      </div>
    """
    return render_admin_shell("Quản lý liên hệ", "contacts", admin_user, content)


def render_admin_quotes_page(admin_user, params, form_quote=None, message="", error=""):
    """Render workflow yêu cầu báo giá MEC."""
    q = str(params.get("q", "")).strip()
    page_number = parse_positive_int(params.get("page"), 1)
    quotes, total = get_paginated_quotes(q, page_number, 8)
    form_quote = form_quote or {}
    admin_options = '<option value="">Chưa phân công</option>' + "\n".join(
        f'<option value="{item["id"]}" {"selected" if form_quote.get("assigned_to") == item["id"] else ""}>{h(item["full_name"])}</option>'
        for item in get_admin_options()
    )
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><strong>{h(item["project_name"])}</strong><br><span>{h(item["company_name"] or item["contact_name"])}</span></td>
          <td>{h(item["status"])}</td>
          <td>{h(item.get("assigned_name", ""))}</td>
          <td>{h(item["created_at"])}</td>
          <td><a class="text-link" href="/admin/quotes/{item["id"]}/edit">Xử lý</a></td>
        </tr>
        """
        for item in quotes
    ) or '<tr><td colspan="6">Chưa có yêu cầu báo giá.</td></tr>'
    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/quotes/save">
          <input type="hidden" name="id" value="{h(form_quote.get("id", ""))}" />
          <h2>Workflow báo giá</h2>
          <label>Dự án<input value="{h(form_quote.get("project_name", ""))}" disabled /></label>
          <label>Trạng thái<select name="status">
            {''.join(f'<option value="{status}" {"selected" if form_quote.get("status", "new") == status else ""}>{label}</option>' for status, label in [
              ("new", "Yêu cầu báo giá"),
              ("assigned", "Phân công nhân viên"),
              ("processing", "Đã xử lý"),
              ("quoted", "Đã báo giá"),
              ("completed", "Hoàn thành"),
            ])}
          </select></label>
          <label>Phân công<select name="assigned_to">{admin_options}</select></label>
          <label>Đã báo giá lúc<input name="quoted_at" value="{h(form_quote.get("quoted_at", ""))}" /></label>
          <label>Hoàn thành lúc<input name="completed_at" value="{h(form_quote.get("completed_at", ""))}" /></label>
          <label>Ghi chú nội bộ<textarea name="internal_note" rows="4">{h(form_quote.get("internal_note", ""))}</textarea></label>
          <button class="btn btn-primary" type="submit">Cập nhật báo giá</button>
        </form>
        <div>
          {render_admin_search('/admin/quotes', q)}
          <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Yêu cầu</th><th>Trạng thái</th><th>Phụ trách</th><th>Ngày tạo</th><th>Hành động</th></tr></thead><tbody>{rows}</tbody></table></div>
          {render_pagination('/admin/quotes', page_number, 8, total, q)}
        </div>
      </div>
    """
    return render_admin_shell("Yêu cầu báo giá", "quotes", admin_user, content)


def render_admin_customers_page(admin_user, params, form_customer=None, message="", error=""):
    """Render Customer Management."""
    q = str(params.get("q", "")).strip()
    page_number = parse_positive_int(params.get("page"), 1)
    customers, total = get_paginated_customers(q, page_number, 8)
    form_customer = form_customer or {"country": "Vietnam"}
    notes = get_customer_notes(form_customer["id"]) if form_customer.get("id") else []
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td><strong>{h(item["company_name"])}</strong><br><span>{h(item["contact_name"])}</span></td>
          <td>{h(item["email"])}</td>
          <td>{h(item["phone"])}</td>
          <td>{h(item["country"])}</td>
          <td><a class="text-link" href="/admin/customers/{item["id"]}/edit">Sửa</a><form class="inline-delete-form" method="post" action="/admin/customers/{item["id"]}/delete" data-confirm-delete><button type="submit">Xóa</button></form></td>
        </tr>
        """
        for item in customers
    ) or '<tr><td colspan="6">Chưa có khách hàng.</td></tr>'
    note_rows = "\n".join(
        f"<tr><td>{h(item['created_at'])}</td><td>{h(item['created_by'])}</td><td>{h(item['note'])}</td></tr>"
        for item in notes
    ) or '<tr><td colspan="3">Chưa có ghi chú/lịch sử.</td></tr>'
    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/customers/save">
          <input type="hidden" name="id" value="{h(form_customer.get("id", ""))}" />
          <h2>Khách hàng</h2>
          <label>Công ty<input name="company_name" value="{h(form_customer.get("company_name", ""))}" /></label>
          <label>Người liên hệ<input name="contact_name" value="{h(form_customer.get("contact_name", ""))}" required /></label>
          <label>Email<input name="email" value="{h(form_customer.get("email", ""))}" /></label>
          <label>Điện thoại<input name="phone" value="{h(form_customer.get("phone", ""))}" /></label>
          <label>Quốc gia<input name="country" value="{h(form_customer.get("country", "Vietnam"))}" /></label>
          <button class="btn btn-primary" type="submit">Lưu khách hàng</button>
        </form>
        <div>
          {render_admin_search('/admin/customers', q)}
          <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Khách hàng</th><th>Email</th><th>Điện thoại</th><th>Quốc gia</th><th>Hành động</th></tr></thead><tbody>{rows}</tbody></table></div>
          {render_pagination('/admin/customers', page_number, 8, total, q)}
        </div>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>Ngày</th><th>Người ghi</th><th>Ghi chú / Lịch sử</th></tr></thead><tbody>{note_rows}</tbody></table>
      </div>
      {f'<form class="admin-form" method="post" action="/admin/customers/{form_customer.get("id")}/notes"><label>Thêm ghi chú<textarea name="note" rows="3"></textarea></label><button class="btn btn-primary" type="submit">Lưu ghi chú</button></form>' if form_customer.get("id") else ''}
    """
    return render_admin_shell("Khách hàng", "customers", admin_user, content)


def render_admin_newsletter_page(admin_user, params, form_subscriber=None, message="", error=""):
    """Render Newsletter CMS."""
    q = str(params.get("q", "")).strip()
    page_number = parse_positive_int(params.get("page"), 1)
    subscribers, total = get_paginated_newsletter(q, page_number, 8)
    form_subscriber = form_subscriber or {"status": "subscribed"}
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td>{h(item["email"])}</td>
          <td>{h(item["status"])}</td>
          <td>{h(item["subscribed_at"])}</td>
          <td>{h(item["unsubscribed_at"])}</td>
          <td><a class="text-link" href="/admin/newsletter/{item["id"]}/edit">Sửa</a><form class="inline-delete-form" method="post" action="/admin/newsletter/{item["id"]}/delete" data-confirm-delete><button type="submit">Xóa</button></form></td>
        </tr>
        """
        for item in subscribers
    ) or '<tr><td colspan="6">Chưa có email newsletter.</td></tr>'
    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/newsletter/save">
          <input type="hidden" name="id" value="{h(form_subscriber.get("id", ""))}" />
          <h2>Newsletter</h2>
          <label>Email<input type="email" name="email" value="{h(form_subscriber.get("email", ""))}" required /></label>
          <label>Status<select name="status">
            <option value="subscribed" {"selected" if form_subscriber.get("status") == "subscribed" else ""}>Đăng ký</option>
            <option value="unsubscribed" {"selected" if form_subscriber.get("status") == "unsubscribed" else ""}>Hủy đăng ký</option>
          </select></label>
          <button class="btn btn-primary" type="submit">Lưu email</button>
          <a class="text-link" href="/admin/newsletter/export">Export CSV</a>
        </form>
        <div>
          {render_admin_search('/admin/newsletter', q)}
          <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Email</th><th>Status</th><th>Đăng ký</th><th>Hủy</th><th>Hành động</th></tr></thead><tbody>{rows}</tbody></table></div>
          {render_pagination('/admin/newsletter', page_number, 8, total, q)}
        </div>
      </div>
    """
    return render_admin_shell("Newsletter", "newsletter", admin_user, content)


def render_admin_users_page(admin_user, params, form_user=None, message="", error=""):
    """Render module quản lý người dùng."""
    q = str(params.get("q", "")).strip()
    page = parse_positive_int(params.get("page"), 1)
    per_page = 8
    users, total = get_paginated_users(q, page, per_page)
    form_user = form_user or {"is_active": 1}
    user_id = form_user.get("id", "")
    avatar_value = form_user.get("avatar_url", "") or ""
    activity_logs = get_recent_activity_logs(8)
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td>
            <div class="user-cell">
              {f'<img class="user-avatar" src="{h(item["avatar_url"])}" alt="{h(item["full_name"])}" />' if item.get("avatar_url") else f'<span class="user-avatar user-avatar-fallback">{h(item["full_name"][:1].upper())}</span>'}
              <div><strong>{h(item["full_name"])}</strong><br><span>{h(item["email"])}</span></div>
            </div>
          </td>
          <td><span class="role-badge">{h(item["role"])}</span></td>
          <td>{"Đang hoạt động" if item["is_active"] else "Tạm khóa"}</td>
          <td>{h(item.get("created_at", ""))}</td>
          <td>{h(format_timestamp(item.get("last_login_at")))}</td>
          <td>
            <a class="text-link" href="/admin/users/{item["id"]}/edit">Sửa</a>
            <form class="inline-delete-form" method="post" action="/admin/users/{item["id"]}/{'lock' if item["is_active"] else 'unlock'}" data-confirm-delete>
              <button type="submit">{"Khóa" if item["is_active"] else "Mở khóa"}</button>
            </form>
            <form class="inline-delete-form" method="post" action="/admin/users/{item["id"]}/delete" data-confirm-delete>
              <button type="submit">Xóa</button>
            </form>
          </td>
        </tr>
        """
        for item in users
    ) or '<tr><td colspan="7">Không có người dùng.</td></tr>'

    activity_rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["created_at"])}</td>
          <td>{h(item["actor_name"])}</td>
          <td>{h(item["action"])}</td>
          <td>{h(item["target_type"])} #{h(item["target_id"])}</td>
          <td>{h(item["description"])}</td>
        </tr>
        """
        for item in activity_logs
    ) or '<tr><td colspan="5">Chưa có nhật ký hoạt động.</td></tr>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" enctype="multipart/form-data" action="/admin/users/save">
          <input type="hidden" name="id" value="{h(user_id)}" />
          <h2>{'Sửa người dùng' if user_id else 'Thêm người dùng'}</h2>
          <label>Họ tên<input name="full_name" value="{h(form_user.get("full_name", ""))}" required /></label>
          <label>Email<input type="email" name="email" value="{h(form_user.get("email", ""))}" required /></label>
          <label>Role<select name="role">
            <option value="admin" {"selected" if form_user.get("role") == "admin" else ""}>Admin</option>
            <option value="editor" {"selected" if form_user.get("role", "viewer") == "editor" else ""}>Editor</option>
            <option value="viewer" {"selected" if form_user.get("role", "viewer") == "viewer" else ""}>Viewer</option>
          </select></label>
          <p class="form-hint">Phân quyền: Admin quản lý toàn bộ, Editor chỉnh nội dung, Viewer chỉ xem.</p>
          <label>Avatar hiện tại / URL ảnh<input name="avatar_url" value="{h(avatar_value)}" data-image-preview-input /></label>
          <label>Upload avatar mới<input type="file" name="avatar_file" accept="image/*" data-image-preview-input /></label>
          <img class="image-preview user-avatar-preview" src="{h(avatar_value)}" alt="Xem trước avatar" data-image-preview />
          <label>Mật khẩu<input type="password" name="password" placeholder="Bắt buộc khi tạo mới, để trống nếu không đổi" /></label>
          <label class="checkbox-row"><input type="checkbox" name="is_active" value="1" {"checked" if form_user.get("is_active", 1) else ""} /> Đang hoạt động</label>
          <button class="btn btn-primary" type="submit">Lưu người dùng</button>
        </form>
        <div>
          {render_admin_search('/admin/users', q)}
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead><tr><th>ID</th><th>Người dùng</th><th>Role</th><th>Trạng thái</th><th>Ngày tạo</th><th>Đăng nhập gần nhất</th><th>Hành động</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
          {render_pagination('/admin/users', page, per_page, total, q)}
        </div>
      </div>
      <div class="section-heading compact-heading">
        <div>
          <p class="eyebrow">Nhật ký hoạt động</p>
          <h2>Hoạt động gần đây trong CMS</h2>
        </div>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead><tr><th>Thời gian</th><th>Người thực hiện</th><th>Hành động</th><th>Đối tượng</th><th>Mô tả</th></tr></thead>
          <tbody>{activity_rows}</tbody>
        </table>
      </div>
    """
    return render_admin_shell("Quản lý người dùng", "users", admin_user, content)


def render_admin_account_page(admin_user, message="", error=""):
    """Render trang tài khoản cá nhân của admin đang đăng nhập."""
    sessions = list_admin_sessions(admin_user["admin_id"])
    current_session_id = admin_user.get("session_id")
    session_rows = "\n".join(
        f"""
        <tr>
          <td>{'Hiện tại' if item["session_id"] == current_session_id else h(item["session_id"][:10] + "...")}</td>
          <td>{h(item.get("remote_addr", ""))}</td>
          <td>{h((item.get("user_agent") or "")[:80])}</td>
          <td>{h(format_timestamp(item.get("last_seen_at")))}</td>
          <td>{h(format_timestamp(item.get("expires_at")))}</td>
          <td>
            <form class="inline-delete-form" method="post" action="/admin/account/sessions/revoke" data-confirm-delete>
              <input type="hidden" name="session_id" value="{h(item["session_id"])}" />
              <button type="submit" {"disabled" if item["session_id"] == current_session_id else ""}>Thu hồi</button>
            </form>
          </td>
        </tr>
        """
        for item in sessions
    ) or '<tr><td colspan="6">Không có session.</td></tr>'

    emails = list_auth_email_outbox(5)
    email_rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td>{h(item["recipient"])}</td>
          <td>{h(item["subject"])}</td>
          <td>{h(item["body"])}</td>
          <td>{h(item["created_at"])}</td>
        </tr>
        """
        for item in emails
    ) or '<tr><td colspan="5">Chưa có email demo.</td></tr>'

    content = f"""
      {render_admin_message(message, error)}
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/account/change-password">
          <h2>Đổi mật khẩu</h2>
          <label>Mật khẩu hiện tại<input type="password" name="current_password" required /></label>
          <label>Mật khẩu mới<input type="password" name="new_password" required /></label>
          <button class="btn btn-primary" type="submit">Đổi mật khẩu</button>
        </form>
        <form class="admin-form" method="post" action="/admin/account/change-email">
          <h2>Đổi email</h2>
          <label>Email hiện tại<input value="{h(admin_user["email"])}" disabled /></label>
          <label>Email mới<input type="email" name="new_email" required /></label>
          <label>Nhập mật khẩu để xác nhận<input type="password" name="password" required /></label>
          <button class="btn btn-primary" type="submit">Đổi email</button>
        </form>
        <form class="admin-form" method="post" action="/admin/account/2fa">
          <h2>2FA</h2>
          <p class="form-hint">Khi bật, lần đăng nhập tiếp theo cần nhập mã 6 số trong Email outbox demo.</p>
          <label class="checkbox-row"><input type="checkbox" name="two_factor_enabled" value="1" {"checked" if admin_user.get("two_factor_enabled") else ""} /> Bật xác thực hai lớp</label>
          <button class="btn btn-primary" type="submit">Lưu 2FA</button>
        </form>
      </div>
      <div class="section-heading compact-heading">
        <div>
          <p class="eyebrow">Session nhiều thiết bị</p>
          <h2>Thiết bị đang đăng nhập</h2>
        </div>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead><tr><th>Session</th><th>IP</th><th>Trình duyệt</th><th>Hoạt động cuối</th><th>Hết hạn</th><th>Hành động</th></tr></thead>
          <tbody>{session_rows}</tbody>
        </table>
      </div>
      <div class="section-heading compact-heading">
        <div>
          <p class="eyebrow">Email demo</p>
          <h2>Reset password bằng email</h2>
        </div>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead><tr><th>ID</th><th>Người nhận</th><th>Tiêu đề</th><th>Nội dung</th><th>Ngày tạo</th></tr></thead>
          <tbody>{email_rows}</tbody>
        </table>
      </div>
    """
    return render_admin_shell("Tài khoản của tôi", "account", admin_user, content)


def render_admin_settings_page(admin_user, message="", error=""):
    """Render module cài đặt hệ thống."""
    settings = get_system_settings()
    content = f"""
      {render_admin_message(message, error)}
      <form class="admin-form admin-settings-form" method="post" action="/admin/settings/save">
        <h2>Cài đặt hệ thống</h2>
        <h3>Company</h3>
        <label>Tên website<input name="site_name" value="{h(settings["site_name"])}" /></label>
        <label>Tên công ty<input name="company_name" value="{h(settings["company_name"])}" /></label>
        <label>Logo URL<input name="logo_url" value="{h(settings["logo_url"])}" /></label>
        <label>Favicon URL<input name="favicon_url" value="{h(settings["favicon_url"])}" /></label>
        <label>Email liên hệ<input name="contact_email" value="{h(settings["contact_email"])}" /></label>
        <label>Hotline<input name="hotline" value="{h(settings["hotline"])}" /></label>
        <label>Địa chỉ<textarea name="address" rows="3">{h(settings["address"])}</textarea></label>
        <h3>SMTP</h3>
        <label>SMTP host<input name="smtp_host" value="{h(settings["smtp_host"])}" placeholder="smtp.gmail.com" /></label>
        <label>SMTP port<input name="smtp_port" value="{h(settings["smtp_port"])}" /></label>
        <label>SMTP username<input name="smtp_username" value="{h(settings["smtp_username"])}" /></label>
        <label>From email<input name="smtp_from_email" value="{h(settings["smtp_from_email"])}" /></label>
        <h3>Tracking & Social</h3>
        <label>Google Analytics ID<input name="google_analytics_id" value="{h(settings["google_analytics_id"])}" placeholder="G-XXXXXXXXXX" /></label>
        <label>Facebook<input name="facebook_url" value="{h(settings["facebook_url"])}" /></label>
        <label>LinkedIn<input name="linkedin_url" value="{h(settings["linkedin_url"])}" /></label>
        <label>YouTube<input name="youtube_url" value="{h(settings["youtube_url"])}" /></label>
        <h3>Localization</h3>
        <label>Language<input name="language" value="{h(settings["language"])}" /></label>
        <label>Timezone<input name="timezone" value="{h(settings["timezone"])}" /></label>
        <h3>Security</h3>
        <label>IP Whitelist<textarea name="ip_whitelist" rows="3" placeholder="Để trống để cho phép mọi IP. Ví dụ: 127.0.0.1">{h(settings["ip_whitelist"])}</textarea></label>
        <label>Password min length<input type="number" name="password_min_length" value="{h(settings["password_min_length"])}" /></label>
        <label class="checkbox-row"><input type="checkbox" name="password_require_uppercase" value="1" {"checked" if settings["password_require_uppercase"] == "1" else ""} /> Bắt buộc có chữ hoa</label>
        <label class="checkbox-row"><input type="checkbox" name="password_require_digit" value="1" {"checked" if settings["password_require_digit"] == "1" else ""} /> Bắt buộc có chữ số</label>
        <label class="checkbox-row"><input type="checkbox" name="captcha_enabled" value="1" {"checked" if settings["captcha_enabled"] == "1" else ""} /> Bật Captcha login</label>
        <button class="btn btn-primary" type="submit">Lưu cài đặt</button>
      </form>
    """
    return render_admin_shell("Cài đặt hệ thống", "settings", admin_user, content)


def render_admin_developer_page(admin_user, message="", error="", ai_result="", ai_form=None):
    """Render Developer tools: health, version, system info, logs, backup."""
    ai_form = ai_form or {}
    health = get_health_status()
    system_info = get_system_info()
    backups = list_database_backups()
    events = get_recent_events(10)
    queue = get_queue_summary()
    notifications = get_recent_notifications(10)
    emails = list_auth_email_outbox(10)
    log_lines = read_recent_logs(80)
    info_rows = "\n".join(f"<tr><td>{h(key)}</td><td>{h(value)}</td></tr>" for key, value in system_info.items())
    backup_rows = "\n".join(
        f"<tr><td>{h(item['name'])}</td><td>{h(round(item['size'] / 1024, 1))} KB</td><td>{h(item['modified_at'])}</td></tr>"
        for item in backups
    ) or '<tr><td colspan="3">Chưa có backup.</td></tr>'
    event_rows = "\n".join(
        f"<tr><td>{h(item['id'])}</td><td>{h(item['event_name'])}</td><td>{h(item['entity_type'])} #{h(item['entity_id'])}</td><td>{h(item['created_at'])}</td></tr>"
        for item in events
    ) or '<tr><td colspan="4">Chưa có event.</td></tr>'
    job_rows = "\n".join(
        f"<tr><td>{h(item['id'])}</td><td>{h(item['job_type'])}</td><td>{h(item['status'])}</td><td>{h(item['attempts'])}</td><td>{h(item.get('last_error', ''))}</td></tr>"
        for item in queue["recent_jobs"]
    ) or '<tr><td colspan="5">Chưa có job.</td></tr>'
    notification_rows = "\n".join(
        f"<tr><td>{h(item['id'])}</td><td>{h(item['level'])}</td><td>{h(item['title'])}</td><td>{h(item['message'])}</td><td>{'Đã đọc' if item['is_read'] else 'Chưa đọc'}</td></tr>"
        for item in notifications
    ) or '<tr><td colspan="5">Chưa có notification.</td></tr>'
    email_rows = "\n".join(
        f"<tr><td>{h(item['id'])}</td><td>{h(item['recipient'])}</td><td>{h(item['subject'])}</td><td>{h(item['created_at'])}</td></tr>"
        for item in emails
    ) or '<tr><td colspan="4">Chưa có email outbox.</td></tr>'
    log_html = "\n".join(h(line) for line in log_lines) or "Chưa có log."
    ai_result_html = (
        f'<div class="admin-message success"><strong>Developer AI trả lời:</strong><br>{h(ai_result)}</div>'
        if ai_result
        else ""
    )
    content = f"""
      {render_admin_message(message, error)}
      {ai_result_html}
      <div class="admin-stats-grid">
        <article><span>Health</span><strong>{h(health["status"])}</strong><p>Database: {h(health["database"])}</p></article>
        <article><span>API Version</span><strong>{h(API_VERSION)}</strong><p>OpenAPI: /api/openapi.json</p></article>
        <article><span>Environment</span><strong>{h(health["environment"])}</strong><p>Redis: {h(health["redis_enabled"])}</p></article>
        <article><span>Queue</span><strong>{h(queue["counts"].get("pending", 0))}</strong><p>Pending jobs</p></article>
      </div>
      <form class="admin-form" method="post" action="/admin/developer/ai-code">
        <h2>Developer AI</h2>
        <p class="form-hint">Dùng để hỏi AI giải thích code, đọc lỗi, gợi ý cách debug hoặc viết ví dụ nhỏ. AI chỉ trả lời gợi ý, không tự sửa file.</p>
        <label>Câu hỏi<textarea name="question" rows="4" required>{h(ai_form.get("question", ""))}</textarea></label>
        <label>Ngôn ngữ/khu vực code<input name="language" value="{h(ai_form.get("language", "Python/HTML/CSS/SQL"))}" /></label>
        <label>Code hoặc log liên quan<textarea name="code_context" rows="8" placeholder="Dán lỗi Python, SQL, đoạn app.py, hoặc log cần phân tích...">{h(ai_form.get("code_context", ""))}</textarea></label>
        <label>Model<input name="model" value="{h(ai_form.get("model", OLLAMA_MODEL))}" /></label>
        <button class="btn btn-primary" type="submit">Hỏi Developer AI</button>
      </form>
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/developer/demo-event">
          <h2>Demo Event</h2>
          <p class="form-hint">Tạo event contact.created, tự sinh job email + notification.</p>
          <button class="btn btn-primary" type="submit">Create demo event</button>
        </form>
        <form class="admin-form" method="post" action="/admin/developer/run-worker">
          <h2>Run Queue</h2>
          <p class="form-hint">Chạy worker một lần để xử lý các job pending.</p>
          <button class="btn btn-primary" type="submit">Run worker now</button>
        </form>
        <form class="admin-form" method="post" action="/admin/developer/cache-clear">
          <h2>Cache Clear</h2>
          <p class="form-hint">Xóa cache runtime như Redis key api:home.</p>
          <button class="btn btn-primary" type="submit">Clear cache</button>
        </form>
        <form class="admin-form" method="post" action="/admin/developer/migrate">
          <h2>Migration</h2>
          <p class="form-hint">Chạy lại migration để đảm bảo database đủ bảng/cột mới.</p>
          <button class="btn btn-primary" type="submit">Run migration</button>
        </form>
        <form class="admin-form" method="post" action="/admin/developer/backup">
          <h2>Backup Database</h2>
          <p class="form-hint">Tạo bản sao SQLite trong thư mục backups.</p>
          <button class="btn btn-primary" type="submit">Create backup</button>
        </form>
        <form class="admin-form" method="post" action="/admin/developer/demo-backup-job">
          <h2>Backup Job</h2>
          <p class="form-hint">Đưa job backup vào queue, sau đó bấm Run worker.</p>
          <button class="btn btn-secondary" type="submit">Queue backup job</button>
        </form>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>ID</th><th>Event</th><th>Entity</th><th>Created</th></tr></thead><tbody>{event_rows}</tbody></table>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>ID</th><th>Job Type</th><th>Status</th><th>Attempts</th><th>Error</th></tr></thead><tbody>{job_rows}</tbody></table>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>ID</th><th>Level</th><th>Title</th><th>Message</th><th>Read</th></tr></thead><tbody>{notification_rows}</tbody></table>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>ID</th><th>Recipient</th><th>Subject</th><th>Created</th></tr></thead><tbody>{email_rows}</tbody></table>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>Key</th><th>Value</th></tr></thead><tbody>{info_rows}</tbody></table>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table"><thead><tr><th>Backup</th><th>Size</th><th>Modified</th></tr></thead><tbody>{backup_rows}</tbody></table>
      </div>
      <pre class="log-viewer">{log_html}</pre>
    """
    return render_admin_shell("Developer Tools", "developer", admin_user, content)


def render_admin_ai_page(admin_user, form=None, answer="", error="", translation_result="", translation_form=None, ops_result="", ops_form=None):
    """Render trang AI trong Admin: hỏi Ollama và xem lịch sử."""
    form = form or {}
    translation_form = translation_form or {}
    ops_form = ops_form or {}
    # status cho admin biết backend đang gọi provider nào, model nào, URL Ollama nào.
    status = get_ai_status()
    # messages là lịch sử hỏi đáp đã lưu trong bảng ai_conversations.
    messages = get_recent_ai_messages(12)
    rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["created_at"])}</td>
          <td>{h(item["channel"])}</td>
          <td>{h(item["model"])}</td>
          <td>{h(item["status"])}</td>
          <td>{h(item["user_message"])}</td>
          <td>{h(item["assistant_message"])}</td>
        </tr>
        """
        for item in messages
    ) or '<tr><td colspan="6">Chưa có lịch sử AI.</td></tr>'
    answer_html = f'<div class="admin-message success"><strong>AI trả lời:</strong>{format_ai_result_html(answer)}</div>' if answer else ""
    translation_html = (
        f'<div class="admin-message success"><strong>Bản dịch AI:</strong>{format_ai_result_html(translation_result)}</div>'
        if translation_result
        else ""
    )
    ops_html = (
        f'<div class="admin-message success"><strong>AI vận hành trả lời:</strong>{format_ai_result_html(ops_result)}</div>'
        if ops_result
        else ""
    )
    content = f"""
      {render_admin_message("", error)}
      {answer_html}
      {translation_html}
      {ops_html}
      <div class="admin-stats-grid">
        <article><span>Provider</span><strong>{h(status["provider"])}</strong><p>Local AI service</p></article>
        <article><span>Model</span><strong>{h(status["model"])}</strong><p>Đổi bằng MEC_OLLAMA_MODEL</p></article>
        <article><span>Ollama URL</span><strong>{h(status["ollama_url"])}</strong><p>Máy local hoặc AI server riêng</p></article>
        <article><span>Timeout</span><strong>{h(status["timeout_seconds"])}s</strong><p>Nếu Ollama tắt sẽ dùng fallback demo</p></article>
      </div>
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/ai/ask">
          <h2>AI Assistant</h2>
          <label>Câu hỏi<textarea name="message" rows="7" required>{h(form.get("message", ""))}</textarea></label>
          <label>Model<input name="model" value="{h(form.get("model", status["model"]))}" /></label>
          <p class="form-hint">Ví dụ: hỏi AI phân tích khách hàng, gợi ý SEO sản phẩm, hoặc soạn nội dung mô tả kỹ thuật.</p>
          <button class="btn btn-primary" type="submit">Hỏi AI</button>
        </form>
        <div class="admin-form">
          <h2>Ví dụ câu hỏi</h2>
          <p>Viết mô tả SEO cho sản phẩm trục CNC chính xác cao.</p>
          <p>Khách hàng hỏi báo giá fixture, cần thu thập thông tin gì?</p>
          <p>Tóm tắt năng lực sản xuất của MecPrecision trong 5 ý.</p>
          <p>Gợi ý email phản hồi khách hàng gửi bản vẽ STEP.</p>
        </div>
      </div>
      <form class="admin-form" method="post" action="/admin/ai/translate">
        <h2>AI dịch đa ngôn ngữ</h2>
        <p class="form-hint">Dịch nội dung sản phẩm, tin tức hoặc email kỹ thuật. AI sẽ cố giữ nguyên mã sản phẩm, đơn vị, URL và thuật ngữ CNC.</p>
        <label>Nội dung cần dịch<textarea name="source_text" rows="7" required>{h(translation_form.get("source_text", ""))}</textarea></label>
        <div class="form-grid">
          <label>Ngôn ngữ nguồn<input name="source_language" value="{h(translation_form.get("source_language", "Tự động nhận diện"))}" /></label>
          <label>Ngôn ngữ đích<input name="target_language" value="{h(translation_form.get("target_language", "English"))}" required /></label>
        </div>
        <div class="form-grid">
          <label>Giọng văn<input name="tone" value="{h(translation_form.get("tone", "chuyên nghiệp, dễ hiểu"))}" /></label>
          <label>Model<input name="model" value="{h(translation_form.get("model", status["model"]))}" /></label>
        </div>
        <button class="btn btn-primary" type="submit">Dịch bằng AI</button>
      </form>
      <div class="admin-module-grid">
        <form class="admin-form" method="post" action="/admin/ai/contacts-summary">
          <h2>AI tóm tắt liên hệ mới</h2>
          <p class="form-hint">Đọc các liên hệ gần nhất và gợi ý khách nào cần xử lý trước.</p>
          <label>Số liên hệ<input type="number" name="limit" value="{h(ops_form.get("limit", "8"))}" min="1" max="20" /></label>
          <label>Model<input name="model" value="{h(ops_form.get("model", status["model"]))}" /></label>
          <button class="btn btn-primary" type="submit">Tóm tắt liên hệ</button>
        </form>
        <form class="admin-form" method="post" action="/admin/ai/quote-analysis">
          <h2>AI phân tích báo giá</h2>
          <p class="form-hint">Nhập ID báo giá hoặc để trống để phân tích yêu cầu mới nhất.</p>
          <label>Quote ID<input name="quote_id" value="{h(ops_form.get("quote_id", ""))}" placeholder="Ví dụ: 15" /></label>
          <label>Model<input name="model" value="{h(ops_form.get("model", status["model"]))}" /></label>
          <button class="btn btn-primary" type="submit">Phân tích báo giá</button>
        </form>
        <form class="admin-form" method="post" action="/admin/ai/smart-search">
          <h2>AI tìm kiếm thông minh</h2>
          <p class="form-hint">Tìm trong sản phẩm/tin tức rồi nhờ AI tóm tắt kết quả phù hợp.</p>
          <label>Câu hỏi / từ khóa<input name="query" value="{h(ops_form.get("query", ""))}" placeholder="trục CNC chính xác, đồ gá nhôm..." required /></label>
          <label>Phạm vi<select name="scope">
            <option value="all" {"selected" if ops_form.get("scope", "all") == "all" else ""}>Sản phẩm + Tin tức</option>
            <option value="products" {"selected" if ops_form.get("scope") == "products" else ""}>Chỉ sản phẩm</option>
            <option value="news" {"selected" if ops_form.get("scope") == "news" else ""}>Chỉ tin tức</option>
          </select></label>
          <label>Model<input name="model" value="{h(ops_form.get("model", status["model"]))}" /></label>
          <button class="btn btn-primary" type="submit">Tìm bằng AI</button>
        </form>
        <form class="admin-form" method="post" action="/admin/ai/dashboard-insights">
          <h2>AI Dashboard</h2>
          <p class="form-hint">Trả lời câu hỏi: Hôm nay website có gì cần chú ý?</p>
          <label>Model<input name="model" value="{h(ops_form.get("model", status["model"]))}" /></label>
          <button class="btn btn-primary" type="submit">Xem AI dashboard</button>
        </form>
      </div>
      <form class="admin-form" method="post" action="/admin/ai/document-read" enctype="multipart/form-data">
        <h2>AI đọc PDF / catalogue / tài liệu</h2>
        <p class="form-hint">Upload PDF có text, TXT, MD hoặc CSV. PDF scan ảnh cần OCR nâng cao nên demo này có thể chưa đọc được.</p>
        <label>Câu hỏi về tài liệu<input name="question" value="{h(ops_form.get("question", "Tóm tắt tài liệu này và chỉ ra thông tin kỹ thuật quan trọng."))}" /></label>
        <label>File tài liệu<input type="file" name="document_file" accept=".pdf,.txt,.md,.csv" required /></label>
        <label>Model<input name="model" value="{h(ops_form.get("model", status["model"]))}" /></label>
        <button class="btn btn-primary" type="submit">Đọc tài liệu bằng AI</button>
      </form>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead><tr><th>Thời gian</th><th>Kênh</th><th>Model</th><th>Status</th><th>Câu hỏi</th><th>Trả lời</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    """
    return render_admin_shell("AI Assistant", "ai", admin_user, content)


def render_bar_chart(title, chart_items):
    """Render biểu đồ cột đơn giản bằng HTML/CSS."""
    max_value = max([item["total"] for item in chart_items] or [1]) or 1
    bars = "\n".join(
        f"""
        <div class="dashboard-bar-item">
          <div class="dashboard-bar-track">
            <span style="height: {max(6, int(item["total"] / max_value * 100))}%"></span>
          </div>
          <strong>{h(item["total"])}</strong>
          <small>{h(item["label"][-5:])}</small>
        </div>
        """
        for item in chart_items
    )
    return f"""
      <article class="dashboard-chart">
        <h3>{h(title)}</h3>
        <div class="dashboard-bars">{bars}</div>
      </article>
    """


def render_admin_dashboard(admin_user):
    """Render dashboard quản trị sau khi đăng nhập."""
    # Dashboard chỉ được render nếu get_current_admin() tìm thấy session hợp lệ.
    dashboard = get_dashboard_stats()
    stats = dashboard["counts"]
    charts = dashboard["charts"]
    contacts = get_recent_contact_requests()
    contact_rows = "\n".join(
        f"""
        <tr>
          <td>{h(item["id"])}</td>
          <td>{h(item["name"])}</td>
          <td>{h(item["contact"])}</td>
          <td>{h(item["message"])}</td>
          <td>{h(item["status"])}</td>
          <td>{h(item["created_at"])}</td>
        </tr>
        """
        for item in contacts
    )
    if not contact_rows:
        contact_rows = '<tr><td colspan="6">Chưa có yêu cầu liên hệ.</td></tr>'

    content = f"""
      <div class="info-grid admin-stats-grid">
        <article><h3>{stats["products"]}</h3><p>Sản phẩm</p></article>
        <article><h3>{stats["news"]}</h3><p>Bài tin tức</p></article>
        <article><h3>{stats["customers"]}</h3><p>Khách hàng</p></article>
        <article><h3>{stats["quotes"]}</h3><p>Yêu cầu báo giá</p></article>
        <article><h3>{stats["new_contacts"]}</h3><p>Liên hệ mới</p></article>
        <article><h3>{stats["online_users"]}</h3><p>Người online</p></article>
        <article><h3>{stats["visits"]}</h3><p>Lượt truy cập</p></article>
      </div>
      <div class="section-heading compact-heading">
        <div>
          <p class="eyebrow">Biểu đồ</p>
          <h2>Lượt truy cập website</h2>
        </div>
      </div>
      <div class="dashboard-chart-grid">
        {render_bar_chart("7 ngày", charts["7_days"])}
        {render_bar_chart("30 ngày", charts["30_days"])}
        {render_bar_chart("12 tháng", charts["12_months"])}
      </div>
      <div class="section-heading compact-heading">
        <div>
          <p class="eyebrow">Liên hệ mới</p>
          <h2>Yêu cầu từ khách hàng</h2>
        </div>
        <a class="text-link" href="/admin/contacts">Xem tất cả</a>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Họ tên</th>
              <th>Liên hệ</th>
              <th>Nội dung</th>
              <th>Trạng thái</th>
              <th>Ngày tạo</th>
            </tr>
          </thead>
          <tbody>{contact_rows}</tbody>
        </table>
      </div>
    """
    return render_admin_shell("Dashboard", "dashboard", admin_user, content)


class MecPrecisionHandler(BaseHTTPRequestHandler):
    """HTTP handler: render web động, trả API JSON và phục vụ static assets."""

    def do_GET(self):
        self.handle_request(self.handle_GET)

    def do_POST(self):
        self.handle_request(self.handle_POST)

    def do_PUT(self):
        self.handle_request(self.handle_PUT)

    def do_DELETE(self):
        self.handle_request(self.handle_DELETE)

    def handle_request(self, action):
        """Exception handler chung cho mọi request."""
        # Mọi method GET/POST/PUT/DELETE đều đi qua đây.
        # Nhờ vậy lỗi API trả về cùng một format thay vì 500 mặc định khó đọc.
        handle_request_exception(self, action, LOGGER, debug=DEBUG)

    def handle_GET(self):
        # do_GET xử lý các request đọc dữ liệu/trang, ví dụ mở /, /admin, /api/home.
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/admin/login":
            # Nếu đã đăng nhập rồi mà vào login, chuyển thẳng đến dashboard.
            if self.get_current_admin():
                self.redirect("/admin")
                return
            self.send_html(render_admin_login_page())
            return

        if path == "/admin/forgot-password":
            self.send_html(render_forgot_password_page())
            return

        if path == "/admin/reset-password":
            params = {key: values[0] if values else "" for key, values in parse_qs(parsed_url.query).items()}
            self.send_html(render_reset_password_page(params.get("token", "")))
            return

        if path == "/admin/2fa":
            params = {key: values[0] if values else "" for key, values in parse_qs(parsed_url.query).items()}
            self.send_html(render_two_factor_page(params.get("challenge_id", "")))
            return

        if path == "/admin":
            # /admin là trang riêng tư, bắt buộc phải có session đăng nhập.
            admin_user = self.get_current_admin()
            if not admin_user:
                self.redirect("/admin/login")
                return
            if not has_admin_permission(admin_user, "dashboard", "read"):
                self.send_html(render_admin_login_page("Bạn không có quyền truy cập khu vực quản trị."), status=403)
                return
            self.send_html(render_admin_dashboard(admin_user))
            return

        if path == "/admin/logout":
            current_admin = self.get_current_admin()
            if current_admin:
                log_admin_activity(current_admin, "auth.logout", "admin_user", current_admin["admin_id"], "Đăng xuất CMS", self.client_address[0] if self.client_address else "")
            self.logout_current_session()
            self.redirect("/admin/login")
            return

        if path.startswith("/admin/"):
            admin_user = self.get_current_admin()
            if not admin_user:
                self.redirect("/admin/login")
                return

            params = {key: values[0] if values else "" for key, values in parse_qs(parsed_url.query).items()}
            if path == "/admin/products":
                if not has_admin_permission(admin_user, "products", "read"):
                    self.send_json({"error": "Bạn không có quyền xem sản phẩm."}, status=403)
                    return
                self.send_html(render_admin_products_page(admin_user, params))
                return
            product_edit_id = parse_admin_item_path(path, "products", "edit")
            if product_edit_id:
                if not has_admin_permission(admin_user, "products", "read"):
                    self.send_json({"error": "Bạn không có quyền xem sản phẩm."}, status=403)
                    return
                self.send_html(render_admin_products_page(admin_user, params, get_product_record(product_edit_id)))
                return

            if path == "/admin/categories":
                if not has_admin_permission(admin_user, "categories", "read"):
                    self.send_json({"error": "Bạn không có quyền xem danh mục."}, status=403)
                    return
                self.send_html(render_admin_categories_page(admin_user, params))
                return
            category_edit_id = parse_admin_item_path(path, "categories", "edit")
            if category_edit_id:
                if not has_admin_permission(admin_user, "categories", "read"):
                    self.send_json({"error": "Bạn không có quyền xem danh mục."}, status=403)
                    return
                self.send_html(render_admin_categories_page(admin_user, params, get_category_record(category_edit_id)))
                return

            if path == "/admin/news":
                if not has_admin_permission(admin_user, "news", "read"):
                    self.send_json({"error": "Bạn không có quyền xem tin tức."}, status=403)
                    return
                self.send_html(render_admin_news_page(admin_user, params))
                return
            news_edit_id = parse_admin_item_path(path, "news", "edit")
            if news_edit_id:
                if not has_admin_permission(admin_user, "news", "read"):
                    self.send_json({"error": "Bạn không có quyền xem tin tức."}, status=403)
                    return
                self.send_html(render_admin_news_page(admin_user, params, get_news_record(news_edit_id)))
                return

            if path == "/admin/media":
                if not has_admin_permission(admin_user, "media", "read"):
                    self.send_json({"error": "Bạn không có quyền xem media."}, status=403)
                    return
                self.send_html(render_admin_media_page(admin_user, params))
                return

            if path == "/admin/pages":
                if not has_admin_permission(admin_user, "pages", "read"):
                    self.send_json({"error": "Bạn không có quyền xem pages."}, status=403)
                    return
                self.send_html(render_admin_pages_page(admin_user, params))
                return
            page_edit_id = parse_admin_item_path(path, "pages", "edit")
            if page_edit_id:
                if not has_admin_permission(admin_user, "pages", "read"):
                    self.send_json({"error": "Bạn không có quyền xem pages."}, status=403)
                    return
                self.send_html(render_admin_pages_page(admin_user, params, get_page_record(page_edit_id)))
                return

            if path == "/admin/menus":
                if not has_admin_permission(admin_user, "menus", "read"):
                    self.send_json({"error": "Bạn không có quyền xem menu."}, status=403)
                    return
                self.send_html(render_admin_menus_page(admin_user))
                return
            menu_edit_id = parse_admin_item_path(path, "menus", "edit")
            if menu_edit_id:
                if not has_admin_permission(admin_user, "menus", "read"):
                    self.send_json({"error": "Bạn không có quyền xem menu."}, status=403)
                    return
                self.send_html(render_admin_menus_page(admin_user, get_menu_record(menu_edit_id)))
                return

            if path == "/admin/banners":
                if not has_admin_permission(admin_user, "banners", "read"):
                    self.send_json({"error": "Bạn không có quyền xem banner."}, status=403)
                    return
                self.send_html(render_admin_banners_page(admin_user, params))
                return
            banner_edit_id = parse_admin_item_path(path, "banners", "edit")
            if banner_edit_id:
                if not has_admin_permission(admin_user, "banners", "read"):
                    self.send_json({"error": "Bạn không có quyền xem banner."}, status=403)
                    return
                self.send_html(render_admin_banners_page(admin_user, params, get_banner_record(banner_edit_id)))
                return

            if path == "/admin/contacts":
                if not has_admin_permission(admin_user, "contacts", "read"):
                    self.send_json({"error": "Bạn không có quyền xem liên hệ."}, status=403)
                    return
                self.send_html(render_admin_contacts_page(admin_user, params))
                return
            if path == "/admin/contacts/export":
                if not has_admin_permission(admin_user, "contacts", "read"):
                    self.send_json({"error": "Bạn không có quyền export liên hệ."}, status=403)
                    return
                self.send_csv(
                    "contacts.csv",
                    get_contacts_csv_rows(),
                    ["id", "name", "company", "phone", "email", "country", "interested_product", "attachment_url", "contact", "message", "status", "is_read", "note", "created_at"],
                )
                return
            contact_edit_id = parse_admin_item_path(path, "contacts", "edit")
            if contact_edit_id:
                if not has_admin_permission(admin_user, "contacts", "read"):
                    self.send_json({"error": "Bạn không có quyền xem liên hệ."}, status=403)
                    return
                self.send_html(render_admin_contacts_page(admin_user, params, get_contact_record(contact_edit_id)))
                return

            if path == "/admin/users":
                if not has_admin_permission(admin_user, "users", "read"):
                    self.send_json({"error": "Bạn không có quyền xem người dùng."}, status=403)
                    return
                self.send_html(render_admin_users_page(admin_user, params))
                return
            user_edit_id = parse_admin_item_path(path, "users", "edit")
            if user_edit_id:
                if not has_admin_permission(admin_user, "users", "read"):
                    self.send_json({"error": "Bạn không có quyền xem người dùng."}, status=403)
                    return
                self.send_html(render_admin_users_page(admin_user, params, get_user_record(user_edit_id)))
                return

            if path == "/admin/settings":
                if not has_admin_permission(admin_user, "settings", "read"):
                    self.send_json({"error": "Bạn không có quyền xem cài đặt."}, status=403)
                    return
                self.send_html(render_admin_settings_page(admin_user))
                return

            if path == "/admin/developer":
                if not has_admin_permission(admin_user, "developer", "read"):
                    self.send_json({"error": "Bạn không có quyền xem Developer Tools."}, status=403)
                    return
                self.send_html(render_admin_developer_page(admin_user))
                return

            if path == "/admin/ai":
                if not has_admin_permission(admin_user, "ai", "read"):
                    self.send_json({"error": "Bạn không có quyền xem AI."}, status=403)
                    return
                self.send_html(render_admin_ai_page(admin_user))
                return

            if path == "/admin/account":
                self.send_html(render_admin_account_page(admin_user))
                return

            if path == "/admin/quotes":
                if not has_admin_permission(admin_user, "quotes", "read"):
                    self.send_json({"error": "Bạn không có quyền xem báo giá."}, status=403)
                    return
                self.send_html(render_admin_quotes_page(admin_user, params))
                return
            quote_edit_id = parse_admin_item_path(path, "quotes", "edit")
            if quote_edit_id:
                if not has_admin_permission(admin_user, "quotes", "read"):
                    self.send_json({"error": "Bạn không có quyền xem báo giá."}, status=403)
                    return
                self.send_html(render_admin_quotes_page(admin_user, params, get_quote_record(quote_edit_id)))
                return

            if path == "/admin/customers":
                if not has_admin_permission(admin_user, "customers", "read"):
                    self.send_json({"error": "Bạn không có quyền xem khách hàng."}, status=403)
                    return
                self.send_html(render_admin_customers_page(admin_user, params))
                return
            customer_edit_id = parse_admin_item_path(path, "customers", "edit")
            if customer_edit_id:
                if not has_admin_permission(admin_user, "customers", "read"):
                    self.send_json({"error": "Bạn không có quyền xem khách hàng."}, status=403)
                    return
                self.send_html(render_admin_customers_page(admin_user, params, get_customer_record(customer_edit_id)))
                return

            if path == "/admin/newsletter":
                if not has_admin_permission(admin_user, "newsletter", "read"):
                    self.send_json({"error": "Bạn không có quyền xem newsletter."}, status=403)
                    return
                self.send_html(render_admin_newsletter_page(admin_user, params))
                return
            newsletter_edit_id = parse_admin_item_path(path, "newsletter", "edit")
            if newsletter_edit_id:
                if not has_admin_permission(admin_user, "newsletter", "read"):
                    self.send_json({"error": "Bạn không có quyền xem newsletter."}, status=403)
                    return
                self.send_html(render_admin_newsletter_page(admin_user, params, get_newsletter_record(newsletter_edit_id)))
                return

            if path == "/admin/newsletter/export":
                if not has_admin_permission(admin_user, "newsletter", "read"):
                    self.send_json({"error": "Bạn không có quyền export newsletter."}, status=403)
                    return
                self.send_csv("newsletter.csv", get_newsletter_csv_rows(), ["email", "status", "subscribed_at", "unsubscribed_at"])
                return

        dynamic_routes = {
            # Các route này được backend render HTML động từ database.
            "/": render_home_page,
            "/index.html": render_home_page,
            "/san-pham.html": render_products_page,
            "/san-pham": render_products_page,
            "/cong-nghe.html": render_technology_page,
            "/cong-nghe": render_technology_page,
            "/tin-tuc.html": render_news_page,
            "/tin-tuc": render_news_page,
            "/api-aws.html": render_api_aws_demo_page,
            "/api-aws": render_api_aws_demo_page,
            "/lien-he.html": render_contact_page,
            "/lien-he": render_contact_page,
        }

        public_params = {key: values[0] if values else "" for key, values in parse_qs(parsed_url.query).items()}
        public_language = normalize_language(public_params.get("lang"))

        if path in dynamic_routes:
            track_page_visit(path, self.client_address[0] if self.client_address else "", self.headers.get("User-Agent", ""))
            self.send_html(dynamic_routes[path](public_language))
            return

        # Trang động tạo trong CMS có URL dạng /about, /privacy, /career...
        # Điều kiện "." not in path tránh nhầm với file tĩnh như /css/styles.css.
        if path.startswith("/") and "." not in path and len(path.strip("/")) > 0:
            cms_page = get_public_page_by_slug(path.strip("/"))
            if cms_page:
                track_page_visit(path, self.client_address[0] if self.client_address else "", self.headers.get("User-Agent", ""))
                self.send_html(render_dynamic_cms_page(cms_page, public_language))
                return

        if path == "/api/home":
            # API trả JSON, dùng cho frontend hoặc hệ thống khác gọi dữ liệu.
            self.send_controller_response(get_home_response())
            return

        if path == "/api/products":
            self.send_controller_response(list_products_response())
            return

        product_id = parse_product_api_id(path)
        if product_id is not None:
            self.send_controller_response(get_product_response(product_id))
            return

        if path == "/api/product-categories":
            self.send_controller_response(list_product_categories_response())
            return

        if path == "/api/capabilities":
            self.send_controller_response(list_capabilities_response())
            return

        if path == "/api/news":
            self.send_controller_response(list_news_response())
            return

        if path == "/api/openapi.json":
            self.send_controller_response(openapi_response())
            return

        if path == "/api/health":
            self.send_json(get_health_status())
            return

        if path == "/api/version":
            self.send_json({"version": API_VERSION})
            return

        if path == "/api/docs":
            self.send_html(render_api_docs_page())
            return

        if path == "/api/aws-demo":
            # Endpoint demo để trang API & AWS gọi thử bằng fetch trong app.js.
            self.send_json(get_api_aws_demo_data())
            return

        if path == "/api/external/weather":
            # Endpoint local này gọi tiếp API bên ngoài Open-Meteo rồi trả kết quả về frontend.
            self.send_json(get_external_weather_data())
            return

        if path.startswith("/api/"):
            self.send_error_response("API không tồn tại.", status=404, code="API_NOT_FOUND")
            return

        if path.startswith("/uploads/"):
            self.serve_upload_file(path)
            return

        self.serve_static_file(path)

    def handle_POST(self):
        # do_POST xử lý các request gửi dữ liệu, ví dụ login và form liên hệ.
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/admin/forgot-password":
            form = self.read_form_body()
            try:
                reset_link = request_password_reset(form.get("email"), self.get_base_url())
                message = "Nếu email hợp lệ, hệ thống đã tạo link reset mật khẩu trong email outbox demo."
                self.send_html(render_forgot_password_page(message=message, reset_link=reset_link or ""))
            except ValueError as error:
                self.send_html(render_forgot_password_page(error=str(error)), status=400)
            return

        if parsed_url.path == "/admin/reset-password":
            form = self.read_form_body()
            try:
                reset_password_with_token(form.get("token"), form.get("password"))
                self.send_html(render_reset_password_page(message="Đã đặt lại mật khẩu. Vui lòng đăng nhập lại."))
            except ValueError as error:
                self.send_html(render_reset_password_page(form.get("token", ""), error=str(error)), status=400)
            return

        if parsed_url.path == "/admin/login":
            # Form login gửi email/password dạng form-urlencoded.
            form = self.read_form_body()
            email = str(form.get("email", "")).strip()
            password = str(form.get("password", "")).strip()
            remote_addr = self.client_address[0] if self.client_address else ""
            settings = get_system_settings()

            if not is_ip_allowed(remote_addr, settings):
                self.send_html(render_admin_login_page("IP của bạn không nằm trong whitelist quản trị."), status=403)
                return

            if settings.get("captcha_enabled") == "1" and not verify_captcha(form.get("captcha_answer"), form.get("captcha_token")):
                self.send_html(render_admin_login_page("Captcha không đúng."), status=400)
                return

            if is_login_rate_limited(email, remote_addr):
                LOGGER.warning("Login rate limited for email=%s ip=%s", email, remote_addr)
                self.send_html(render_admin_login_page("Bạn đăng nhập sai quá nhiều lần. Vui lòng thử lại sau vài phút."), status=429)
                return

            admin_user = get_admin_by_email(email)

            if not admin_user or not verify_password(password, admin_user["password_hash"]):
                record_login_attempt(email, remote_addr, False)
                LOGGER.warning("Failed admin login for email=%s ip=%s", email, remote_addr)
                self.send_html(render_admin_login_page("Email hoặc mật khẩu không đúng."), status=401)
                return

            if password_hash_needs_upgrade(admin_user["password_hash"]):
                upgrade_admin_password_hash(admin_user["id"], password)

            record_login_attempt(email, remote_addr, True)
            if admin_user.get("two_factor_enabled"):
                challenge_id = create_two_factor_challenge(admin_user)
                self.redirect(f"/admin/2fa?challenge_id={challenge_id}")
                return

            remember_login = form.get("remember_login") == "1"
            session_ttl = get_session_ttl(remember_login)
            session_id = create_admin_session(
                admin_user,
                remote_addr=remote_addr,
                user_agent=self.headers.get("User-Agent", ""),
                ttl_seconds=session_ttl,
            )
            login_actor = {"admin_id": admin_user["id"], "full_name": admin_user["full_name"], "email": admin_user["email"]}
            log_admin_activity(login_actor, "auth.login", "admin_user", admin_user["id"], "Đăng nhập CMS", remote_addr)
            LOGGER.info("Admin login success for email=%s role=%s", admin_user["email"], admin_user["role"])
            self.redirect(
                "/admin",
                headers=[
                    (
                        "Set-Cookie",
                        f"{SESSION_COOKIE_NAME}={session_id}; HttpOnly; SameSite=Lax; Path=/; Max-Age={session_ttl}",
                    )
                ],
            )
            return

        if parsed_url.path == "/admin/2fa":
            form = self.read_form_body()
            try:
                admin_user = verify_two_factor_challenge(form.get("challenge_id"), form.get("code"))
                remote_addr = self.client_address[0] if self.client_address else ""
                session_id = create_admin_session(
                    admin_user,
                    remote_addr=remote_addr,
                    user_agent=self.headers.get("User-Agent", ""),
                )
                login_actor = {"admin_id": admin_user["id"], "full_name": admin_user["full_name"], "email": admin_user["email"]}
                log_admin_activity(login_actor, "auth.2fa_login", "admin_user", admin_user["id"], "Đăng nhập CMS bằng 2FA", remote_addr)
                self.redirect(
                    "/admin",
                    headers=[("Set-Cookie", f"{SESSION_COOKIE_NAME}={session_id}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_TTL_SECONDS}")],
                )
            except ValueError as error:
                self.send_html(render_two_factor_page(form.get("challenge_id", ""), str(error)), status=400)
            return

        if parsed_url.path.startswith("/admin/"):
            admin_user = self.get_current_admin()
            if not admin_user:
                self.redirect("/admin/login")
                return

            form, files = self.read_multipart_or_form_body()
            if not verify_csrf_token(admin_user.get("session_id"), form.get("csrf_token")):
                self.send_html(render_admin_dashboard(admin_user), status=403)
                print("CMS CSRF validation failed")
                return

            try:
                if parsed_url.path == "/admin/account/change-password":
                    change_password(admin_user["admin_id"], form.get("current_password"), form.get("new_password"))
                    log_admin_activity(admin_user, "auth.change_password", "admin_user", admin_user["admin_id"], "Đổi mật khẩu", self.client_address[0] if self.client_address else "")
                    self.redirect(
                        "/admin/login",
                        headers=[("Set-Cookie", f"{SESSION_COOKIE_NAME}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")],
                    )
                    return

                if parsed_url.path == "/admin/account/change-email":
                    old_email = admin_user["email"]
                    change_email(admin_user["admin_id"], form.get("password"), form.get("new_email"))
                    log_admin_activity(admin_user, "auth.change_email", "admin_user", admin_user["admin_id"], f"Đổi email từ {old_email} sang {form.get('new_email')}", self.client_address[0] if self.client_address else "")
                    self.redirect(
                        "/admin/login",
                        headers=[("Set-Cookie", f"{SESSION_COOKIE_NAME}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")],
                    )
                    return

                if parsed_url.path == "/admin/account/sessions/revoke":
                    target_session_id = str(form.get("session_id", "")).strip()
                    if target_session_id and target_session_id != admin_user.get("session_id"):
                        delete_admin_session_for_user(admin_user["admin_id"], target_session_id)
                        log_admin_activity(admin_user, "auth.revoke_session", "admin_session", target_session_id[:10], "Thu hồi session thiết bị khác", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/account")
                    return

                if parsed_url.path == "/admin/account/2fa":
                    enabled = parse_bool(form.get("two_factor_enabled"))
                    set_two_factor_enabled(admin_user["admin_id"], enabled)
                    log_admin_activity(admin_user, "auth.2fa_toggle", "admin_user", admin_user["admin_id"], f"{'Bật' if enabled else 'Tắt'} 2FA", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/account")
                    return

                if parsed_url.path == "/admin/developer/cache-clear":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền clear cache."}, status=403)
                        return
                    clear_runtime_cache()
                    log_admin_activity(admin_user, "developer.cache_clear", "system", "cache", "Clear runtime cache", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/developer")
                    return

                if parsed_url.path == "/admin/developer/migrate":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền chạy migration."}, status=403)
                        return
                    run_migrations()
                    log_admin_activity(admin_user, "developer.migrate", "system", "database", "Run migrations", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/developer")
                    return

                if parsed_url.path == "/admin/developer/backup":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền backup database."}, status=403)
                        return
                    backup_path = create_database_backup()
                    log_admin_activity(admin_user, "developer.backup", "database_backup", backup_path.name, f"Tạo backup {backup_path.name}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/developer")
                    return

                if parsed_url.path == "/admin/developer/demo-event":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền tạo demo event."}, status=403)
                        return
                    event_id = publish_event(
                        "contact.created",
                        "contact_request",
                        "demo",
                        {"name": "Demo Customer", "contact": "demo@mecprecision.vn"},
                    )
                    log_admin_activity(admin_user, "developer.demo_event", "enterprise_event", event_id, "Tạo demo event contact.created", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/developer")
                    return

                if parsed_url.path == "/admin/developer/run-worker":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền chạy queue."}, status=403)
                        return
                    results = process_pending_jobs(limit=20)
                    log_admin_activity(admin_user, "developer.run_worker", "job_queue", "batch", f"Worker processed {len(results)} jobs", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/developer")
                    return

                if parsed_url.path == "/admin/developer/demo-backup-job":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền tạo backup job."}, status=403)
                        return
                    event_id = publish_event("database.backup.requested", "database", "mecprecision.sqlite", {})
                    log_admin_activity(admin_user, "developer.queue_backup", "enterprise_event", event_id, "Đưa backup database vào queue", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/developer")
                    return

                if parsed_url.path == "/admin/developer/ai-code":
                    if not has_admin_permission(admin_user, "developer", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng Developer AI."}, status=403)
                        return
                    try:
                        result = ask_developer_ai(
                            form.get("question"),
                            code_context=form.get("code_context"),
                            language=form.get("language"),
                            model=form.get("model"),
                        )
                    except ValueError as error:
                        self.send_html(render_admin_developer_page(admin_user, error=str(error), ai_form=form))
                        return
                    log_admin_activity(admin_user, "developer.ai_code", "ai_conversation", result["id"], f"Developer AI bằng model {result['model']}", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_developer_page(admin_user, ai_result=result["answer"], ai_form=form))
                    return

                if parsed_url.path == "/admin/ai/ask":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI."}, status=403)
                        return
                    # Form Admin AI gửi câu hỏi vào đây.
                    # ask_ai sẽ gọi Ollama, lưu lịch sử, rồi trả câu trả lời để render lại trang.
                    result = ask_ai(form.get("message"), channel="admin", model=form.get("model"))
                    log_admin_activity(admin_user, "ai.ask", "ai_conversation", result["id"], f"Hỏi AI bằng model {result['model']}", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, form, answer=result["answer"]))
                    return

                if parsed_url.path == "/admin/ai/translate":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI dịch thuật."}, status=403)
                        return
                    try:
                        result = translate_text(
                            form.get("source_text"),
                            form.get("target_language"),
                            source_language=form.get("source_language"),
                            tone=form.get("tone"),
                            model=form.get("model"),
                        )
                    except ValueError as error:
                        self.send_html(render_admin_ai_page(admin_user, translation_form=form, error=str(error)))
                        return
                    log_admin_activity(admin_user, "ai.translate", "ai_conversation", result["id"], f"Dịch AI sang {form.get('target_language', '')}", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, translation_result=result["answer"], translation_form=form))
                    return

                if parsed_url.path == "/admin/ai/contacts-summary":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI tóm tắt liên hệ."}, status=403)
                        return
                    try:
                        result = summarize_recent_contacts(form.get("limit", 8), model=form.get("model"))
                    except ValueError as error:
                        self.send_html(render_admin_ai_page(admin_user, ops_form=form, error=str(error)))
                        return
                    log_admin_activity(admin_user, "ai.contacts_summary", "ai_conversation", result["id"], "AI tóm tắt liên hệ mới", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, ops_result=result["answer"], ops_form=form))
                    return

                if parsed_url.path == "/admin/ai/quote-analysis":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI phân tích báo giá."}, status=403)
                        return
                    try:
                        result = analyze_quote_request(form.get("quote_id"), model=form.get("model"))
                    except ValueError as error:
                        self.send_html(render_admin_ai_page(admin_user, ops_form=form, error=str(error)))
                        return
                    log_admin_activity(admin_user, "ai.quote_analysis", "ai_conversation", result["id"], f"AI phân tích báo giá {form.get('quote_id', '')}", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, ops_result=result["answer"], ops_form=form))
                    return

                if parsed_url.path == "/admin/ai/smart-search":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI tìm kiếm."}, status=403)
                        return
                    try:
                        result = smart_search_content(form.get("query"), scope=form.get("scope"), model=form.get("model"))
                    except ValueError as error:
                        self.send_html(render_admin_ai_page(admin_user, ops_form=form, error=str(error)))
                        return
                    log_admin_activity(admin_user, "ai.smart_search", "ai_conversation", result["id"], f"AI tìm kiếm {form.get('query', '')}", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, ops_result=result["answer"], ops_form=form))
                    return

                if parsed_url.path == "/admin/ai/dashboard-insights":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI dashboard."}, status=403)
                        return
                    result = generate_dashboard_insights(model=form.get("model"))
                    log_admin_activity(admin_user, "ai.dashboard_insights", "ai_conversation", result["id"], "AI dashboard hôm nay", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, ops_result=result["answer"], ops_form=form))
                    return

                if parsed_url.path == "/admin/ai/document-read":
                    if not has_admin_permission(admin_user, "ai", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI đọc tài liệu."}, status=403)
                        return
                    try:
                        result = analyze_uploaded_document(files.get("document_file"), question=form.get("question"), model=form.get("model"))
                    except ValueError as error:
                        self.send_html(render_admin_ai_page(admin_user, ops_form=form, error=str(error)))
                        return
                    log_admin_activity(admin_user, "ai.document_read", "ai_conversation", result["id"], "AI đọc tài liệu upload", self.client_address[0] if self.client_address else "")
                    self.send_html(render_admin_ai_page(admin_user, ops_result=result["answer"], ops_form=form))
                    return

                if parsed_url.path == "/admin/media/upload":
                    if not has_admin_permission(admin_user, "media", "write"):
                        self.send_json({"error": "Bạn không có quyền upload media."}, status=403)
                        return
                    folder = form.get("folder", "images")
                    uploaded_url = save_media_file(files.get("media_file"), folder)
                    log_admin_activity(admin_user, "media.upload", "media", uploaded_url, f"Upload media {uploaded_url}", self.client_address[0] if self.client_address else "")
                    self.redirect(f"/admin/media?{build_query_string({'folder': folder})}")
                    return

                if parsed_url.path == "/admin/media/folders/create":
                    if not has_admin_permission(admin_user, "media", "write"):
                        self.send_json({"error": "Bạn không có quyền tạo folder media."}, status=403)
                        return
                    folder = create_folder(form.get("folder"))
                    log_admin_activity(admin_user, "media.folder_create", "media_folder", folder, f"Tạo folder media {folder}", self.client_address[0] if self.client_address else "")
                    self.redirect(f"/admin/media?{build_query_string({'folder': folder})}")
                    return

                if parsed_url.path == "/admin/media/rename":
                    if not has_admin_permission(admin_user, "media", "write"):
                        self.send_json({"error": "Bạn không có quyền đổi tên media."}, status=403)
                        return
                    old_url = form.get("url", "")
                    new_url = rename_media(old_url, form.get("new_name"))
                    log_admin_activity(admin_user, "media.rename", "media", new_url, f"Đổi tên media từ {old_url} sang {new_url}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/media")
                    return

                if parsed_url.path == "/admin/media/delete":
                    if not has_admin_permission(admin_user, "media", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa media."}, status=403)
                        return
                    deleted_url = delete_media(form.get("url"))
                    log_admin_activity(admin_user, "media.delete", "media", deleted_url, f"Xóa media {deleted_url}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/media")
                    return

                if parsed_url.path == "/admin/products/ai-generate":
                    if not has_admin_permission(admin_user, "products", "write"):
                        self.send_json({"error": "Bạn không có quyền dùng AI cho sản phẩm."}, status=403)
                        return
                    category_id = parse_positive_int(form.get("category_id"), 0)
                    category_name = ""
                    for category in get_product_categories():
                        if category["id"] == category_id:
                            category_name = category["name"]
                            break
                    form["category_name"] = category_name
                    result = generate_product_content(form, model=form.get("ai_model"))
                    generated_fields = result["fields"]
                    # AI chỉ điền lại các field nội dung/SEO vào form, chưa lưu database.
                    for key, value in generated_fields.items():
                        form[key] = value
                    log_admin_activity(admin_user, "product.ai_generate", "ai_conversation", result["id"], f"AI tạo nội dung SEO cho {form.get('name', '')}", self.client_address[0] if self.client_address else "")
                    message = f"AI đã tạo gợi ý nội dung & SEO bằng model {result['model']} ({result['status']}). Kiểm tra lại rồi bấm Lưu sản phẩm."
                    self.send_html(render_admin_products_page(admin_user, {}, form, message=message))
                    return

                if parsed_url.path == "/admin/products/save":
                    if not has_admin_permission(admin_user, "products", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa sản phẩm."}, status=403)
                        return
                    uploaded_image = save_uploaded_file(files.get("image_file"), "images")
                    if uploaded_image:
                        form["main_image"] = uploaded_image
                    form["is_featured"] = form.get("is_featured", "0")
                    if form.get("save_mode") == "draft":
                        form["status"] = "draft"
                    product_id = parse_positive_int(form.get("id"), 0)
                    if product_id:
                        update_product(product_id, form)
                    else:
                        create_product(form)
                    self.redirect("/admin/products")
                    return

                product_delete_id = parse_admin_item_path(parsed_url.path, "products", "delete")
                if product_delete_id:
                    if not has_admin_permission(admin_user, "products", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa sản phẩm."}, status=403)
                        return
                    delete_product(product_delete_id)
                    self.redirect("/admin/products")
                    return

                if parsed_url.path == "/admin/categories/save":
                    if not has_admin_permission(admin_user, "categories", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa danh mục."}, status=403)
                        return
                    category_id = parse_positive_int(form.get("id"), 0)
                    save_category(form, category_id or None)
                    self.redirect("/admin/categories")
                    return

                category_delete_id = parse_admin_item_path(parsed_url.path, "categories", "delete")
                if category_delete_id:
                    if not has_admin_permission(admin_user, "categories", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa danh mục."}, status=403)
                        return
                    delete_category(category_delete_id)
                    self.redirect("/admin/categories")
                    return

                if parsed_url.path == "/admin/news/save":
                    if not has_admin_permission(admin_user, "news", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa tin tức."}, status=403)
                        return
                    uploaded_image = save_uploaded_file(files.get("image_file"), "images")
                    if uploaded_image:
                        form["image"] = uploaded_image
                    if form.get("save_mode") == "draft":
                        form["status"] = "draft"
                    news_id = parse_positive_int(form.get("id"), 0)
                    save_news(form, news_id or None)
                    self.redirect("/admin/news")
                    return

                news_delete_id = parse_admin_item_path(parsed_url.path, "news", "delete")
                if news_delete_id:
                    if not has_admin_permission(admin_user, "news", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa tin tức."}, status=403)
                        return
                    delete_news(news_delete_id)
                    self.redirect("/admin/news")
                    return

                if parsed_url.path == "/admin/contacts/save":
                    if not has_admin_permission(admin_user, "contacts", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa liên hệ."}, status=403)
                        return
                    form["is_read"] = form.get("is_read", "0")
                    contact_id = parse_positive_int(form.get("id"), 0)
                    save_contact(form, contact_id or None)
                    self.redirect("/admin/contacts")
                    return

                contact_delete_id = parse_admin_item_path(parsed_url.path, "contacts", "delete")
                if contact_delete_id:
                    if not has_admin_permission(admin_user, "contacts", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa liên hệ."}, status=403)
                        return
                    delete_contact(contact_delete_id)
                    self.redirect("/admin/contacts")
                    return

                if parsed_url.path == "/admin/pages/save":
                    if not has_admin_permission(admin_user, "pages", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa trang."}, status=403)
                        return
                    page_id = parse_positive_int(form.get("id"), 0)
                    saved_page = save_page(form, page_id or None)
                    log_admin_activity(admin_user, "page.save", "cms_page", saved_page["id"], f"Lưu trang {saved_page['title']}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/pages")
                    return

                page_delete_id = parse_admin_item_path(parsed_url.path, "pages", "delete")
                if page_delete_id:
                    if not has_admin_permission(admin_user, "pages", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa trang."}, status=403)
                        return
                    deleted_page = delete_page(page_delete_id)
                    log_admin_activity(admin_user, "page.delete", "cms_page", page_delete_id, f"Xóa trang {deleted_page['title'] if deleted_page else page_delete_id}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/pages")
                    return

                if parsed_url.path == "/admin/menus/save":
                    if not has_admin_permission(admin_user, "menus", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa menu."}, status=403)
                        return
                    menu_id = parse_positive_int(form.get("id"), 0)
                    saved_menu = save_menu_item(form, menu_id or None)
                    log_admin_activity(admin_user, "menu.save", "cms_menu_item", saved_menu["id"], f"Lưu menu {saved_menu['label']}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/menus")
                    return

                menu_delete_id = parse_admin_item_path(parsed_url.path, "menus", "delete")
                if menu_delete_id:
                    if not has_admin_permission(admin_user, "menus", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa menu."}, status=403)
                        return
                    deleted_menu = delete_menu_item(menu_delete_id)
                    log_admin_activity(admin_user, "menu.delete", "cms_menu_item", menu_delete_id, f"Xóa menu {deleted_menu['label'] if deleted_menu else menu_delete_id}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/menus")
                    return

                if parsed_url.path == "/admin/banners/save":
                    if not has_admin_permission(admin_user, "banners", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa banner."}, status=403)
                        return
                    uploaded_image = save_uploaded_file(files.get("image_file"), "images")
                    if uploaded_image:
                        form["image_url"] = uploaded_image
                    banner_id = parse_positive_int(form.get("id"), 0)
                    saved_banner = save_banner(form, banner_id or None)
                    log_admin_activity(admin_user, "banner.save", "cms_banner", saved_banner["id"], f"Lưu banner {saved_banner['title']}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/banners")
                    return

                banner_delete_id = parse_admin_item_path(parsed_url.path, "banners", "delete")
                if banner_delete_id:
                    if not has_admin_permission(admin_user, "banners", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa banner."}, status=403)
                        return
                    deleted_banner = delete_banner(banner_delete_id)
                    log_admin_activity(admin_user, "banner.delete", "cms_banner", banner_delete_id, f"Xóa banner {deleted_banner['title'] if deleted_banner else banner_delete_id}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/banners")
                    return

                if parsed_url.path == "/admin/quotes/save":
                    if not has_admin_permission(admin_user, "quotes", "write"):
                        self.send_json({"error": "Bạn không có quyền xử lý báo giá."}, status=403)
                        return
                    quote_id = parse_positive_int(form.get("id"), 0)
                    save_quote(form, quote_id)
                    log_admin_activity(admin_user, "quote.update", "quote_request", quote_id, f"Cập nhật yêu cầu báo giá #{quote_id}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/quotes")
                    return

                if parsed_url.path == "/admin/customers/save":
                    if not has_admin_permission(admin_user, "customers", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa khách hàng."}, status=403)
                        return
                    customer_id = parse_positive_int(form.get("id"), 0)
                    saved_customer = save_customer(form, customer_id or None)
                    log_admin_activity(admin_user, "customer.save", "customer", saved_customer["id"], f"Lưu khách hàng {saved_customer['contact_name']}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/customers")
                    return

                customer_note_id = parse_admin_item_path(parsed_url.path, "customers", "notes")
                if customer_note_id:
                    if not has_admin_permission(admin_user, "customers", "write"):
                        self.send_json({"error": "Bạn không có quyền thêm ghi chú khách hàng."}, status=403)
                        return
                    add_customer_note(customer_note_id, form.get("note"), admin_user["full_name"])
                    self.redirect(f"/admin/customers/{customer_note_id}/edit")
                    return

                customer_delete_id = parse_admin_item_path(parsed_url.path, "customers", "delete")
                if customer_delete_id:
                    if not has_admin_permission(admin_user, "customers", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa khách hàng."}, status=403)
                        return
                    deleted_customer = delete_customer(customer_delete_id)
                    log_admin_activity(admin_user, "customer.delete", "customer", customer_delete_id, f"Xóa khách hàng {deleted_customer['contact_name'] if deleted_customer else customer_delete_id}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/customers")
                    return

                if parsed_url.path == "/admin/newsletter/save":
                    if not has_admin_permission(admin_user, "newsletter", "write"):
                        self.send_json({"error": "Bạn không có quyền sửa newsletter."}, status=403)
                        return
                    subscriber_id = parse_positive_int(form.get("id"), 0)
                    saved_subscriber = save_newsletter(form, subscriber_id or None)
                    log_admin_activity(admin_user, "newsletter.save", "newsletter_subscriber", saved_subscriber["id"], f"Lưu newsletter {saved_subscriber['email']}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/newsletter")
                    return

                newsletter_delete_id = parse_admin_item_path(parsed_url.path, "newsletter", "delete")
                if newsletter_delete_id:
                    if not has_admin_permission(admin_user, "newsletter", "write"):
                        self.send_json({"error": "Bạn không có quyền xóa newsletter."}, status=403)
                        return
                    deleted_subscriber = delete_newsletter(newsletter_delete_id)
                    log_admin_activity(admin_user, "newsletter.delete", "newsletter_subscriber", newsletter_delete_id, f"Xóa newsletter {deleted_subscriber['email'] if deleted_subscriber else newsletter_delete_id}", self.client_address[0] if self.client_address else "")
                    self.redirect("/admin/newsletter")
                    return

                if parsed_url.path == "/admin/users/save":
                    if not has_admin_permission(admin_user, "users", "write"):
                        self.send_json({"error": "Chỉ Admin được quản lý người dùng."}, status=403)
                        return
                    uploaded_avatar = save_uploaded_file(files.get("avatar_file"), "avatars")
                    if uploaded_avatar:
                        form["avatar_url"] = uploaded_avatar
                    form["is_active"] = form.get("is_active", "0")
                    user_id = parse_positive_int(form.get("id"), 0)
                    if user_id == admin_user["admin_id"] and not parse_bool(form.get("is_active")):
                        self.send_html(render_admin_users_page(admin_user, {}, error="Không thể tự khóa tài khoản đang đăng nhập."), status=400)
                        return
                    saved_user = save_user(form, user_id or None)
                    log_admin_activity(
                        admin_user,
                        "user.update" if user_id else "user.create",
                        "admin_user",
                        saved_user["id"],
                        f"{'Cập nhật' if user_id else 'Tạo'} người dùng {saved_user['email']} với role {saved_user['role']}",
                        self.client_address[0] if self.client_address else "",
                    )
                    self.redirect("/admin/users")
                    return

                user_lock_id = parse_admin_item_path(parsed_url.path, "users", "lock")
                if user_lock_id:
                    if not has_admin_permission(admin_user, "users", "write"):
                        self.send_json({"error": "Chỉ Admin được khóa người dùng."}, status=403)
                        return
                    if user_lock_id == admin_user["admin_id"]:
                        self.send_html(render_admin_users_page(admin_user, {}, error="Không thể tự khóa tài khoản đang đăng nhập."), status=400)
                        return
                    locked_user = set_account_active(user_lock_id, False)
                    log_admin_activity(
                        admin_user,
                        "user.lock",
                        "admin_user",
                        user_lock_id,
                        f"Khóa tài khoản {locked_user['email'] if locked_user else user_lock_id}",
                        self.client_address[0] if self.client_address else "",
                    )
                    self.redirect("/admin/users")
                    return

                user_unlock_id = parse_admin_item_path(parsed_url.path, "users", "unlock")
                if user_unlock_id:
                    if not has_admin_permission(admin_user, "users", "write"):
                        self.send_json({"error": "Chỉ Admin được mở khóa người dùng."}, status=403)
                        return
                    unlocked_user = set_account_active(user_unlock_id, True)
                    log_admin_activity(
                        admin_user,
                        "user.unlock",
                        "admin_user",
                        user_unlock_id,
                        f"Mở khóa tài khoản {unlocked_user['email'] if unlocked_user else user_unlock_id}",
                        self.client_address[0] if self.client_address else "",
                    )
                    self.redirect("/admin/users")
                    return

                user_delete_id = parse_admin_item_path(parsed_url.path, "users", "delete")
                if user_delete_id:
                    if not has_admin_permission(admin_user, "users", "write"):
                        self.send_json({"error": "Chỉ Admin được xóa người dùng."}, status=403)
                        return
                    if user_delete_id == admin_user["admin_id"]:
                        self.send_html(render_admin_users_page(admin_user, {}, error="Không thể xóa chính tài khoản đang đăng nhập."), status=400)
                        return
                    deleted_user = delete_user(user_delete_id)
                    log_admin_activity(
                        admin_user,
                        "user.delete",
                        "admin_user",
                        user_delete_id,
                        f"Xóa người dùng {deleted_user['email'] if deleted_user else user_delete_id}",
                        self.client_address[0] if self.client_address else "",
                    )
                    self.redirect("/admin/users")
                    return

                if parsed_url.path == "/admin/settings/save":
                    if not has_admin_permission(admin_user, "settings", "write"):
                        self.send_json({"error": "Chỉ Admin được sửa cài đặt hệ thống."}, status=403)
                        return
                    save_system_settings(form)
                    self.redirect("/admin/settings")
                    return
            except ValueError as error:
                if parsed_url.path == "/admin/users/save":
                    self.send_html(render_admin_users_page(admin_user, {}, form, error=str(error)), status=400)
                    return
                if parsed_url.path.startswith("/admin/media"):
                    self.send_html(render_admin_media_page(admin_user, form, error=str(error)), status=400)
                    return
                self.send_html(render_admin_dashboard(admin_user), status=400)
                print(f"CMS validation error: {error}")
                return
            except sqlite3.IntegrityError as error:
                if parsed_url.path == "/admin/users/save":
                    self.send_html(render_admin_users_page(admin_user, {}, form, error="Email này đã tồn tại. Vui lòng dùng email khác."), status=409)
                    return
                self.send_html(render_admin_dashboard(admin_user), status=409)
                print(f"CMS database error: {error}")
                return

        if parsed_url.path == "/api/contact":
            # Form liên hệ từ frontend/js/app.js gửi JSON vào endpoint này.
            payload = self.read_json_body()
            self.send_controller_response(create_contact_response(payload))
            return

        if parsed_url.path == "/api/quote-request":
            payload = self.read_json_body()
            quote = create_public_quote_request(payload)
            publish_event(
                "quote.created",
                "quote_request",
                quote["id"],
                {"project_name": quote.get("project_name", f"Quote #{quote['id']}")},
            )
            self.send_json({"id": quote["id"], "message": "Đã tạo yêu cầu báo giá trong CMS."}, status=201)
            return

        if parsed_url.path == "/api/ai/chat":
            # API public cho chatbot hoặc frontend gọi bằng JSON.
            # Ví dụ body: {"message": "MecPrecision có gia công CNC không?"}
            payload = self.read_json_body()
            try:
                result = ask_ai(payload.get("message"), channel="public", model=payload.get("model"))
                self.send_json(result, status=200)
            except ValueError as error:
                self.send_json({"success": False, "error": {"code": "AI_VALIDATION_ERROR", "message": str(error)}}, status=400)
            return

        if parsed_url.path == "/api/products":
            # API thực tế: thêm sản phẩm mới vào bảng products bằng JSON.
            payload = self.read_json_body()
            self.send_controller_response(create_product_response(payload))
            return

        self.send_error_response("API không tồn tại.", status=404, code="API_NOT_FOUND")

    def handle_PUT(self):
        # do_PUT dùng để cập nhật tài nguyên đã có, ở đây là cập nhật sản phẩm.
        parsed_url = urlparse(self.path)
        product_id = parse_product_api_id(parsed_url.path)

        if product_id is None:
            self.send_error_response("API không tồn tại.", status=404, code="API_NOT_FOUND")
            return

        payload = self.read_json_body()
        self.send_controller_response(update_product_response(product_id, payload))

    def handle_DELETE(self):
        # do_DELETE dùng để xóa tài nguyên, ở đây là xóa sản phẩm theo id.
        parsed_url = urlparse(self.path)
        product_id = parse_product_api_id(parsed_url.path)

        if product_id is None:
            self.send_error_response("API không tồn tại.", status=404, code="API_NOT_FOUND")
            return

        self.send_controller_response(delete_product_response(product_id))

    def read_form_body(self):
        """Đọc dữ liệu form application/x-www-form-urlencoded."""
        # parse_qs đổi chuỗi "email=a&password=b" thành dictionary dễ dùng.
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        parsed = parse_qs(raw_body)
        return {key: values[0] if values else "" for key, values in parsed.items()}

    def read_multipart_or_form_body(self):
        """Đọc form admin, hỗ trợ cả form thường và form có upload file."""
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            return self.read_form_body(), {}

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            },
        )

        fields = {}
        files = {}
        for key in form.keys():
            item = form[key]
            if isinstance(item, list):
                item = item[0]
            if getattr(item, "filename", ""):
                files[key] = item
            else:
                fields[key] = item.value
        return fields, files

    def get_current_admin(self):
        """Lấy admin hiện tại từ session cookie."""
        # Trình duyệt tự gửi Cookie ở mỗi request sau khi đăng nhập.
        # Ta đọc cookie đó để biết người dùng đã đăng nhập hay chưa.
        cookie_header = self.headers.get("Cookie", "")
        cookies = {}
        for item in cookie_header.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                cookies[key] = value
        session_id = cookies.get(SESSION_COOKIE_NAME)
        session = get_admin_session(session_id)
        if not session:
            return None
        user_record = get_user_record(session["admin_id"]) or {}
        session.update(user_record)
        session["admin_id"] = session.get("admin_id") or user_record.get("id")
        session["session_id"] = session_id
        return session

    def logout_current_session(self):
        """Xóa session hiện tại khỏi bộ nhớ backend."""
        cookie_header = self.headers.get("Cookie", "")
        for item in cookie_header.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                if key == SESSION_COOKIE_NAME:
                    delete_admin_session(value)

    def get_base_url(self):
        """Lấy URL gốc hiện tại để tạo link reset mật khẩu."""
        host = self.headers.get("Host", f"{HOST}:{PORT}")
        return f"http://{host}"

    def redirect(self, location, headers=None):
        """Chuyển hướng trình duyệt sang URL khác."""
        # 302 là mã HTTP báo trình duyệt chuyển sang địa chỉ mới.
        self.send_response(302)
        self.send_header("Location", location)
        self.send_security_headers()
        for key, value in headers or []:
            self.send_header(key, value)
        self.end_headers()

    def send_security_headers(self):
        """Thêm HTTP security headers cơ bản cho mọi response."""
        apply_security_headers(self)

    def serve_static_file(self, path):
        """Trả file CSS/JS/ảnh từ thư mục dự án."""
        # Static file là file có sẵn trong frontend như CSS, JS, ảnh, font.
        requested_path = (FRONTEND_ROOT / path.lstrip("/")).resolve()

        # Kiểm tra an toàn: không cho request đọc file nằm ngoài thư mục frontend.
        if FRONTEND_ROOT not in requested_path.parents and requested_path != FRONTEND_ROOT:
            self.send_error(403)
            return

        if not requested_path.exists() or requested_path.is_dir():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(requested_path.name)[0] or "application/octet-stream"
        data = requested_path.read_bytes()
        should_compress = content_type.startswith(("text/", "application/javascript", "application/json"))
        if should_compress and "gzip" in self.headers.get("Accept-Encoding", ""):
            data = gzip.compress(data)
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        if should_compress and "gzip" in self.headers.get("Accept-Encoding", ""):
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(data)))
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(data)

    def serve_upload_file(self, path):
        """Trả file đã upload trong backend/uploads."""
        requested_path = (UPLOAD_ROOT / path.replace("/uploads/", "", 1)).resolve()
        if UPLOAD_ROOT not in requested_path.parents and requested_path != UPLOAD_ROOT:
            self.send_error(403)
            return
        if not requested_path.exists() or requested_path.is_dir():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(requested_path.name)[0] or "application/octet-stream"
        data = requested_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(data)

    def read_json_body(self):
        """Đọc JSON body từ request POST."""
        # API /api/contact gửi dữ liệu JSON nên cần hàm đọc JSON riêng.
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        if not raw_body:
            return {}
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {}

    def send_html(self, html, status=200):
        """Trả HTML động cho trình duyệt."""
        # Backend tự tạo HTML string rồi gửi về browser với Content-Type text/html.
        body = html.encode("utf-8")
        compressed = "gzip" in self.headers.get("Accept-Encoding", "")
        if compressed:
            body = gzip.compress(body)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if compressed:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, status=200):
        """Trả dữ liệu JSON cho frontend/API."""
        # ensure_ascii=False để JSON giữ tiếng Việt có dấu.
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        compressed = "gzip" in self.headers.get("Accept-Encoding", "")
        if compressed:
            body = gzip.compress(body)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if compressed:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self, filename, rows, fieldnames):
        """Trả file CSV để mở bằng Excel hoặc Google Sheets."""
        # utf-8-sig giúp Excel trên Windows đọc tiếng Việt có dấu ổn định hơn.
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        body = output.getvalue().encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_controller_response(self, response):
        """Gửi dữ liệu trả về từ controller."""
        # Controller trả về dạng (data, status).
        # app.py không cần biết controller xử lý nghiệp vụ ra sao.
        data, status = response
        self.send_json(data, status=status)

    def send_error_response(self, message, status=500, code="ERROR"):
        """Trả lỗi thống nhất cho API và trang web."""
        # API nhận JSON để frontend dễ xử lý bằng code.
        # Trang HTML nhận một trang lỗi đơn giản để người dùng đọc được.
        if self.path.startswith("/api/"):
            self.send_json(
                {
                    "success": False,
                    "error": {
                        "code": code,
                        "message": message,
                    },
                },
                status=status,
            )
            return

        body = f"""
          <section class="page-hero">
            <div class="container">
              <p class="eyebrow">Lỗi {status}</p>
              <h1>Không thể xử lý yêu cầu</h1>
              <p>{h(message)}</p>
              <a class="btn btn-primary" href="/">Về trang chủ</a>
            </div>
          </section>
        """
        self.send_html(render_base(f"Lỗi {status}", message, "index", body), status=status)


def main():
    """Khởi động web động tại http://127.0.0.1:8000."""
    # ThreadingHTTPServer cho phép xử lý nhiều request cùng lúc ở mức đơn giản.
    setup_logging()
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    ensure_cms_tables()
    cleanup_expired_sessions()
    server = ThreadingHTTPServer((HOST, PORT), MecPrecisionHandler)
    LOGGER.info("Dynamic web running at http://%s:%s env=%s debug=%s", HOST, PORT, ENVIRONMENT, DEBUG)
    server.serve_forever()


if __name__ == "__main__":
    main()
