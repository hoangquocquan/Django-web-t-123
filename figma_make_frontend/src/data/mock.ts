export const PRODUCTS = [
  {
    id: "p001",
    name: "Vỏ Động Cơ CNC 5 Trục",
    category: "Kết Cấu Máy",
    material: "Nhôm 6061-T6",
    tolerance: "±0.005mm",
    finish: "Anodize Cứng Loại III",
    lead_time: "5–7 ngày",
    price_range: "1.200.000 – 4.500.000 ₫",
    processes: ["Phay CNC 5 trục", "Tiện CNC", "Anodize"],
    certifications: ["ISO 9001:2015", "AS9100D"],
    image: "photo-1565688534245-5571d5e0a9fc",
    description: "Vỏ động cơ độ chính xác cao dành cho thiết bị công nghiệp và hàng không. Gia công từ nhôm hàng không 6061-T6 với dung sai cực chặt.",
    specs: { "Độ nhám Ra": "0.8 µm", "Độ cứng Anodize": "60 HRC", "Kích thước max": "500×400×300 mm" },
    gallery: ["photo-1565688534245-5571d5e0a9fc", "photo-1581091226825-a6a2a5aee158", "photo-1504328345606-18bbc8c9d7d1"],
    related: ["p002", "p003"],
    status: "Còn hàng",
    stock: 42,
  },
  {
    id: "p002",
    name: "Đĩa Bánh Răng Chính Xác",
    category: "Truyền Động",
    material: "Thép 4140",
    tolerance: "±0.003mm",
    finish: "Tôi cứng & Ram",
    lead_time: "7–10 ngày",
    price_range: "800.000 – 2.200.000 ₫",
    processes: ["Tiện CNC", "Mài vô tâm", "Nhiệt luyện"],
    certifications: ["ISO 9001:2015"],
    image: "photo-1504328345606-18bbc8c9d7d1",
    description: "Bánh răng chính xác cho hệ thống truyền động tốc độ cao, yêu cầu độ ồn thấp và tuổi thọ dài.",
    specs: { "Mô-đun": "0.5 – 8", "Số răng": "12 – 200", "Độ cứng": "58–62 HRC" },
    gallery: ["photo-1504328345606-18bbc8c9d7d1", "photo-1565688534245-5571d5e0a9fc"],
    related: ["p001", "p004"],
    status: "Còn hàng",
    stock: 18,
  },
  {
    id: "p003",
    name: "Thân Xy-lanh Thủy Lực",
    category: "Thủy Lực",
    material: "Thép không gỉ 316L",
    tolerance: "±0.008mm",
    finish: "Đánh bóng điện hóa",
    lead_time: "10–14 ngày",
    price_range: "2.500.000 – 8.000.000 ₫",
    processes: ["Tiện CNC", "Khoan sâu", "Đánh bóng"],
    certifications: ["ISO 9001:2015", "PED 2014/68/EU"],
    image: "photo-1581091226825-a6a2a5aee158",
    description: "Xy-lanh thủy lực áp suất cao cho hệ thống công nghiệp và thiết bị nâng hạ.",
    specs: { "Áp suất tối đa": "350 bar", "Độ bền bề mặt": "Ra 0.2 µm", "Chiều dài max": "2.000 mm" },
    gallery: ["photo-1581091226825-a6a2a5aee158"],
    related: ["p001", "p005"],
    status: "Sản xuất theo đơn",
    stock: 0,
  },
  {
    id: "p004",
    name: "Bộ Định Vị Khuôn Mẫu",
    category: "Khuôn Mẫu",
    material: "Thép P20",
    tolerance: "±0.002mm",
    finish: "Đánh bóng gương",
    lead_time: "14–21 ngày",
    price_range: "5.000.000 – 25.000.000 ₫",
    processes: ["Phay EDM", "Phay CNC", "Đánh bóng tay"],
    certifications: ["ISO 9001:2015"],
    image: "photo-1518611012118-696072aa579a",
    description: "Bộ khuôn định vị chính xác cao cho ngành nhựa và đúc áp lực.",
    specs: { "Độ nhám": "Ra 0.05 µm", "Tuổi thọ khuôn": "500.000+ chu kỳ", "Kích thước": "Theo yêu cầu" },
    gallery: ["photo-1518611012118-696072aa579a"],
    related: ["p002", "p003"],
    status: "Sản xuất theo đơn",
    stock: 0,
  },
  {
    id: "p005",
    name: "Khớp Nối Trục Chính Xác",
    category: "Truyền Động",
    material: "Nhôm 7075-T651",
    tolerance: "±0.005mm",
    finish: "Anodize Loại II",
    lead_time: "3–5 ngày",
    price_range: "350.000 – 1.200.000 ₫",
    processes: ["Phay CNC 4 trục", "Tiện CNC"],
    certifications: ["ISO 9001:2015"],
    image: "photo-1565688534245-5571d5e0a9fc",
    description: "Khớp nối trục linh hoạt, hấp thụ lệch tâm và góc lệch trong hệ thống máy móc chính xác.",
    specs: { "Mô-men xoắn max": "120 N·m", "Tốc độ max": "10.000 RPM", "Đường kính": "6 – 100 mm" },
    gallery: ["photo-1565688534245-5571d5e0a9fc"],
    related: ["p002", "p004"],
    status: "Còn hàng",
    stock: 76,
  },
  {
    id: "p006",
    name: "Tấm Bảng Điều Khiển CNC",
    category: "Kết Cấu Máy",
    material: "Nhôm 5052-H32",
    tolerance: "±0.1mm",
    finish: "Sơn tĩnh điện",
    lead_time: "3–5 ngày",
    price_range: "200.000 – 800.000 ₫",
    processes: ["Cắt laser", "Uốn CNC", "Sơn tĩnh điện"],
    certifications: ["ISO 9001:2015"],
    image: "photo-1504328345606-18bbc8c9d7d1",
    description: "Tấm bảng điều khiển máy móc công nghiệp, độ bền cao, chống ăn mòn.",
    specs: { "Độ dày": "1.5 – 6 mm", "Màu sắc": "RAL theo yêu cầu", "Kích thước max": "2.000×1.000 mm" },
    gallery: ["photo-1504328345606-18bbc8c9d7d1"],
    related: ["p001", "p005"],
    status: "Còn hàng",
    stock: 120,
  },
];

export const NEWS = [
  {
    id: "n001",
    slug: "mec-dat-chung-chi-as9100d",
    title: "MecPrecision Đạt Chứng Chỉ AS9100D – Bước Tiến Vào Ngành Hàng Không Vũ Trụ",
    excerpt: "Sau 18 tháng chuẩn bị nghiêm ngặt, MecPrecision Việt Nam chính thức nhận chứng nhận AS9100D từ Bureau Veritas, mở ra cơ hội hợp tác với các tập đoàn hàng không quốc tế.",
    date: "2026-07-15",
    category: "Tin Tức Công Ty",
    author: "Nguyễn Văn Thành",
    image: "photo-1540575467063-178a50c2df87",
    read_time: 5,
    content: `MecPrecision Việt Nam vừa chính thức nhận chứng nhận quản lý chất lượng AS9100D từ Bureau Veritas International – một trong những tổ chức chứng nhận uy tín nhất thế giới trong lĩnh vực hàng không vũ trụ.

Đây là kết quả của 18 tháng đầu tư và hoàn thiện hệ thống quản lý chất lượng toàn diện, từ kiểm soát tài liệu, quy trình sản xuất, đến kiểm tra và theo dõi sản phẩm theo tiêu chuẩn quốc tế.

**Ý nghĩa của chứng chỉ AS9100D**

AS9100D là phiên bản mới nhất của tiêu chuẩn quản lý chất lượng dành riêng cho ngành hàng không vũ trụ, được xây dựng dựa trên nền tảng ISO 9001:2015 với các yêu cầu bổ sung khắt khe hơn về quản lý rủi ro, kiểm soát cấu hình và truy xuất nguồn gốc.

Với chứng nhận này, MecPrecision đủ điều kiện cung ứng linh kiện cho các nhà sản xuất OEM hàng không như Airbus, Boeing và các chuỗi cung ứng cấp 1, cấp 2 tại châu Á – Thái Bình Dương.

**Năng lực sản xuất**

Hiện tại, nhà máy của MecPrecision tại Khu Công Nghệ Cao TP.HCM sở hữu 12 trung tâm phay CNC 5 trục, 8 máy tiện đa nhiệm, cùng phòng CMM kiểm tra tọa độ 3 chiều được kiểm chuẩn hàng quý.`,
  },
  {
    id: "n002",
    slug: "khai-truong-xuong-cnc-moi",
    title: "Khai Trương Xưởng CNC Mở Rộng – Tăng Gấp Đôi Công Suất Năm 2026",
    excerpt: "Xưởng sản xuất mở rộng 2.400 m² chính thức đi vào hoạt động với 8 máy CNC DMG MORI thế hệ mới, nâng tổng công suất lên 180.000 chi tiết/năm.",
    date: "2026-06-01",
    category: "Sản Xuất",
    author: "Trần Minh Khoa",
    image: "photo-1581091226825-a6a2a5aee158",
    read_time: 4,
    content: `Ngày 1 tháng 6 năm 2026, MecPrecision khai trương xưởng sản xuất mở rộng tại Khu Công Nghệ Cao TP.HCM, đánh dấu giai đoạn tăng trưởng quan trọng trong chiến lược phát triển dài hạn.

Xưởng mới có diện tích 2.400 m², được trang bị 8 trung tâm gia công DMG MORI NMV 5000 DCG – dòng máy 5 trục đứng hàng đầu thế giới với độ chính xác lặp lại ±0.002mm.

Tổng công suất nhà máy sau mở rộng đạt 180.000 chi tiết/năm, tăng 120% so với năm 2024.`,
  },
  {
    id: "n003",
    slug: "hop-tac-samsung-electro-mechanics",
    title: "Ký Kết Hợp Tác Chiến Lược Với Samsung Electro-Mechanics Việt Nam",
    excerpt: "MecPrecision trở thành nhà cung ứng linh kiện chính xác được phê duyệt (AVL) của Samsung Electro-Mechanics, cung cấp chi tiết kết cấu cho dây chuyền sản xuất PCB tự động.",
    date: "2026-05-12",
    category: "Đối Tác",
    author: "Lê Thị Hương",
    image: "photo-1518611012118-696072aa579a",
    read_time: 3,
    content: `MecPrecision Việt Nam và Samsung Electro-Mechanics Việt Nam (SEMV) vừa ký kết thỏa thuận hợp tác cung ứng dài hạn, đưa MecPrecision vào danh sách nhà cung ứng được phê duyệt (AVL) chính thức.

Theo thỏa thuận, MecPrecision sẽ cung cấp các chi tiết kết cấu chính xác dùng trong dây chuyền lắp ráp PCB tự động của SEMV tại Khu Công Nghiệp Thái Nguyên.`,
  },
];

export const CUSTOMERS = [
  { id: "c001", name: "Samsung Electro-Mechanics VN", industry: "Điện tử", tier: "Chiến lược", revenue: "4.200.000.000 ₫", orders: 47, status: "active", contact: "Kim Ji-hoon", phone: "+82 31 279 5000", email: "jihoon.kim@sem.samsung.com" },
  { id: "c002", name: "Thaco Auto", industry: "Ô tô", tier: "Vàng", revenue: "2.800.000.000 ₫", orders: 31, status: "active", contact: "Nguyễn Quốc Hùng", phone: "0236 363 6666", email: "hung.nq@thaco.com.vn" },
  { id: "c003", name: "Vietjet Air MRO", industry: "Hàng không", tier: "Bạc", revenue: "1.100.000.000 ₫", orders: 12, status: "active", contact: "Phạm Thanh Liêm", phone: "028 3547 8888", email: "liem.pt@vietjet.com" },
  { id: "c004", name: "Doosan Vina", industry: "Năng lượng", tier: "Vàng", revenue: "3.400.000.000 ₫", orders: 28, status: "active", contact: "Lee Sang-ho", phone: "0510 3893 990", email: "sangho.lee@doosan.com" },
  { id: "c005", name: "ABB Việt Nam", industry: "Điện công nghiệp", tier: "Bạc", revenue: "890.000.000 ₫", orders: 9, status: "inactive", contact: "Trần Anh Tuấn", phone: "024 3824 7070", email: "tuan.ta@vn.abb.com" },
];

export const ORDERS = [
  { id: "DH2026-0847", customer: "Samsung Electro-Mechanics VN", product: "Vỏ Động Cơ CNC 5 Trục", qty: 200, value: "840.000.000 ₫", status: "Đang sản xuất", progress: 65, due: "2026-09-15", priority: "Cao" },
  { id: "DH2026-0831", customer: "Thaco Auto", product: "Đĩa Bánh Răng Chính Xác", qty: 500, value: "1.100.000.000 ₫", status: "Kiểm tra QC", progress: 90, due: "2026-09-05", priority: "Cao" },
  { id: "DH2026-0819", customer: "Doosan Vina", product: "Thân Xy-lanh Thủy Lực", qty: 50, value: "375.000.000 ₫", status: "Hoàn thành", progress: 100, due: "2026-08-20", priority: "Bình thường" },
  { id: "DH2026-0808", customer: "Vietjet Air MRO", product: "Bộ Định Vị Khuôn Mẫu", qty: 10, value: "250.000.000 ₫", status: "Chờ vật tư", progress: 15, due: "2026-09-30", priority: "Thấp" },
  { id: "DH2026-0795", customer: "ABB Việt Nam", product: "Khớp Nối Trục Chính Xác", qty: 100, value: "120.000.000 ₫", status: "Đã giao", progress: 100, due: "2026-08-10", priority: "Bình thường" },
];

export const INVENTORY = [
  { id: "VT001", name: "Nhôm 6061-T6 Thanh Tròn Ø50", unit: "kg", stock: 2450, min: 500, cost: "65.000 ₫/kg", supplier: "BKSC Metals", location: "Kho A-03" },
  { id: "VT002", name: "Thép 4140 Thanh Tròn Ø80", unit: "kg", stock: 1820, min: 300, cost: "48.000 ₫/kg", supplier: "Thép Miền Nam", location: "Kho A-05" },
  { id: "VT003", name: "Thép SS316L Thanh Tròn Ø60", unit: "kg", stock: 340, min: 400, cost: "210.000 ₫/kg", supplier: "BKSC Metals", location: "Kho B-01" },
  { id: "VT004", name: "Dao Phay Ø16 HRC65 4 Lưỡi", unit: "cái", stock: 28, min: 30, cost: "1.250.000 ₫/cái", supplier: "Sandvik VN", location: "Kho Dụng Cụ" },
  { id: "VT005", name: "Dầu Tản Nhiệt CNC 100L", unit: "thùng", stock: 12, min: 5, cost: "2.800.000 ₫/thùng", supplier: "Castrol VN", location: "Kho Hóa Chất" },
];

export const LEADS = [
  { id: "L001", company: "Vinfast", contact: "Đỗ Văn Nam", title: "Kỹ sư Mua hàng", value: "2.500.000.000 ₫", stage: "Tiếp Cận", assigned: "Nguyễn Thị Mai", probability: 20, source: "LinkedIn", created: "2026-08-10", next_action: "Gọi điện giới thiệu năng lực" },
  { id: "L002", company: "Fujikura VN", contact: "Yamamoto Kenji", title: "Procurement Manager", value: "800.000.000 ₫", stage: "Báo Giá", assigned: "Lê Quốc Huy", probability: 60, source: "Triển lãm METALEX", created: "2026-07-22", next_action: "Follow-up báo giá RFQ-2406" },
  { id: "L003", company: "PTSC M&C", contact: "Hoàng Minh Đức", title: "Trưởng Phòng Kỹ Thuật", value: "1.200.000.000 ₫", stage: "Thương Lượng", assigned: "Nguyễn Thị Mai", probability: 75, source: "Giới thiệu", created: "2026-07-05", next_action: "Đàm phán điều khoản hợp đồng" },
  { id: "L004", company: "GE Gas Power VN", contact: "Sarah Chen", title: "Supply Chain Director", value: "5.000.000.000 ₫", stage: "Chốt Hợp Đồng", assigned: "Trần Văn Đức", probability: 85, source: "Website", created: "2026-06-18", next_action: "Ký hợp đồng khung Q3/2026" },
  { id: "L005", company: "Nidec VN", contact: "Tanaka Hiroshi", title: "VP Engineering", value: "650.000.000 ₫", stage: "Tìm Hiểu", assigned: "Lê Quốc Huy", probability: 40, source: "Cold email", created: "2026-08-20", next_action: "Gửi brochure năng lực" },
  { id: "L006", company: "Yazaki VN", contact: "Phạm Hữu Lộc", title: "Purchasing Lead", value: "420.000.000 ₫", stage: "Tiếp Cận", assigned: "Trần Văn Đức", probability: 30, source: "Referral", created: "2026-08-25", next_action: "Lên lịch tham quan nhà máy" },
];

export const QUOTATIONS = [
  { id: "BG2026-142", customer: "Fujikura VN", products: "Đĩa Bánh Răng + Khớp Nối (3 SKU)", total: "420.000.000 ₫", status: "Chờ Duyệt", created: "2026-08-28", valid_until: "2026-09-28", created_by: "Lê Quốc Huy" },
  { id: "BG2026-139", customer: "PTSC M&C", products: "Thân Xy-lanh Thủy Lực (Ø200×800mm)", total: "1.200.000.000 ₫", status: "Đã Duyệt", created: "2026-08-20", valid_until: "2026-09-20", created_by: "Nguyễn Thị Mai" },
  { id: "BG2026-131", customer: "Vinfast", products: "Vỏ Hộp Số (Prototype × 5)", total: "350.000.000 ₫", status: "Đã Gửi", created: "2026-08-12", valid_until: "2026-09-12", created_by: "Nguyễn Thị Mai" },
  { id: "BG2026-118", customer: "GE Gas Power VN", products: "Bộ Chi Tiết Turbin (15 SKU)", total: "4.800.000.000 ₫", status: "Đã Chốt", created: "2026-07-30", valid_until: "2026-08-30", created_by: "Trần Văn Đức" },
  { id: "BG2026-105", customer: "Doosan Vina", products: "Khớp Nối Ống (×200)", total: "280.000.000 ₫", status: "Từ Chối", created: "2026-07-15", valid_until: "2026-08-15", created_by: "Lê Quốc Huy" },
];

export const METRICS = {
  revenue_ytd: "28.400.000.000 ₫",
  orders_ytd: 284,
  active_customers: 47,
  on_time_delivery: "96.2%",
  defect_rate: "0.08%",
  capacity_util: "78%",
  avg_lead_time: "6.4 ngày",
  nps: 72,
};
