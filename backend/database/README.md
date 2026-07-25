# Cơ sở dữ liệu nâng cao

Thư mục này chứa cơ sở dữ liệu SQL cho website MecPrecision. Mình dùng SQLite vì dễ chạy trên máy cá nhân, không cần cài MySQL/PostgreSQL.

## Các file chính

- `schema.sql`: tạo cấu trúc bảng, khóa ngoại, index và view.
- `seed.sql`: thêm dữ liệu mẫu.
- `mecprecision.sqlite`: file database SQLite sau khi chạy script khởi tạo.

## Nhóm bảng chính

- Quản trị: `admin_users`
- Sản phẩm: `product_categories`, `products`, `product_images`, `product_specs`
- Sản xuất: `materials`, `machines`, `manufacturing_processes`, `product_materials`, `product_processes`
- Năng lực: `capabilities`, `capability_machines`
- Khách hàng/báo giá: `customers`, `quote_requests`, `quote_request_items`, `quote_files`
- Tin tức: `news_categories`, `news`, `tags`, `news_tags`
- Liên hệ: `contact_requests`

## Quan hệ dữ liệu quan trọng

- Một danh mục có nhiều sản phẩm.
- Một sản phẩm có nhiều vật liệu, nhiều quy trình, nhiều ảnh và nhiều thông số kỹ thuật.
- Một yêu cầu báo giá thuộc về một khách hàng.
- Một yêu cầu báo giá có nhiều dòng chi tiết và nhiều file đính kèm.
- Một bài viết thuộc một danh mục và có thể có nhiều tag.

## View có sẵn

- `product_overview`: bảng ảo giúp xem sản phẩm kèm tên danh mục nhanh hơn.

## Lưu ý

Website hiện tại vẫn là HTML/CSS/JS tĩnh, nên chưa đọc trực tiếp từ database. Muốn website dùng SQL thật, bước tiếp theo là thêm backend như Node.js, PHP, Python Flask hoặc Laravel để lấy dữ liệu từ `mecprecision.sqlite`.
