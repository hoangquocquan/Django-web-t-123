from database.connection import get_connection


def ensure_cms_tables():
    """Tạo các bảng CMS bổ sung nếu database cũ chưa có."""
    with get_connection() as connection:
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
            CREATE TABLE IF NOT EXISTS admin_sessions (
              session_id TEXT PRIMARY KEY,
              admin_id INTEGER NOT NULL,
              full_name TEXT NOT NULL,
              email TEXT NOT NULL,
              role TEXT NOT NULL,
              expires_at INTEGER NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS login_attempts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT NOT NULL,
              remote_addr TEXT,
              success INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
              token TEXT PRIMARY KEY,
              admin_id INTEGER NOT NULL,
              email TEXT NOT NULL,
              expires_at INTEGER NOT NULL,
              used_at INTEGER,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_email_outbox (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              recipient TEXT NOT NULL,
              subject TEXT NOT NULL,
              body TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Các cột session dưới đây giúp demo "session nhiều thiết bị".
        # SQLite không có ADD COLUMN IF NOT EXISTS nên cần kiểm tra trước.
        existing_session_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(admin_sessions)").fetchall()
        }
        session_columns = {
            "remote_addr": "TEXT",
            "user_agent": "TEXT",
            "last_seen_at": "INTEGER",
        }
        for column_name, column_type in session_columns.items():
            if column_name not in existing_session_columns:
                connection.execute(f"ALTER TABLE admin_sessions ADD COLUMN {column_name} {column_type}")

        # Avatar người dùng: database cũ chưa có cột này nên thêm bằng migration.
        existing_user_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(admin_users)").fetchall()
        }
        user_columns = {
            "avatar_url": "TEXT",
            "two_factor_enabled": "INTEGER NOT NULL DEFAULT 0",
        }
        for column_name, column_type in user_columns.items():
            if column_name not in existing_user_columns:
                connection.execute(f"ALTER TABLE admin_users ADD COLUMN {column_name} {column_type}")

        # 2FA challenge lưu mã xác thực một lần cho admin.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_2fa_challenges (
              challenge_id TEXT PRIMARY KEY,
              admin_id INTEGER NOT NULL,
              code TEXT NOT NULL,
              used_at TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
            )
            """
        )

        # Products nâng cao cho CMS giai đoạn 2.
        existing_product_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(products)").fetchall()
        }
        product_columns = {
            "sku": "TEXT",
            "price": "REAL NOT NULL DEFAULT 0",
            "thumbnail_url": "TEXT",
            "gallery_urls": "TEXT",
            "pdf_url": "TEXT",
            "video_url": "TEXT",
            "tags_text": "TEXT",
            "seo_title": "TEXT",
            "seo_description": "TEXT",
            "seo_keywords": "TEXT",
            "canonical_url": "TEXT",
            "og_image": "TEXT",
            "robots": "TEXT NOT NULL DEFAULT 'index,follow'",
            "schema_json": "TEXT",
            "related_product_ids": "TEXT",
            "sort_order": "INTEGER NOT NULL DEFAULT 0",
            "status": "TEXT NOT NULL DEFAULT 'published'",
            "published_at": "TEXT",
        }
        for column_name, column_type in product_columns.items():
            if column_name not in existing_product_columns:
                connection.execute(f"ALTER TABLE products ADD COLUMN {column_name} {column_type}")

        # View product_overview dùng cho public web và CMS.
        # Khi thêm cột mới vào products, view cũ phải được tạo lại để SELECT không bị thiếu cột.
        connection.execute("DROP VIEW IF EXISTS product_overview")
        connection.execute(
            """
            CREATE VIEW product_overview AS
            SELECT
              products.id,
              products.category_id,
              products.name,
              products.slug,
              product_categories.name AS category_name,
              products.short_description,
              products.main_image,
              products.is_featured,
              products.sku,
              products.price,
              products.thumbnail_url,
              products.gallery_urls,
              products.pdf_url,
              products.video_url,
              products.tags_text,
              products.seo_title,
              products.seo_description,
              products.seo_keywords,
              products.canonical_url,
              products.og_image,
              products.robots,
              products.schema_json,
              products.related_product_ids,
              products.sort_order,
              products.status,
              products.published_at
            FROM products
            JOIN product_categories ON product_categories.id = products.category_id
            """
        )

        # News nâng cao cho CMS giai đoạn 2.
        existing_news_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(news)").fetchall()
        }
        news_columns = {
            "tags_text": "TEXT",
            "seo_title": "TEXT",
            "seo_description": "TEXT",
            "thumbnail_url": "TEXT",
            "author": "TEXT",
            "scheduled_at": "TEXT",
            "is_featured": "INTEGER NOT NULL DEFAULT 0",
            "status": "TEXT NOT NULL DEFAULT 'published'",
        }
        for column_name, column_type in news_columns.items():
            if column_name not in existing_news_columns:
                connection.execute(f"ALTER TABLE news ADD COLUMN {column_name} {column_type}")

        # Nhật ký hoạt động giúp admin biết ai đã thêm/sửa/xóa/khóa/mở khóa dữ liệu.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_activity_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              admin_id INTEGER,
              actor_name TEXT,
              action TEXT NOT NULL,
              target_type TEXT,
              target_id TEXT,
              description TEXT,
              remote_addr TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE SET NULL
            )
            """
        )

        # Trang động: About, Contact, Privacy, Terms, Career, History...
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cms_pages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              slug TEXT NOT NULL UNIQUE,
              content TEXT,
              seo_title TEXT,
              seo_description TEXT,
              status TEXT NOT NULL DEFAULT 'draft',
              sort_order INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Menu Builder: header/footer/sidebar, có parent_id để tạo menu lồng nhau.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cms_menu_items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              location TEXT NOT NULL DEFAULT 'header',
              parent_id INTEGER,
              label TEXT NOT NULL,
              url TEXT NOT NULL,
              sort_order INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'published',
              FOREIGN KEY (parent_id) REFERENCES cms_menu_items(id) ON DELETE SET NULL
            )
            """
        )

        # Banner: slider trang chủ, popup, advertisement.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cms_banners (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              placement TEXT NOT NULL DEFAULT 'home_slider',
              image_url TEXT,
              link_url TEXT,
              content TEXT,
              sort_order INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'draft',
              starts_at TEXT,
              ends_at TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Ghi chú/lịch sử khách hàng.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_notes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              customer_id INTEGER NOT NULL,
              note TEXT NOT NULL,
              created_by TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
            """
        )

        # Newsletter: đăng ký/hủy đăng ký và export CSV.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT NOT NULL UNIQUE,
              status TEXT NOT NULL DEFAULT 'subscribed',
              subscribed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              unsubscribed_at TEXT
            )
            """
        )

        # Enterprise Events: lưu sự kiện nghiệp vụ như contact.created, quote.created.
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

        # Queue: hàng đợi xử lý nền cho email, notification, backup...
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

        # Notification: thông báo nội bộ để admin thấy việc mới cần xử lý.
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

        # AI conversations: lịch sử hỏi đáp từ chatbot public và Admin AI.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_conversations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              channel TEXT NOT NULL DEFAULT 'public',
              user_message TEXT NOT NULL,
              assistant_message TEXT,
              model TEXT,
              provider TEXT NOT NULL DEFAULT 'ollama',
              status TEXT NOT NULL DEFAULT 'ok',
              error TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Cache bản dịch AI cho public site đa ngôn ngữ.
        # Nếu một câu đã dịch sang English/Japanese rồi, lần sau lấy từ SQLite thay vì gọi Ollama lại.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_translation_cache (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source_hash TEXT NOT NULL,
              source_text TEXT NOT NULL,
              target_language TEXT NOT NULL,
              translated_text TEXT NOT NULL,
              provider TEXT NOT NULL DEFAULT 'ollama',
              model TEXT,
              status TEXT NOT NULL DEFAULT 'ok',
              error TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(source_hash, target_language, model)
            )
            """
        )

        # Contact giai đoạn 3: đánh dấu đã đọc và ghi chú nội bộ.
        existing_contact_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(contact_requests)").fetchall()
        }
        contact_columns = {
            "company": "TEXT",
            "phone": "TEXT",
            "email": "TEXT",
            "country": "TEXT",
            "interested_product": "TEXT",
            "attachment_url": "TEXT",
            "is_read": "INTEGER NOT NULL DEFAULT 0",
            "note": "TEXT",
        }
        for column_name, column_type in contact_columns.items():
            if column_name not in existing_contact_columns:
                connection.execute(f"ALTER TABLE contact_requests ADD COLUMN {column_name} {column_type}")

        # Quote workflow: phân công nhân viên và các mốc xử lý.
        existing_quote_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(quote_requests)").fetchall()
        }
        quote_columns = {
            "assigned_to": "INTEGER",
            "internal_note": "TEXT",
            "quoted_at": "TEXT",
            "completed_at": "TEXT",
        }
        for column_name, column_type in quote_columns.items():
            if column_name not in existing_quote_columns:
                connection.execute(f"ALTER TABLE quote_requests ADD COLUMN {column_name} {column_type}")

        # Lượt truy cập public site. Bảng này phục vụ dashboard và biểu đồ.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS page_visits (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              path TEXT NOT NULL,
              remote_addr TEXT,
              user_agent TEXT,
              visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at ON admin_sessions(expires_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, created_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_admin ON password_reset_tokens(admin_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_created ON admin_activity_logs(created_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_page_visits_visited_at ON page_visits(visited_at)"
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_cms_pages_slug ON cms_pages(slug)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_cms_menu_location ON cms_menu_items(location)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_cms_banners_placement ON cms_banners(placement)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_newsletter_status ON newsletter_subscribers(status)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_enterprise_events_created ON enterprise_events(created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status, available_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read, created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_ai_conversations_created ON ai_conversations(created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_ai_translation_cache_lookup ON ai_translation_cache(source_hash, target_language, model)")
        connection.commit()
