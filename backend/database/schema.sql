-- File này tạo cấu trúc cơ sở dữ liệu nâng cao cho website MecPrecision.
-- SQLite dùng kiểu dữ liệu đơn giản hơn MySQL/PostgreSQL, nhưng cách tổ chức bảng vẫn giống SQL thật.

PRAGMA foreign_keys = ON;

-- Người quản trị website. Sau này dùng cho trang admin đăng nhập.
CREATE TABLE IF NOT EXISTS admin_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'editor',
  is_active INTEGER NOT NULL DEFAULT 1,
  avatar_url TEXT,
  two_factor_enabled INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Danh mục sản phẩm, ví dụ: trục, bánh răng, cụm lắp ráp.
CREATE TABLE IF NOT EXISTS product_categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Vật liệu dùng để sản xuất sản phẩm.
CREATE TABLE IF NOT EXISTS materials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  standard TEXT,
  description TEXT
);

-- Máy móc trong nhà xưởng.
CREATE TABLE IF NOT EXISTS machines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  machine_type TEXT NOT NULL,
  brand TEXT,
  max_size TEXT,
  tolerance TEXT,
  status TEXT NOT NULL DEFAULT 'active'
);

-- Quy trình hoặc công đoạn gia công.
CREATE TABLE IF NOT EXISTS manufacturing_processes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0
);

-- Sản phẩm chính.
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  short_description TEXT NOT NULL,
  description TEXT NOT NULL,
  main_image TEXT NOT NULL,
  sku TEXT,
  price REAL NOT NULL DEFAULT 0,
  thumbnail_url TEXT,
  gallery_urls TEXT,
  pdf_url TEXT,
  video_url TEXT,
  tags_text TEXT,
  seo_title TEXT,
  seo_description TEXT,
  seo_keywords TEXT,
  canonical_url TEXT,
  og_image TEXT,
  robots TEXT NOT NULL DEFAULT 'index,follow',
  schema_json TEXT,
  related_product_ids TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'published',
  published_at TEXT,
  is_featured INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES product_categories(id)
);

-- Một sản phẩm có thể dùng nhiều vật liệu.
CREATE TABLE IF NOT EXISTS product_materials (
  product_id INTEGER NOT NULL,
  material_id INTEGER NOT NULL,
  PRIMARY KEY (product_id, material_id),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
);

-- Một sản phẩm có thể đi qua nhiều công đoạn gia công.
CREATE TABLE IF NOT EXISTS product_processes (
  product_id INTEGER NOT NULL,
  process_id INTEGER NOT NULL,
  step_order INTEGER NOT NULL DEFAULT 0,
  note TEXT,
  PRIMARY KEY (product_id, process_id),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (process_id) REFERENCES manufacturing_processes(id) ON DELETE CASCADE
);

-- Ảnh phụ của sản phẩm.
CREATE TABLE IF NOT EXISTS product_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  image_url TEXT NOT NULL,
  alt_text TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Thông số kỹ thuật dạng key/value, ví dụ: dung sai, vật liệu, độ nhám.
CREATE TABLE IF NOT EXISTS product_specs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  spec_name TEXT NOT NULL,
  spec_value TEXT NOT NULL,
  unit TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Năng lực sản xuất hiển thị trên website.
CREATE TABLE IF NOT EXISTS capabilities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  icon_label TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Liên kết năng lực với máy móc cụ thể.
CREATE TABLE IF NOT EXISTS capability_machines (
  capability_id INTEGER NOT NULL,
  machine_id INTEGER NOT NULL,
  PRIMARY KEY (capability_id, machine_id),
  FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE,
  FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- Khách hàng hoặc công ty gửi yêu cầu.
CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name TEXT,
  contact_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  country TEXT DEFAULT 'Vietnam',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Yêu cầu báo giá tổng.
CREATE TABLE IF NOT EXISTS quote_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  project_name TEXT,
  message TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  assigned_to INTEGER,
  internal_note TEXT,
  quoted_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Chi tiết từng dòng trong yêu cầu báo giá.
CREATE TABLE IF NOT EXISTS quote_request_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quote_request_id INTEGER NOT NULL,
  product_id INTEGER,
  drawing_code TEXT,
  material_id INTEGER,
  quantity INTEGER NOT NULL DEFAULT 1,
  tolerance TEXT,
  note TEXT,
  FOREIGN KEY (quote_request_id) REFERENCES quote_requests(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (material_id) REFERENCES materials(id)
);

-- File khách hàng gửi kèm, ví dụ bản vẽ PDF, DXF, STEP.
CREATE TABLE IF NOT EXISTS quote_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quote_request_id INTEGER NOT NULL,
  file_name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_type TEXT,
  uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (quote_request_id) REFERENCES quote_requests(id) ON DELETE CASCADE
);

-- Danh mục tin tức.
CREATE TABLE IF NOT EXISTS news_categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE
);

-- Bài viết tin tức.
CREATE TABLE IF NOT EXISTS news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  image TEXT NOT NULL,
  description TEXT NOT NULL,
  content TEXT,
  tags_text TEXT,
  seo_title TEXT,
  seo_description TEXT,
  thumbnail_url TEXT,
  author TEXT,
  published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  scheduled_at TEXT,
  is_featured INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'published',
  FOREIGN KEY (category_id) REFERENCES news_categories(id)
);

-- Tag giúp lọc bài viết.
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE
);

-- Một bài viết có thể có nhiều tag.
CREATE TABLE IF NOT EXISTS news_tags (
  news_id INTEGER NOT NULL,
  tag_id INTEGER NOT NULL,
  PRIMARY KEY (news_id, tag_id),
  FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Bảng lưu form liên hệ đơn giản.
CREATE TABLE IF NOT EXISTS contact_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  contact TEXT NOT NULL,
  company TEXT,
  phone TEXT,
  email TEXT,
  country TEXT,
  interested_product TEXT,
  attachment_url TEXT,
  message TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  is_read INTEGER NOT NULL DEFAULT 0,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Session đăng nhập admin lưu trong database thay vì RAM.
CREATE TABLE IF NOT EXISTS admin_sessions (
  session_id TEXT PRIMARY KEY,
  admin_id INTEGER NOT NULL,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  role TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  remote_addr TEXT,
  user_agent TEXT,
  last_seen_at INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Lưu lịch sử đăng nhập để audit và chống brute force cơ bản.
CREATE TABLE IF NOT EXISTS login_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  remote_addr TEXT,
  success INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL
);

-- Token reset mật khẩu. Token chỉ dùng một lần và có thời hạn.
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  token TEXT PRIMARY KEY,
  admin_id INTEGER NOT NULL,
  email TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  used_at INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Mã xác thực 2FA dùng một lần.
CREATE TABLE IF NOT EXISTS admin_2fa_challenges (
  challenge_id TEXT PRIMARY KEY,
  admin_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  used_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Outbox email demo. Local chưa gửi email thật nên lưu nội dung email ở đây.
CREATE TABLE IF NOT EXISTS auth_email_outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipient TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Nhật ký hoạt động trong CMS.
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
);

-- Lượt truy cập trang public, dùng để hiển thị dashboard và biểu đồ.
CREATE TABLE IF NOT EXISTS page_visits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL,
  remote_addr TEXT,
  user_agent TEXT,
  visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Trang động trong CMS: About, Contact, Privacy, Terms, Career, History...
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
);

-- Menu Builder: header/footer/sidebar, parent_id dùng cho menu lồng nhau.
CREATE TABLE IF NOT EXISTS cms_menu_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  location TEXT NOT NULL DEFAULT 'header',
  parent_id INTEGER,
  label TEXT NOT NULL,
  url TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'published',
  FOREIGN KEY (parent_id) REFERENCES cms_menu_items(id) ON DELETE SET NULL
);

-- Banner cho slider trang chủ, popup và advertisement.
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
);

-- Ghi chú lịch sử chăm sóc khách hàng.
CREATE TABLE IF NOT EXISTS customer_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  note TEXT NOT NULL,
  created_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Newsletter: đăng ký, hủy đăng ký và export CSV.
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'subscribed',
  subscribed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  unsubscribed_at TEXT
);

-- Event nghiệp vụ để truy vết luồng hệ thống.
CREATE TABLE IF NOT EXISTS enterprise_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_name TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  payload TEXT,
  status TEXT NOT NULL DEFAULT 'published',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Queue xử lý nền: email, notification, backup...
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
);

-- Thông báo nội bộ trong CMS.
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
);

-- Cài đặt hệ thống chỉnh trong CMS.
-- Lịch sử hỏi đáp AI, dùng cho chatbot public và AI trong Admin.
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
);

-- Cache bản dịch AI cho website đa ngôn ngữ.
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
);

CREATE TABLE IF NOT EXISTS system_settings (
  setting_key TEXT PRIMARY KEY,
  setting_value TEXT NOT NULL
);

-- Index giúp truy vấn nhanh hơn khi dữ liệu lớn.
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);
CREATE INDEX IF NOT EXISTS idx_news_category_id ON news(category_id);
CREATE INDEX IF NOT EXISTS idx_quote_requests_customer_id ON quote_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_quote_items_quote_request_id ON quote_request_items(quote_request_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at ON admin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, created_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_admin ON password_reset_tokens(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_created ON admin_activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_page_visits_visited_at ON page_visits(visited_at);
CREATE INDEX IF NOT EXISTS idx_enterprise_events_created ON enterprise_events(created_at);
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status, available_at);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_created ON ai_conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_translation_cache_lookup ON ai_translation_cache(source_hash, target_language, model);

-- View là "bảng ảo" để đọc dữ liệu sản phẩm kèm tên danh mục dễ hơn.
CREATE VIEW IF NOT EXISTS product_overview AS
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
JOIN product_categories ON product_categories.id = products.category_id;
