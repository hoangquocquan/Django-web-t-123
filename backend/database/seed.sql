-- File này thêm dữ liệu mẫu cho database nâng cao.
-- Dữ liệu này giúp bạn thử website/admin trước khi nhập dữ liệu thật.

INSERT INTO admin_users (full_name, email, password_hash, role) VALUES
('Quản trị MecPrecision', 'admin@mecprecision.vn', '285b9ab0fea85722dd3c251d7783a2a020e24724daf20241ebd546cd259843cf', 'admin');

INSERT INTO product_categories (name, slug, description, sort_order) VALUES
('Trục & bạc chính xác', 'truc-bac-chinh-xac', 'Các chi tiết dạng tròn, trục truyền động, bạc dẫn hướng.', 1),
('Bánh răng & truyền động', 'banh-rang-truyen-dong', 'Nhóm chi tiết truyền động có yêu cầu độ đồng tâm và độ bền cao.', 2),
('Cụm linh kiện lắp ráp', 'cum-linh-kien-lap-rap', 'Gia công và lắp ráp cụm chi tiết theo bản vẽ khách hàng.', 3);

INSERT INTO materials (name, standard, description) VALUES
('S45C', 'JIS G4051', 'Thép carbon dùng phổ biến cho trục và chi tiết cơ khí.'),
('SUS304', 'JIS G4303', 'Thép không gỉ phù hợp môi trường cần chống ăn mòn.'),
('A6061', 'JIS H4000', 'Nhôm hợp kim nhẹ, dễ gia công, dùng cho đồ gá và chi tiết máy.'),
('SCM440', 'JIS G4105', 'Thép hợp kim có độ bền cao, dùng cho chi tiết chịu tải.');

INSERT INTO machines (name, machine_type, brand, max_size, tolerance, status) VALUES
('CNC Lathe L-250', 'CNC Turning', 'Mazak', 'Ø250 x 500mm', '±0.01mm', 'active'),
('Vertical Machining Center VMC-850', 'CNC Milling', 'Okuma', '850 x 500 x 500mm', '±0.015mm', 'active'),
('Surface Grinder SG-500', 'Grinding', 'Amada', '500 x 250mm', '±0.005mm', 'active'),
('CMM Inspection C-700', 'Inspection', 'Mitutoyo', '700 x 600 x 500mm', '±0.003mm', 'active');

INSERT INTO manufacturing_processes (name, description, sort_order) VALUES
('Tiện CNC', 'Gia công chi tiết tròn bằng máy tiện CNC.', 1),
('Phay CNC', 'Gia công mặt phẳng, rãnh, lỗ và biên dạng bằng máy phay CNC.', 2),
('Mài chính xác', 'Hoàn thiện bề mặt và kích thước có dung sai chặt.', 3),
('Kiểm tra CMM', 'Đo kiểm kích thước bằng máy đo tọa độ.', 4),
('Xử lý bề mặt', 'Nhiệt luyện, anodize, mạ hoặc xử lý theo yêu cầu.', 5);

INSERT INTO products (category_id, name, slug, short_description, description, main_image, is_featured) VALUES
(1, 'Trục truyền động chính xác', 'truc-truyen-dong-chinh-xac', 'Gia công trục, bạc và chi tiết tròn theo bản vẽ kỹ thuật.', 'Trục truyền động được gia công bằng tiện CNC, có thể kết hợp mài chính xác và kiểm tra kích thước trước khi giao hàng.', 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?auto=format&fit=crop&w=700&q=80', 1),
(2, 'Bánh răng & chi tiết truyền động', 'banh-rang-chi-tiet-truyen-dong', 'Hỗ trợ sản xuất chi tiết có yêu cầu độ bền và độ đồng tâm cao.', 'Nhóm chi tiết truyền động phù hợp cho hệ thống máy công nghiệp, có thể gia công theo vật liệu và tiêu chuẩn riêng.', 'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=700&q=80', 1),
(3, 'Cụm linh kiện lắp ráp', 'cum-linh-kien-lap-rap', 'Gia công, kiểm tra và đóng gói theo tiêu chuẩn khách hàng.', 'Cụm linh kiện được kiểm tra từng chi tiết trước khi lắp ráp, phù hợp cho khách hàng cần giao hàng theo bộ.', 'https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?auto=format&fit=crop&w=700&q=80', 1);

INSERT INTO product_materials (product_id, material_id) VALUES
(1, 1), (1, 4),
(2, 1), (2, 4),
(3, 2), (3, 3);

INSERT INTO product_processes (product_id, process_id, step_order, note) VALUES
(1, 1, 1, 'Tiện thô và tiện tinh'),
(1, 3, 2, 'Mài cổ trục nếu yêu cầu dung sai chặt'),
(1, 4, 3, 'Kiểm tra kích thước trước khi đóng gói'),
(2, 2, 1, 'Phay biên dạng và lỗ lắp'),
(2, 5, 2, 'Xử lý bề mặt theo yêu cầu'),
(3, 2, 1, 'Gia công từng chi tiết'),
(3, 4, 2, 'Kiểm tra trước khi lắp cụm');

INSERT INTO product_images (product_id, image_url, alt_text, sort_order) VALUES
(1, 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?auto=format&fit=crop&w=700&q=80', 'Trục truyền động chính xác', 1),
(2, 'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=700&q=80', 'Bánh răng và chi tiết truyền động', 1),
(3, 'https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?auto=format&fit=crop&w=700&q=80', 'Cụm linh kiện lắp ráp', 1);

INSERT INTO product_specs (product_id, spec_name, spec_value, unit, sort_order) VALUES
(1, 'Dung sai tham khảo', '±0.01', 'mm', 1),
(1, 'Đường kính tối đa', '250', 'mm', 2),
(2, 'Vật liệu đề xuất', 'S45C / SCM440', NULL, 1),
(2, 'Xử lý bề mặt', 'Nhiệt luyện / mạ theo yêu cầu', NULL, 2),
(3, 'Hình thức giao hàng', 'Theo bộ lắp ráp', NULL, 1);

INSERT INTO capabilities (title, content, icon_label, sort_order) VALUES
('Gia công CNC', 'Tiện, phay và khoan chính xác cho nhiều loại vật liệu.', 'CNC', 1),
('Kiểm tra chất lượng', 'Đo kiểm kích thước và lưu lại thông tin theo từng đơn hàng.', 'QC', 2),
('Tư vấn kỹ thuật', 'Hỗ trợ đọc bản vẽ, chọn vật liệu và tối ưu phương án gia công.', 'ENG', 3),
('Giao hàng ổn định', 'Quản lý tiến độ sản xuất và đóng gói để hạn chế lỗi phát sinh.', 'LOG', 4);

INSERT INTO capability_machines (capability_id, machine_id) VALUES
(1, 1), (1, 2), (2, 4), (3, 4), (4, 1);

INSERT INTO customers (company_name, contact_name, email, phone, country) VALUES
('Công ty Demo Precision', 'Nguyễn Văn A', 'buyer@example.com', '0900000000', 'Vietnam');

INSERT INTO quote_requests (customer_id, project_name, message, status) VALUES
(1, 'Báo giá trục truyền động H-Series', 'Cần báo giá 100 chi tiết theo bản vẽ đính kèm.', 'new');

INSERT INTO quote_request_items (quote_request_id, product_id, drawing_code, material_id, quantity, tolerance, note) VALUES
(1, 1, 'H-SERIES-001', 1, 100, '±0.01mm', 'Cần kiểm tra độ đồng tâm.');

INSERT INTO quote_files (quote_request_id, file_name, file_url, file_type) VALUES
(1, 'H-SERIES-001.pdf', '/uploads/demo/H-SERIES-001.pdf', 'pdf');

INSERT INTO news_categories (name, slug) VALUES
('Tin nhà máy', 'tin-nha-may'),
('Kỹ thuật', 'ky-thuat');

INSERT INTO news (category_id, title, slug, image, description, content) VALUES
(1, 'Nâng cấp quy trình kiểm tra chi tiết chính xác', 'nang-cap-quy-trinh-kiem-tra', 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?auto=format&fit=crop&w=700&q=80', 'Ứng dụng thêm bước kiểm tra trước khi đóng gói để tăng độ ổn định.', 'Nội dung bài viết có thể cập nhật sau khi website có hệ thống quản trị.'),
(1, 'Tối ưu gia công cho đơn hàng lặp lại', 'toi-uu-gia-cong-don-hang-lap-lai', 'https://images.unsplash.com/photo-1581092162384-8987c1d64718?auto=format&fit=crop&w=700&q=80', 'Chuẩn hóa đồ gá và quy trình giúp rút ngắn thời gian sản xuất.', 'Nội dung bài viết có thể cập nhật sau khi website có hệ thống quản trị.'),
(2, 'Dịch vụ tư vấn bản vẽ trước sản xuất', 'tu-van-ban-ve-truoc-san-xuat', 'https://images.unsplash.com/photo-1581092335397-9583eb92d232?auto=format&fit=crop&w=700&q=80', 'Đội kỹ thuật hỗ trợ kiểm tra dung sai, vật liệu và bề mặt hoàn thiện.', 'Nội dung bài viết có thể cập nhật sau khi website có hệ thống quản trị.');

INSERT INTO tags (name, slug) VALUES
('CNC', 'cnc'),
('Kiểm tra chất lượng', 'kiem-tra-chat-luong'),
('Bản vẽ kỹ thuật', 'ban-ve-ky-thuat');

INSERT INTO news_tags (news_id, tag_id) VALUES
(1, 2),
(2, 1),
(3, 3);
