from pathlib import Path
import hashlib
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "backend" / "database" / "mecprecision.sqlite"
PASSWORD_SALT = "mecprecision-demo-salt"


def hash_password(password):
    """Tạo hash giống backend/app.py để tài khoản demo đăng nhập được."""
    raw_value = f"{PASSWORD_SALT}:{password}".encode("utf-8")
    return hashlib.sha256(raw_value).hexdigest()


def insert_if_missing(connection, table, unique_column, unique_value, data):
    """Thêm dữ liệu nếu chưa có, tránh chạy script nhiều lần bị trùng."""
    exists = connection.execute(
        f"SELECT id FROM {table} WHERE {unique_column} = ?",
        (unique_value,),
    ).fetchone()
    if exists:
        return exists["id"]

    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cursor = connection.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    return cursor.lastrowid


def main():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    # Bảng cài đặt được CMS tạo khi backend chạy, script cũng tạo để dùng độc lập.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
          setting_key TEXT PRIMARY KEY,
          setting_value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS enterprise_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_name TEXT NOT NULL,
          entity_type TEXT,
          entity_id TEXT,
          payload TEXT,
          status TEXT NOT NULL DEFAULT 'published',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS job_queue (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          job_type TEXT NOT NULL,
          payload TEXT,
          status TEXT NOT NULL DEFAULT 'pending',
          attempts INTEGER NOT NULL DEFAULT 0,
          available_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          started_at TEXT,
          finished_at TEXT,
          last_error TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          recipient_type TEXT NOT NULL DEFAULT 'admin',
          recipient_id INTEGER,
          title TEXT NOT NULL,
          message TEXT NOT NULL,
          level TEXT NOT NULL DEFAULT 'info',
          is_read INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          read_at TEXT
        )
        """
    )

    categories = [
        ("Đồ gá & fixture", "do-ga-fixture", "Đồ gá kiểm tra, đồ gá gia công và fixture theo bản vẽ.", 4),
        ("Chi tiết máy tự động hóa", "chi-tiet-may-tu-dong-hoa", "Chi tiết cho dây chuyền tự động, robot và máy chuyên dụng.", 5),
        ("Khuôn mẫu & insert", "khuon-mau-insert", "Insert, lõi khuôn và chi tiết khuôn có yêu cầu độ chính xác cao.", 6),
        ("Chi tiết inox", "chi-tiet-inox", "Linh kiện SUS304/SUS316 cho môi trường cần chống ăn mòn.", 7),
        ("Chi tiết nhôm", "chi-tiet-nhom", "Chi tiết nhôm nhẹ, anodize hoặc xử lý bề mặt theo yêu cầu.", 8),
    ]
    category_ids = {}
    for name, slug, description, sort_order in categories:
        category_ids[slug] = insert_if_missing(
            connection,
            "product_categories",
            "slug",
            slug,
            {
                "name": name,
                "slug": slug,
                "description": description,
                "sort_order": sort_order,
            },
        )

    # Lấy cả danh mục cũ để liên kết sản phẩm demo.
    all_categories = {
        row["slug"]: row["id"]
        for row in connection.execute("SELECT id, slug FROM product_categories").fetchall()
    }

    products = [
        ("Đồ gá kiểm tra kích thước", "do-ga-kiem-tra-kich-thuoc", "do-ga-fixture", "Đồ gá hỗ trợ kiểm tra nhanh kích thước chi tiết.", "Thiết kế và gia công đồ gá kiểm tra theo bản vẽ, phù hợp kiểm soát chất lượng hàng loạt.", "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=900&q=80", 1),
        ("Fixture phay CNC nhiều vị trí", "fixture-phay-cnc-nhieu-vi-tri", "do-ga-fixture", "Fixture giúp gá nhiều chi tiết trong một lần gia công.", "Tối ưu thời gian gá đặt, tăng độ lặp lại cho các đơn hàng sản xuất số lượng vừa và lớn.", "https://images.unsplash.com/photo-1565043589221-1a6fd9ae45c7?auto=format&fit=crop&w=900&q=80", 0),
        ("Puly nhôm chính xác", "puly-nhom-chinh-xac", "chi-tiet-nhom", "Puly nhôm gia công CNC cho hệ truyền động nhẹ.", "Có thể anodize màu, kiểm tra độ đồng tâm và cân bằng theo yêu cầu ứng dụng.", "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=900&q=80", 1),
        ("Insert khuôn thép tôi", "insert-khuon-thep-toi", "khuon-mau-insert", "Insert khuôn có xử lý nhiệt và mài hoàn thiện.", "Phù hợp cho khuôn ép nhựa, khuôn dập hoặc chi tiết chịu mài mòn cao.", "https://images.unsplash.com/photo-1581092919535-7146ff1a590b?auto=format&fit=crop&w=900&q=80", 0),
        ("Chi tiết inox chống ăn mòn", "chi-tiet-inox-chong-an-mon", "chi-tiet-inox", "Linh kiện inox cho môi trường ẩm hoặc hóa chất nhẹ.", "Gia công từ SUS304/SUS316, xử lý bề mặt và đóng gói chống trầy xước.", "https://images.unsplash.com/photo-1581093458791-9f3c3f8b607f?auto=format&fit=crop&w=900&q=80", 0),
        ("Trục robot tự động hóa", "truc-robot-tu-dong-hoa", "chi-tiet-may-tu-dong-hoa", "Trục và bạc dẫn hướng cho cụm máy tự động.", "Đảm bảo độ thẳng, độ đồng tâm và truy xuất dữ liệu kiểm tra từng lô.", "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=900&q=80", 1),
        ("Tấm gá nhôm anodize", "tam-ga-nhom-anodize", "chi-tiet-nhom", "Tấm gá nhôm phay CNC và anodize bề mặt.", "Ứng dụng trong máy kiểm tra, dây chuyền lắp ráp và robot công nghiệp.", "https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?auto=format&fit=crop&w=900&q=80", 0),
        ("Bạc dẫn hướng SCM440", "bac-dan-huong-scm440", "truc-bac-chinh-xac", "Bạc dẫn hướng thép hợp kim có xử lý nhiệt.", "Gia công tiện, mài, kiểm tra đường kính trong/ngoài theo dung sai chặt.", "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?auto=format&fit=crop&w=900&q=80", 1),
    ]
    for name, slug, category_slug, short_description, description, image, is_featured in products:
        insert_if_missing(
            connection,
            "products",
            "slug",
            slug,
            {
                "category_id": all_categories[category_slug],
                "name": name,
                "slug": slug,
                "short_description": short_description,
                "description": description,
                "main_image": image,
                "is_featured": is_featured,
            },
        )

    news_category_ids = {}
    for name, slug in [
        ("Dự án khách hàng", "du-an-khach-hang"),
        ("Năng lực sản xuất", "nang-luc-san-xuat"),
        ("Tuyển dụng", "tuyen-dung"),
    ]:
        news_category_ids[slug] = insert_if_missing(
            connection,
            "news_categories",
            "slug",
            slug,
            {"name": name, "slug": slug},
        )

    all_news_categories = {
        row["slug"]: row["id"]
        for row in connection.execute("SELECT id, slug FROM news_categories").fetchall()
    }
    news_items = [
        ("Hoàn thành lô fixture kiểm tra cho dây chuyền mới", "hoan-thanh-lo-fixture-kiem-tra", "du-an-khach-hang", "https://images.unsplash.com/photo-1581092162384-8987c1d64718?auto=format&fit=crop&w=900&q=80", "Đội sản xuất hoàn thành lô fixture kiểm tra với yêu cầu truy xuất dữ liệu từng mã hàng.", "Nội dung demo có thể sửa trực tiếp trong CMS."),
        ("Bổ sung quy trình kiểm tra ảnh trước khi giao hàng", "bo-sung-quy-trinh-kiem-tra-anh", "nang-luc-san-xuat", "https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?auto=format&fit=crop&w=900&q=80", "Mỗi lô hàng quan trọng được chụp ảnh lưu hồ sơ trước khi đóng gói.", "Nội dung demo có thể sửa trực tiếp trong CMS."),
        ("Mở vị trí kỹ thuật viên vận hành CNC", "tuyen-ky-thuat-vien-van-hanh-cnc", "tuyen-dung", "https://images.unsplash.com/photo-1581092334651-ddf26d9a09d0?auto=format&fit=crop&w=900&q=80", "MecPrecision tuyển kỹ thuật viên CNC có kinh nghiệm đọc bản vẽ và kiểm tra kích thước.", "Nội dung demo có thể sửa trực tiếp trong CMS."),
        ("Cải tiến đóng gói chống trầy cho chi tiết inox", "cai-tien-dong-goi-chi-tiet-inox", "tin-nha-may", "https://images.unsplash.com/photo-1581092335397-9583eb92d232?auto=format&fit=crop&w=900&q=80", "Quy trình đóng gói mới giúp hạn chế vết xước trong quá trình vận chuyển.", "Nội dung demo có thể sửa trực tiếp trong CMS."),
        ("Khi nào nên chọn nhôm 6061 cho đồ gá", "chon-nhom-6061-cho-do-ga", "ky-thuat", "https://images.unsplash.com/photo-1581093458791-9f3c3f8b607f?auto=format&fit=crop&w=900&q=80", "Nhôm 6061 phù hợp khi cần trọng lượng nhẹ, gia công nhanh và xử lý bề mặt đẹp.", "Nội dung demo có thể sửa trực tiếp trong CMS."),
    ]
    for title, slug, category_slug, image, description, content in news_items:
        insert_if_missing(
            connection,
            "news",
            "slug",
            slug,
            {
                "category_id": all_news_categories[category_slug],
                "title": title,
                "slug": slug,
                "image": image,
                "description": description,
                "content": content,
            },
        )

    contacts = [
        ("Trần Minh Khang", "khang@example.com", "Cần báo giá 50 chi tiết inox theo bản vẽ.", "new"),
        ("Công ty Alpha", "0901234567", "Muốn tư vấn vật liệu cho trục truyền động.", "processing"),
        ("Nguyễn Thị Lan", "lan@factory.vn", "Gửi thông tin năng lực gia công đồ gá.", "done"),
        ("Bộ phận mua hàng Beta", "purchase@beta.vn", "Cần làm fixture phay CNC số lượng 12 bộ.", "new"),
        ("Lê Hoàng Nam", "nam@example.com", "Tư vấn dung sai cho bạc dẫn hướng.", "processing"),
        ("Công ty Delta Automation", "0911222333", "Cần báo giá tấm gá nhôm anodize.", "new"),
    ]
    for name, contact, message, status in contacts:
        exists = connection.execute(
            "SELECT id FROM contact_requests WHERE contact = ? AND message = ?",
            (contact, message),
        ).fetchone()
        if not exists:
            connection.execute(
                "INSERT INTO contact_requests (name, contact, message, status) VALUES (?, ?, ?, ?)",
                (name, contact, message, status),
            )

    users = [
        ("Biên tập viên Nội dung", "editor@mecprecision.vn", "editor123", "editor", 1),
        ("Người xem Demo", "viewer@mecprecision.vn", "viewer123", "viewer", 1),
    ]
    for full_name, email, password, role, is_active in users:
        insert_if_missing(
            connection,
            "admin_users",
            "email",
            email,
            {
                "full_name": full_name,
                "email": email,
                "password_hash": hash_password(password),
                "role": role,
                "is_active": is_active,
            },
        )

    pages = [
        (
            "Giới thiệu MecPrecision",
            "gioi-thieu",
            """
            <h2>Giới thiệu MecPrecision VIETNAM</h2>
            <p>MecPrecision VIETNAM cung cấp dịch vụ gia công cơ khí chính xác cho doanh nghiệp sản xuất, tự động hóa và lắp ráp công nghiệp.</p>
            <p>Chúng tôi tập trung vào các chi tiết CNC, đồ gá, fixture, chi tiết inox, chi tiết nhôm và cụm linh kiện theo bản vẽ kỹ thuật.</p>
            <p>Mục tiêu của MecPrecision là giúp khách hàng có sản phẩm ổn định, đúng dung sai và giao hàng đúng tiến độ.</p>
            """,
            "Giới thiệu MecPrecision VIETNAM",
            "Thông tin giới thiệu công ty MecPrecision VIETNAM và năng lực gia công cơ khí chính xác.",
            "published",
            1,
        ),
        (
            "Lịch sử phát triển",
            "lich-su-phat-trien",
            """
            <h2>Lịch sử phát triển</h2>
            <p>MecPrecision bắt đầu từ nhóm kỹ thuật chuyên gia công chi tiết chính xác cho máy tự động và thiết bị công nghiệp.</p>
            <p>Qua từng giai đoạn, công ty mở rộng năng lực từ tiện, phay CNC sang thiết kế đồ gá, kiểm tra chất lượng và quản lý dữ liệu sản xuất.</p>
            <p>Trang này có thể dùng để cập nhật các mốc quan trọng của doanh nghiệp.</p>
            """,
            "Lịch sử phát triển MecPrecision",
            "Các cột mốc phát triển và định hướng của MecPrecision VIETNAM.",
            "published",
            2,
        ),
        (
            "Năng lực sản xuất",
            "nang-luc-san-xuat",
            """
            <h2>Năng lực sản xuất</h2>
            <p>Hệ thống sản xuất hỗ trợ gia công CNC, tiện, phay, khoan, taro, mài và xử lý bề mặt theo yêu cầu.</p>
            <ul>
              <li>Gia công chi tiết theo bản vẽ 2D/3D.</li>
              <li>Gia công đồ gá kiểm tra, fixture và jig lắp ráp.</li>
              <li>Kiểm tra kích thước theo dung sai kỹ thuật.</li>
              <li>Đóng gói và truy xuất dữ liệu theo từng đơn hàng.</li>
            </ul>
            """,
            "Năng lực sản xuất cơ khí chính xác",
            "Năng lực CNC, fixture, đồ gá và kiểm tra chất lượng của MecPrecision.",
            "published",
            3,
        ),
        (
            "Quy trình chất lượng",
            "quy-trinh-chat-luong",
            """
            <h2>Quy trình chất lượng</h2>
            <p>Mỗi đơn hàng được kiểm soát từ bước nhận bản vẽ, phân tích dung sai, lập kế hoạch gia công, kiểm tra trong quá trình và kiểm tra cuối.</p>
            <p>Dữ liệu kiểm tra có thể được lưu lại để hỗ trợ truy xuất khi khách hàng cần đối chiếu.</p>
            <p>Trang này phù hợp để trình bày quy trình QC, thiết bị đo và tiêu chuẩn nghiệm thu.</p>
            """,
            "Quy trình kiểm soát chất lượng",
            "Mô tả quy trình QC và kiểm tra chất lượng trong gia công cơ khí chính xác.",
            "published",
            4,
        ),
        (
            "Tuyển dụng",
            "tuyen-dung",
            """
            <h2>Tuyển dụng</h2>
            <p>MecPrecision thường xuyên tìm kiếm kỹ thuật viên CNC, nhân viên QC, kỹ sư thiết kế đồ gá và nhân sự vận hành sản xuất.</p>
            <p>Ứng viên có kinh nghiệm đọc bản vẽ, sử dụng dụng cụ đo và làm việc theo quy trình chất lượng sẽ phù hợp với môi trường của chúng tôi.</p>
            <p>Vui lòng gửi hồ sơ qua email tuyển dụng hoặc liên hệ trực tiếp với bộ phận nhân sự.</p>
            """,
            "Tuyển dụng MecPrecision",
            "Thông tin tuyển dụng kỹ thuật viên CNC, QC và kỹ sư cơ khí tại MecPrecision.",
            "published",
            5,
        ),
        (
            "Đối tác và khách hàng",
            "doi-tac-khach-hang",
            """
            <h2>Đối tác và khách hàng</h2>
            <p>MecPrecision hướng tới hợp tác dài hạn với các công ty sản xuất, nhà máy tự động hóa và doanh nghiệp cần linh kiện cơ khí chính xác.</p>
            <p>Chúng tôi ưu tiên sự minh bạch trong báo giá, tiến độ giao hàng và phản hồi kỹ thuật.</p>
            <p>Trang này có thể dùng để giới thiệu nhóm khách hàng, ngành phục vụ hoặc case study tiêu biểu.</p>
            """,
            "Đối tác và khách hàng MecPrecision",
            "Thông tin đối tác, khách hàng và ngành nghề MecPrecision phục vụ.",
            "published",
            6,
        ),
        (
            "Tài liệu kỹ thuật",
            "tai-lieu-ky-thuat",
            """
            <h2>Tài liệu kỹ thuật</h2>
            <p>Trang này dùng để đăng các hướng dẫn chuẩn bị bản vẽ, định dạng file, yêu cầu dung sai và lưu ý khi gửi yêu cầu báo giá.</p>
            <ul>
              <li>File bản vẽ nên có PDF kèm STEP hoặc DWG.</li>
              <li>Nên ghi rõ vật liệu, xử lý bề mặt và số lượng.</li>
              <li>Nên ghi deadline mong muốn để bộ phận kỹ thuật phản hồi chính xác.</li>
            </ul>
            """,
            "Tài liệu kỹ thuật gia công cơ khí",
            "Hướng dẫn chuẩn bị bản vẽ và thông tin kỹ thuật khi yêu cầu báo giá.",
            "published",
            7,
        ),
        (
            "Câu hỏi thường gặp",
            "cau-hoi-thuong-gap",
            """
            <h2>Câu hỏi thường gặp</h2>
            <h3>MecPrecision nhận gia công số lượng ít không?</h3>
            <p>Có. Chúng tôi có thể hỗ trợ mẫu thử, đơn hàng nhỏ và đơn hàng sản xuất lặp lại.</p>
            <h3>Cần gửi thông tin gì để báo giá?</h3>
            <p>Khách hàng nên gửi bản vẽ, vật liệu, số lượng, dung sai quan trọng và thời gian cần hàng.</p>
            <h3>Có hỗ trợ tư vấn vật liệu không?</h3>
            <p>Có. Bộ phận kỹ thuật có thể góp ý vật liệu và phương án gia công phù hợp.</p>
            """,
            "Câu hỏi thường gặp MecPrecision",
            "Giải đáp các câu hỏi thường gặp về gia công CNC, báo giá và bản vẽ kỹ thuật.",
            "published",
            8,
        ),
        (
            "Chính sách bảo mật",
            "chinh-sach-bao-mat",
            """
            <h2>Chính sách bảo mật</h2>
            <p>MecPrecision tôn trọng thông tin khách hàng, bao gồm thông tin liên hệ, bản vẽ kỹ thuật và tài liệu dự án.</p>
            <p>Dữ liệu chỉ được sử dụng cho mục đích tư vấn, báo giá, sản xuất và chăm sóc khách hàng.</p>
            <p>Khách hàng có thể yêu cầu cập nhật hoặc xóa thông tin liên hệ khi cần.</p>
            """,
            "Chính sách bảo mật MecPrecision",
            "Chính sách bảo mật thông tin khách hàng và tài liệu kỹ thuật.",
            "published",
            9,
        ),
        (
            "Điều khoản sử dụng",
            "dieu-khoan-su-dung",
            """
            <h2>Điều khoản sử dụng</h2>
            <p>Nội dung trên website MecPrecision được cung cấp nhằm mục đích giới thiệu năng lực, sản phẩm và dịch vụ.</p>
            <p>Thông tin báo giá, thời gian giao hàng và điều kiện sản xuất sẽ được xác nhận riêng theo từng yêu cầu thực tế.</p>
            <p>Việc sử dụng website đồng nghĩa với việc người dùng đồng ý tuân thủ các điều khoản cơ bản này.</p>
            """,
            "Điều khoản sử dụng website MecPrecision",
            "Điều khoản sử dụng thông tin và dịch vụ trên website MecPrecision.",
            "published",
            10,
        ),
    ]
    for title, slug, content, seo_title, seo_description, status, sort_order in pages:
        insert_if_missing(
            connection,
            "cms_pages",
            "slug",
            slug,
            {
                "title": title,
                "slug": slug,
                "content": content.strip(),
                "seo_title": seo_title,
                "seo_description": seo_description,
                "status": status,
                "sort_order": sort_order,
            },
        )

    menu_items = [
        ("header", "Trang chủ", "/", 1),
        ("header", "Sản phẩm", "/san-pham.html", 2),
        ("header", "Công nghệ", "/cong-nghe.html", 3),
        ("header", "Tin tức", "/tin-tuc.html", 4),
        ("header", "Giới thiệu", "/gioi-thieu", 5),
        ("header", "Năng lực", "/nang-luc-san-xuat", 6),
        ("header", "Tuyển dụng", "/tuyen-dung", 7),
        ("header", "Liên hệ", "/lien-he.html", 8),
        ("footer", "Giới thiệu", "/gioi-thieu", 1),
        ("footer", "Lịch sử phát triển", "/lich-su-phat-trien", 2),
        ("footer", "Năng lực sản xuất", "/nang-luc-san-xuat", 3),
        ("footer", "Quy trình chất lượng", "/quy-trinh-chat-luong", 4),
        ("footer", "Tuyển dụng", "/tuyen-dung", 5),
        ("footer", "Đối tác và khách hàng", "/doi-tac-khach-hang", 6),
        ("footer", "Tài liệu kỹ thuật", "/tai-lieu-ky-thuat", 7),
        ("footer", "Câu hỏi thường gặp", "/cau-hoi-thuong-gap", 8),
        ("footer", "Chính sách bảo mật", "/chinh-sach-bao-mat", 9),
        ("footer", "Điều khoản sử dụng", "/dieu-khoan-su-dung", 10),
    ]
    for location, label, url, sort_order in menu_items:
        exists = connection.execute(
            "SELECT id FROM cms_menu_items WHERE location = ? AND url = ?",
            (location, url),
        ).fetchone()
        if not exists:
            connection.execute(
                """
                INSERT INTO cms_menu_items (location, label, url, sort_order, status)
                VALUES (?, ?, ?, ?, 'published')
                """,
                (location, label, url, sort_order),
            )

    settings = {
        "site_name": "MecPrecision VIETNAM",
        "contact_email": "sales@mecprecision.vn",
        "hotline": "0900 000 000",
        "address": "Khu công nghiệp, TP. Hồ Chí Minh, Việt Nam",
    }
    for key, value in settings.items():
        connection.execute(
            """
            INSERT INTO system_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """,
            (key, value),
        )

    # Dữ liệu demo cho phần Enterprise Backend: Event, Queue, Notification.
    if not connection.execute("SELECT id FROM enterprise_events WHERE event_name = 'demo.seeded'").fetchone():
        connection.execute(
            """
            INSERT INTO enterprise_events (event_name, entity_type, entity_id, payload, status)
            VALUES ('demo.seeded', 'system', 'seed', '{"message":"Demo event tu seed script"}', 'published')
            """
        )
    if not connection.execute("SELECT id FROM job_queue WHERE job_type = 'notification.create' AND payload LIKE '%Demo notification%'").fetchone():
        connection.execute(
            """
            INSERT INTO job_queue (job_type, payload, status)
            VALUES ('notification.create', '{"title":"Demo notification","message":"Job nay duoc tao tu seed script","level":"info"}', 'pending')
            """
        )
    if not connection.execute("SELECT id FROM notifications WHERE title = 'Chào mừng CMS Enterprise'").fetchone():
        connection.execute(
            """
            INSERT INTO notifications (title, message, level)
            VALUES ('Chào mừng CMS Enterprise', 'Notification mẫu để xem trong Developer panel.', 'success')
            """
        )

    connection.commit()
    connection.close()
    print("Da them du lieu demo cho CMS.")


if __name__ == "__main__":
    main()
