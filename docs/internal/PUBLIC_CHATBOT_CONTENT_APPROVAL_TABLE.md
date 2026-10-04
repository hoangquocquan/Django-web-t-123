# Bảng duyệt nội dung chatbot công khai

Trạng thái: **CHƯA PHÊ DUYỆT — KHÔNG CÔNG BỐ**  
Nguồn đối chiếu: `mecprecision_public_chatbot_data_draft.json` và giao diện website local trên nhánh `codex/demo-database-validation`.

## 1. Nội dung dự kiến công khai

| ID / tiêu đề | Nguyên văn dự thảo | Cần chủ dự án xác nhận |
|---|---|---|
| **201 — Chuẩn bị thông tin để yêu cầu báo giá gia công** | Để yêu cầu báo giá gia công, hãy cung cấp bản vẽ hoặc mô hình chi tiết nếu có, phiên bản bản vẽ, số lượng, vật liệu mong muốn, các kích thước và dung sai quan trọng, yêu cầu hoàn thiện bề mặt, địa điểm giao hàng và thời điểm cần hàng. Nếu chưa rõ một mục, hãy ghi rõ để bộ phận phụ trách trao đổi thêm. Việc có thể nhận gia công, giá và thời gian thực hiện cần được xác nhận sau khi xem xét yêu cầu cụ thể. Không gửi thông tin mật qua cửa sổ chatbot công khai; hãy dùng kênh tiếp nhận yêu cầu do doanh nghiệp xác nhận. | Duyệt nguyên văn? Kênh nào được phép nhận bản vẽ/RFQ? Có cho phép nêu địa điểm và ngày cần hàng trong checklist không? |
| **202 — Câu hỏi thường gặp về báo giá** | Giá gia công phụ thuộc vào bản vẽ, vật liệu, số lượng, yêu cầu kỹ thuật và điều kiện của từng đơn hàng. Chatbot công khai không cung cấp báo giá chính thức, mức giá cố định, hạn hiệu lực báo giá hoặc thời gian giao hàng cam kết. Khách hàng cần gửi yêu cầu cụ thể để nhân viên phụ trách kiểm tra và phản hồi qua kênh chính thức. Nếu đã có báo giá, hãy đối chiếu điều kiện trực tiếp trên báo giá được doanh nghiệp gửi cho bạn. | Duyệt nguyên văn? Quy trình tiếp nhận/phản hồi báo giá thực tế là gì? Kênh nào được coi là chính thức? |
| **203 — Bản vẽ, phiên bản và thông tin kỹ thuật** | Khi trao đổi về một chi tiết, hãy nêu mã chi tiết và phiên bản bản vẽ đang áp dụng. Làm rõ vật liệu, số lượng, các kích thước và dung sai cần kiểm soát, yêu cầu xử lý bề mặt và tiêu chí nghiệm thu nếu có. Khi thay đổi bản vẽ hoặc thông số, cần thông báo rõ nội dung thay đổi và phiên bản mới để bộ phận phụ trách xem xét lại báo giá hoặc kế hoạch sản xuất. Chatbot công khai không thể phê duyệt bản vẽ hoặc xác nhận khả năng đạt một dung sai cụ thể. | Duyệt nguyên văn? Checklist mã chi tiết/phiên bản/tiêu chí nghiệm thu có đúng quy trình thực tế không? |
| **204 — Câu hỏi thường gặp về kiểm tra chất lượng** | Nếu cần báo cáo đo kiểm, kiểm tra mẫu đầu tiên hoặc hồ sơ chất lượng, hãy nêu rõ yêu cầu ngay khi gửi yêu cầu báo giá và cung cấp tiêu chí nghiệm thu. Phương pháp kiểm tra và loại hồ sơ cung cấp cần được hai bên xác nhận cho từng đơn hàng. Chatbot công khai không xác nhận chứng chỉ doanh nghiệp, tiêu chuẩn đang áp dụng, thiết bị đo, năng lực máy hoặc dung sai có thể đạt nếu chưa có tài liệu công khai đã được doanh nghiệp phê duyệt. | Duyệt nguyên văn? Có cho phép nêu “kiểm tra mẫu đầu tiên” và “hồ sơ chất lượng” không? Chưa bổ sung chứng chỉ/thiết bị/năng lực khi chưa có hồ sơ duyệt. |
| **205 — Phạm vi hỗ trợ của chatbot công khai** | Chatbot hỗ trợ giải thích cách chuẩn bị yêu cầu gia công và hướng dẫn câu hỏi cần làm rõ trước khi xin báo giá. Câu trả lời mang tính tham khảo; báo giá, năng lực gia công, lịch giao hàng và điều khoản thương mại phải do người phụ trách xác nhận qua kênh chính thức. Chatbot không tra cứu hoặc công bố dữ liệu khách hàng, đơn hàng, báo giá riêng, tồn kho, tài liệu nội bộ hay thông tin cá nhân. Nếu câu hỏi vượt quá tài liệu công khai đã được phê duyệt, chatbot cần nói chưa có đủ thông tin và hướng khách hàng liên hệ bộ phận phụ trách. | Duyệt nguyên văn? Tên bộ phận, kênh và URL nào được phép nêu? |

## 2. Kênh nhận bản vẽ/RFQ đang hiển thị trên website

> Các mục dưới đây chỉ là hiện trạng mã nguồn/giao diện. **Không mục nào được coi là đã phê duyệt.**

| Kênh/hiển thị hiện có | Hiện trạng kỹ thuật | Cần xác nhận |
|---|---|---|
| Trang `#/contact` với form họ tên, email công ty, tên công ty, vùng “kéo thả STEP/PDF/DWG”, mô tả và nút “Gửi yêu cầu” | Chỉ là UI demo: submit chỉ đổi state React sang màn hình “Đã nhận yêu cầu”; không có file input, upload, API call hay bản ghi RFQ thật. | Có chọn form website là kênh chính thức không? Nếu có: nơi lưu file, loại/dung lượng file, quét an toàn, retention, thông báo quyền riêng tư và người/bộ phận nhận. |
| Email hiển thị: `baogia@mecprecision.vn` | Text tĩnh, không phải liên kết `mailto:`; chưa xác minh hộp thư tồn tại hay được phép nhận bản vẽ. | Email này có chính xác và được phép công bố/nhận file không? |
| Điện thoại hiển thị: `+84 24 3827 xxxx` | Placeholder chưa hoàn chỉnh; không thể dùng làm kênh thật. | Số chính thức (nếu muốn công bố) và phạm vi hỗ trợ RFQ. |
| Địa chỉ hiển thị: `KCN Thăng Long, Đông Anh, Hà Nội` | Text tĩnh ở trang liên hệ/footer; bản đồ chỉ là placeholder. | Địa chỉ có chính xác và được phép công bố không? Có phải nơi nhận RFQ không? |
| Các CTA “Yêu cầu báo giá”, “Tải bản vẽ · Nhận báo giá”, “Gửi bản vẽ nhận báo giá” | Chỉ điều hướng nội bộ tới `#/contact`; không tạo RFQ hay upload. | Giữ, đổi câu chữ hay ẩn cho đến khi kênh thật sẵn sàng? |

## 3. Cam kết/khẳng định hiện có cần duyệt riêng

- `Đội kỹ thuật phản hồi báo giá và nhận xét DFM trong một ngày làm việc.`
- `Kỹ sư sẽ liên hệ trong 24 giờ.`
- Quy trình trên website hiển thị `Tiếp nhận RFQ — Trong 2 giờ` và `DFM & báo giá — Trong 24 giờ`.

Các câu trên chưa được dùng làm nguồn chatbot. Cần chủ dự án chọn: **duyệt**, **sửa thành mô tả không cam kết**, hoặc **gỡ bỏ**.

## 4. Quyết định cần trả lời

1. Duyệt/từ chối/yêu cầu sửa cho từng ID `201`–`205`.
2. Chọn kênh nhận bản vẽ/RFQ: form website, email, kênh khác, hoặc chưa công bố.
3. Xác nhận email, số điện thoại và địa chỉ nào được phép công bố.
4. Quyết định về các mốc `2 giờ`, `24 giờ`, `một ngày làm việc`.
5. Xác nhận có cho phép nêu báo cáo đo kiểm/kiểm tra mẫu đầu tiên/hồ sơ chất lượng hay không.

Cho đến khi có câu trả lời rõ ràng, database chính phải giữ `0 public` và chatbot không được công bố/triển khai cho khách hàng.
